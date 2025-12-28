"""
Webhook Agent - Handles webhook receiving and sending for A.D.A
Allows A.D.A to receive notifications from external services and send data to webhooks.
"""

import os
import asyncio
import json
import uuid
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime
from dotenv import load_dotenv

try:
    import aiohttp
except ImportError:
    aiohttp = None

load_dotenv()


class WebhookAgent:
    """
    Agent for webhook operations.
    
    Provides methods to:
    - Register webhook endpoints
    - Receive incoming webhooks
    - Send data to external webhook URLs
    - Manage webhook subscriptions
    """
    
    def __init__(self, on_webhook_received: Callable = None):
        """
        Initialize the Webhook Agent.
        
        Args:
            on_webhook_received: Callback function when webhook is received
                                 signature: async def callback(source: str, data: dict)
        """
        self.on_webhook_received = on_webhook_received
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Registered webhooks with their handlers
        self._registered_webhooks: Dict[str, Dict] = {}
        
        # Incoming webhook queue
        self._webhook_queue: asyncio.Queue = asyncio.Queue()
        
        # Saved webhook URLs for quick access
        self._saved_webhooks: Dict[str, str] = {}
        
        # Load saved webhooks from environment
        self._load_saved_webhooks()
    
    def _load_saved_webhooks(self):
        """Load saved webhook URLs from environment."""
        # Check for common webhook URLs in environment
        webhook_vars = [
            ("N8N_WEBHOOK", os.getenv("N8N_WEBHOOK_URL", "")),
            ("DISCORD_WEBHOOK", os.getenv("DISCORD_WEBHOOK_URL", "")),
            ("SLACK_WEBHOOK", os.getenv("SLACK_WEBHOOK_URL", "")),
            ("CUSTOM_WEBHOOK", os.getenv("CUSTOM_WEBHOOK_URL", "")),
        ]
        
        for name, url in webhook_vars:
            if url:
                self._saved_webhooks[name.lower()] = url
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if aiohttp is None:
            raise ImportError("aiohttp is required. Install with: pip install aiohttp")
            
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    def register_webhook(self, webhook_id: str, source: str, description: str = "") -> Dict[str, Any]:
        """
        Register a new webhook endpoint.
        
        Args:
            webhook_id: Unique ID for the webhook
            source: Source name (e.g., 'whatsapp', 'n8n', 'custom')
            description: Description of what this webhook handles
            
        Returns:
            dict with webhook details
        """
        self._registered_webhooks[webhook_id] = {
            "id": webhook_id,
            "source": source,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "last_triggered": None,
            "trigger_count": 0
        }
        
        return {
            "success": True,
            "webhook_id": webhook_id,
            "endpoint": f"/webhook/{webhook_id}",
            "message": f"Webhook registered: {source}"
        }
    
    async def process_incoming_webhook(self, webhook_id: str, data: Dict[str, Any], headers: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Process an incoming webhook request.
        
        Args:
            webhook_id: ID of the webhook endpoint
            data: Payload data from the webhook
            headers: HTTP headers from the request
        """
        # Find registered webhook
        webhook = self._registered_webhooks.get(webhook_id)
        
        if not webhook:
            # Auto-register if not exists
            webhook = {
                "id": webhook_id,
                "source": "unknown",
                "description": "Auto-registered webhook",
                "created_at": datetime.now().isoformat(),
                "last_triggered": None,
                "trigger_count": 0
            }
            self._registered_webhooks[webhook_id] = webhook
        
        # Update webhook stats
        webhook["last_triggered"] = datetime.now().isoformat()
        webhook["trigger_count"] = webhook.get("trigger_count", 0) + 1
        
        # Format message for A.D.A
        event_data = {
            "webhook_id": webhook_id,
            "source": webhook.get("source", "unknown"),
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "headers": headers or {}
        }
        
        # Add to queue for processing
        await self._webhook_queue.put(event_data)
        
        # Notify callback if set
        if self.on_webhook_received:
            try:
                await self.on_webhook_received(webhook.get("source", "unknown"), event_data)
            except Exception as e:
                print(f"[WEBHOOK] Error in callback: {e}")
        
        return {
            "success": True,
            "message": "Webhook received",
            "webhook_id": webhook_id
        }
    
    async def get_pending_webhooks(self) -> List[Dict[str, Any]]:
        """Get all pending webhooks from queue."""
        webhooks = []
        while not self._webhook_queue.empty():
            try:
                webhooks.append(self._webhook_queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        return webhooks
    
    async def send_webhook(self, url: str, data: Dict[str, Any], method: str = "POST", headers: Dict[str, str] = None) -> Dict[str, Any]:
        """
        Send data to an external webhook URL.
        
        Args:
            url: Webhook URL to send to
            data: Data payload to send
            method: HTTP method (POST, PUT, etc.)
            headers: Additional headers
        """
        if not url:
            return {"success": False, "error": "URL is required"}
        
        try:
            session = await self._get_session()
            
            request_headers = {
                "Content-Type": "application/json",
                "User-Agent": "ADA-Webhook/1.0"
            }
            if headers:
                request_headers.update(headers)
            
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with session.request(
                method=method.upper(),
                url=url,
                json=data,
                headers=request_headers,
                timeout=timeout
            ) as response:
                response_text = await response.text()
                
                # Try to parse as JSON
                try:
                    response_data = json.loads(response_text)
                except:
                    response_data = response_text
                
                if response.status < 400:
                    return {
                        "success": True,
                        "status_code": response.status,
                        "response": response_data
                    }
                else:
                    return {
                        "success": False,
                        "status_code": response.status,
                        "error": f"HTTP {response.status}",
                        "response": response_data
                    }
                    
        except aiohttp.ClientError as e:
            return {"success": False, "error": f"Connection error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Error: {str(e)}"}
    
    async def send_to_saved_webhook(self, webhook_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send data to a saved webhook by name.
        
        Args:
            webhook_name: Name of saved webhook (e.g., 'n8n', 'discord', 'slack')
            data: Data to send
        """
        name_lower = webhook_name.lower().strip()
        
        # Check for exact match
        url = self._saved_webhooks.get(name_lower)
        
        # Try with _webhook suffix
        if not url:
            url = self._saved_webhooks.get(f"{name_lower}_webhook")
        
        if not url:
            available = ', '.join(self._saved_webhooks.keys()) if self._saved_webhooks else "none"
            return {
                "success": False,
                "error": f"Webhook '{webhook_name}' not found. Available: {available}"
            }
        
        return await self.send_webhook(url, data)
    
    def save_webhook_url(self, name: str, url: str) -> Dict[str, Any]:
        """
        Save a webhook URL for quick access.
        
        Args:
            name: Name to save as
            url: Webhook URL
        """
        self._saved_webhooks[name.lower().strip()] = url
        return {
            "success": True,
            "name": name,
            "message": f"Webhook '{name}' saved"
        }
    
    def list_saved_webhooks(self) -> Dict[str, Any]:
        """List all saved webhook URLs."""
        return {
            "success": True,
            "webhooks": [
                {"name": name, "url": url[:50] + "..." if len(url) > 50 else url}
                for name, url in self._saved_webhooks.items()
            ],
            "count": len(self._saved_webhooks)
        }
    
    def list_registered_webhooks(self) -> Dict[str, Any]:
        """List all registered incoming webhooks."""
        return {
            "success": True,
            "webhooks": list(self._registered_webhooks.values()),
            "count": len(self._registered_webhooks)
        }


# Singleton instance
_agent_instance: Optional[WebhookAgent] = None


def get_webhook_agent(on_webhook_received: Callable = None) -> WebhookAgent:
    """Get or create the singleton WebhookAgent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = WebhookAgent(on_webhook_received=on_webhook_received)
    return _agent_instance


# Test function
async def test_agent():
    """Test the Webhook Agent."""
    agent = get_webhook_agent()
    
    print("1. List saved webhooks...")
    result = agent.list_saved_webhooks()
    print(f"   {result}")
    
    print("\n2. Register a test webhook...")
    result = agent.register_webhook("test-webhook", "test", "Test webhook")
    print(f"   {result}")
    
    print("\n3. List registered webhooks...")
    result = agent.list_registered_webhooks()
    print(f"   {result}")
    
    await agent.close()


if __name__ == "__main__":
    asyncio.run(test_agent())
