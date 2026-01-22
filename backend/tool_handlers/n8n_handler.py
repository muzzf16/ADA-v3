from typing import Dict, Any
from n8n_mcp_agent import N8nMCPAgent

class N8nHandler:
    def __init__(self, agent: N8nMCPAgent):
        self.agent = agent

    async def handle_n8n_connect(self):
        """Handle connecting to n8n MCP Server."""
        print(f"[ADA DEBUG] [N8N] Connecting to n8n MCP Server...")
        result = await self.agent.connect()

        if result.get("success"):
            message = f"Connected to n8n MCP Server! Server: {result.get('server_name', 'n8n')}"
        else:
            message = f"Failed to connect to n8n: {result.get('error', 'Unknown error')}"

        print(f"[ADA DEBUG] [N8N] Connect result: {message}")
        return {"result": message}

    async def handle_n8n_list_workflows(self):
        """Handle listing available n8n workflows."""
        print(f"[ADA DEBUG] [N8N] Listing workflows...")
        result = await self.agent.list_workflows()

        if result.get("success"):
            workflows = result.get("workflows", [])
            # Extract actual workflow data from nested structure
            workflow_names = []  # List of (name, id) tuples
            for w in workflows:
                if isinstance(w, dict):
                    # Handle nested data structure: {data: [{id, name, ...}]}
                    if "data" in w:
                        for item in w.get("data", []):
                            if isinstance(item, dict) and "name" in item:
                                workflow_names.append((item.get("name", "Unknown"), item.get("id", "N/A")))
                    elif "name" in w:
                        workflow_names.append((w.get("name", "Unknown"), w.get("id", "N/A")))

            if workflow_names:
                workflow_list = "\n".join([f"- {name} (ID: {wid})" for name, wid in workflow_names[:10]])
                message = f"Found {len(workflow_names)} workflows:\n{workflow_list}"
                if len(workflow_names) > 10:
                    message += f"\n...and {len(workflow_names) - 10} more"
            else:
                message = "No workflows found. Make sure workflows are exposed to MCP in n8n settings."
        else:
            message = f"Failed to list workflows: {result.get('error', 'Unknown error')}"

        return {"result": message, "workflows": result.get("workflows", [])}

    async def handle_n8n_search_workflows(self, query):
        """Handle searching n8n workflows."""
        print(f"[ADA DEBUG] [N8N] Searching workflows: {query}")
        result = await self.agent.search_workflows(query)

        if result.get("success"):
            workflows = result.get("workflows", [])
            # Extract actual workflow data from nested structure
            workflow_names = []  # List of (name, id) tuples
            for w in workflows:
                if isinstance(w, dict):
                    # Handle nested data structure: {data: [{id, name, ...}]}
                    if "data" in w:
                        for item in w.get("data", []):
                            if isinstance(item, dict) and "name" in item:
                                workflow_names.append((item.get("name", "Unknown"), item.get("id", "N/A")))
                    elif "name" in w:
                        workflow_names.append((w.get("name", "Unknown"), w.get("id", "N/A")))

            if workflow_names:
                workflow_list = "\n".join([f"- {name} (ID: {wid})" for name, wid in workflow_names])
                message = f"Found {len(workflow_names)} matching workflows:\n{workflow_list}\n\nTo execute, use the workflow ID."
            else:
                message = f"No workflows found matching '{query}'."
        else:
            message = f"Search failed: {result.get('error', 'Unknown error')}"

        return {"result": message, "workflows": result.get("workflows", [])}

    async def handle_n8n_execute_workflow(self, workflow_name, input_data=None):
        """Handle executing an n8n workflow. workflow_name can be the workflow ID."""
        print(f"[ADA DEBUG] [N8N] Executing workflow: {workflow_name}")

        # Parse input_data if it's a JSON string
        parsed_data = {}
        if input_data:
            import json
            try:
                parsed_data = json.loads(input_data)
            except:
                parsed_data = {"input": input_data}

        # workflow_name is actually the workflow ID
        result = await self.agent.execute_workflow(workflow_name, parsed_data)

        if result.get("success"):
            exec_result = result.get("result", {})
            if isinstance(exec_result, dict):
                exec_id = exec_result.get("executionId", "N/A")
                if exec_result.get("success", True):
                    message = f"Workflow executed successfully! Execution ID: {exec_id}"
                else:
                    error_msg = exec_result.get("result", {}).get("error", {}).get("message", "Unknown error")
                    message = f"Workflow execution completed with warning. Execution ID: {exec_id}\nDetails: {str(error_msg)[:200]}"
            else:
                message = f"Workflow executed successfully! Result: {exec_result}"
        else:
            message = f"Workflow execution failed: {result.get('error', 'Unknown error')}"

        return {"result": message}

    async def handle_n8n_get_workflow_info(self, workflow_name):
        """Handle getting workflow details."""
        print(f"[ADA DEBUG] [N8N] Getting info for workflow: {workflow_name}")
        result = await self.agent.get_workflow_info(workflow_name)

        if result.get("success"):
            workflow = result.get("workflow", {})
            # Handle both string and dict responses
            if isinstance(workflow, str):
                message = f"Workflow Info: {workflow}"
            elif isinstance(workflow, dict):
                message = f"Workflow: {workflow.get('name', 'Unknown')}\n"
                message += f"Description: {workflow.get('description', 'No description')}\n"
                if workflow.get("input_schema"):
                    message += f"Input Schema: {workflow.get('input_schema')}"
            else:
                message = f"Workflow Info: {str(workflow)}"
        else:
            message = f"Failed to get workflow info: {result.get('error', 'Unknown error')}"

        return {"result": message, "workflow": result.get("workflow", {})}
