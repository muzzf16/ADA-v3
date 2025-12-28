"""
n8n MCP Agent - Client for n8n MCP Server
Allows A.D.A to connect to n8n and execute workflows via MCP protocol.
Uses n8n's built-in MCP tools: search_workflows, execute_workflow, get_workflow_details.
"""

import os
import json
import asyncio
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

try:
    import aiohttp
except ImportError:
    aiohttp = None

load_dotenv()


class N8nMCPAgent:
    """
    Client for n8n's built-in MCP Server.
    
    n8n MCP provides 3 built-in tools:
    - search_workflows: Search for workflows by name/description
    - execute_workflow: Execute a workflow with input data
    - get_workflow_details: Get detailed information about a workflow
    """
    
    def __init__(self, base_url: str = None, token: str = None):
        """
        Initialize the n8n MCP Agent.
        
        Args:
            base_url: n8n MCP Server URL (e.g., https://n8n.example.com/mcp-server/http)
            token: MCP Access Token from n8n Settings
        """
        self.base_url = base_url or os.getenv("N8N_MCP_URL", "")
        self.token = token or os.getenv("N8N_MCP_TOKEN", "")
        
        # Ensure base_url ends with /mcp-server/http
        if self.base_url and not self.base_url.endswith("/mcp-server/http"):
            if self.base_url.endswith("/"):
                self.base_url = self.base_url + "mcp-server/http"
            else:
                self.base_url = self.base_url + "/mcp-server/http"
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._mcp_session_id: Optional[str] = None
        self._request_id = 0
        
    @property
    def is_configured(self) -> bool:
        """Check if the agent has valid configuration."""
        return bool(self.base_url and self.token)
    
    @property
    def is_connected(self) -> bool:
        """Check if the agent is connected."""
        return self._connected
    
    def _next_request_id(self) -> int:
        """Generate next JSON-RPC request ID."""
        self._request_id += 1
        return self._request_id
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if aiohttp is None:
            raise ImportError("aiohttp is required. Install with: pip install aiohttp")
            
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers for MCP Streamable HTTP."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self._mcp_session_id:
            headers["Mcp-Session-Id"] = self._mcp_session_id
        return headers
    
    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
        self._connected = False
        self._mcp_session_id = None
    
    async def _parse_sse_response(self, response) -> Dict[str, Any]:
        """Parse Server-Sent Events response."""
        try:
            result = None
            async for line in response.content:
                decoded = line.decode('utf-8').strip()
                if decoded.startswith('data:'):
                    data_str = decoded[5:].strip()
                    if data_str:
                        try:
                            data = json.loads(data_str)
                            if "result" in data:
                                result = data["result"]
                            elif "error" in data:
                                return {"success": False, "error": data["error"].get("message", str(data["error"]))}
                        except json.JSONDecodeError:
                            continue
            
            if result is not None:
                return {"success": True, "result": result}
            return {"success": False, "error": "No valid data in SSE stream"}
            
        except Exception as e:
            return {"success": False, "error": f"SSE parse error: {str(e)}"}
    
    async def _call_mcp(self, method: str, params: dict = None) -> Dict[str, Any]:
        """Send a JSON-RPC request to MCP server."""
        if not self.is_configured:
            return {"success": False, "error": "n8n MCP not configured"}
        
        try:
            session = await self._get_session()
            
            payload = {
                "jsonrpc": "2.0",
                "id": self._next_request_id(),
                "method": method,
            }
            if params:
                payload["params"] = params
            
            headers = self._get_headers()
            timeout = aiohttp.ClientTimeout(total=300)
            
            async with session.post(self.base_url, json=payload, headers=headers, timeout=timeout) as response:
                if "Mcp-Session-Id" in response.headers:
                    self._mcp_session_id = response.headers["Mcp-Session-Id"]
                
                content_type = response.headers.get("Content-Type", "")
                
                if response.status == 200:
                    if "text/event-stream" in content_type:
                        return await self._parse_sse_response(response)
                    else:
                        data = await response.json()
                        if "result" in data:
                            return {"success": True, "result": data["result"]}
                        elif "error" in data:
                            return {"success": False, "error": data["error"].get("message", str(data["error"]))}
                        return {"success": True, "result": data}
                else:
                    text = await response.text()
                    return {"success": False, "error": f"HTTP {response.status}: {text[:200]}"}
                    
        except Exception as e:
            return {"success": False, "error": f"Request error: {str(e)}"}
    
    async def _call_tool(self, tool_name: str, arguments: dict = None) -> Dict[str, Any]:
        """Call an MCP tool."""
        result = await self._call_mcp("tools/call", {
            "name": tool_name,
            "arguments": arguments or {}
        })
        
        if result.get("success"):
            # Extract text content from MCP tool response
            content = result.get("result", {}).get("content", [])
            text_result = ""
            for item in content:
                if item.get("type") == "text":
                    text_result += item.get("text", "")
            
            if text_result:
                # Try to parse as JSON
                try:
                    parsed = json.loads(text_result)
                    return {"success": True, "result": parsed}
                except:
                    return {"success": True, "result": text_result}
            
            return {"success": True, "result": result.get("result")}
        
        return result
    
    async def connect(self) -> Dict[str, Any]:
        """Initialize connection to n8n MCP Server."""
        if not self.is_configured:
            return {
                "success": False,
                "error": "n8n MCP not configured. Set N8N_MCP_URL and N8N_MCP_TOKEN environment variables."
            }
        
        result = await self._call_mcp("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "A.D.A",
                "version": "2.0"
            }
        })
        
        if result.get("success"):
            self._connected = True
            server_info = result.get("result", {}).get("serverInfo", {})
            return {
                "success": True,
                "message": f"Connected to n8n MCP Server",
                "server_name": server_info.get("name", "n8n"),
                "server_version": server_info.get("version", "unknown")
            }
        return result
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available MCP tools from n8n."""
        result = await self._call_mcp("tools/list")
        
        if result.get("success"):
            tools = result.get("result", {}).get("tools", [])
            return {
                "success": True,
                "tools": [{"name": t.get("name"), "description": t.get("description")} for t in tools],
                "count": len(tools)
            }
        return result
    
    async def list_workflows(self) -> Dict[str, Any]:
        """
        List all available workflows in n8n using search_workflows tool.
        Uses empty query to get all workflows.
        """
        result = await self._call_tool("search_workflows", {"query": ""})
        
        if result.get("success"):
            workflows = result.get("result", [])
            if isinstance(workflows, list):
                return {
                    "success": True,
                    "workflows": workflows,
                    "count": len(workflows)
                }
            return {"success": True, "workflows": [workflows] if workflows else [], "count": 1 if workflows else 0}
        return result
    
    async def search_workflows(self, query: str) -> Dict[str, Any]:
        """Search for workflows by name or description using n8n's search_workflows tool."""
        result = await self._call_tool("search_workflows", {"query": query})
        
        if result.get("success"):
            workflows = result.get("result", [])
            if isinstance(workflows, list):
                return {
                    "success": True,
                    "query": query,
                    "workflows": workflows,
                    "count": len(workflows)
                }
            return {"success": True, "query": query, "workflows": [workflows] if workflows else [], "count": 1 if workflows else 0}
        return result
    
    async def get_workflow_info(self, workflow_id: str) -> Dict[str, Any]:
        """Get detailed information about a workflow using n8n's get_workflow_details tool.
        
        Args:
            workflow_id: The workflow ID (from search_workflows result)
        """
        result = await self._call_tool("get_workflow_details", {"workflowId": workflow_id})
        
        if result.get("success"):
            return {
                "success": True,
                "workflow": result.get("result", {})
            }
        return result
    
    async def execute_workflow(self, workflow_id: str, input_data: dict = None) -> Dict[str, Any]:
        """Execute a workflow using n8n's execute_workflow tool.
        
        Args:
            workflow_id: The workflow ID (from search_workflows result)
            input_data: Optional input data for the workflow
        """
        args = {"workflowId": workflow_id}
        if input_data:
            args["inputData"] = input_data
        
        result = await self._call_tool("execute_workflow", args)
        
        if result.get("success"):
            return {
                "success": True,
                "workflow_id": workflow_id,
                "result": result.get("result", "Workflow executed successfully")
            }
        return result


# Singleton instance
_agent_instance: Optional[N8nMCPAgent] = None


def get_n8n_agent() -> N8nMCPAgent:
    """Get or create the singleton N8nMCPAgent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = N8nMCPAgent()
    return _agent_instance


# Test function
async def test_connection():
    """Test the n8n MCP connection."""
    agent = get_n8n_agent()
    
    print(f"Configured: {agent.is_configured}")
    print(f"Base URL: {agent.base_url}")
    
    if agent.is_configured:
        print("\n1. Connecting...")
        result = await agent.connect()
        print(f"   {result}")
        
        if result.get("success"):
            print("\n2. Listing MCP tools...")
            tools = await agent.list_tools()
            print(f"   {tools}")
            
            print("\n3. Searching workflows (empty query)...")
            workflows = await agent.list_workflows()
            print(f"   {workflows}")
            
            print("\n4. Searching for 'Virtual'...")
            search = await agent.search_workflows("Virtual")
            print(f"   {search}")
    else:
        print("Not configured. Set N8N_MCP_URL and N8N_MCP_TOKEN in .env file")
    
    await agent.close()


if __name__ == "__main__":
    asyncio.run(test_connection())
