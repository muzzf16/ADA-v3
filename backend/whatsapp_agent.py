"""
WhatsApp Agent - Handles WhatsApp messaging for A.D.A
Integrates with local WhatsApp Dashboard API.
"""

import os
import asyncio
from typing import Optional, Dict, Any
from dotenv import load_dotenv

try:
    import aiohttp
except ImportError:
    aiohttp = None

load_dotenv()


class WhatsAppAgent:
    """
    Agent for WhatsApp operations.
    
    Provides methods to:
    - Send text messages
    - Send media files
    - Check connection status
    """
    
    def __init__(self):
        """Initialize the WhatsApp Agent."""
        base_url = os.getenv("WHATSAPP_API_URL", "http://localhost:4000")
        # Remove trailing slash to prevent double slashes in URLs
        self.base_url = base_url.rstrip('/')
        self.default_connection_id = os.getenv("WHATSAPP_CONNECTION_ID", "main")
        self._session: Optional[aiohttp.ClientSession] = None
        
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
    
    def _format_phone_number(self, phone: str) -> str:
        """
        Format phone number to ensure it has country code.
        
        Args:
            phone: Phone number (can be 08xxx or 62xxx or +62xxx)
        
        Returns:
            Formatted phone number with 62 prefix
        """
        # Remove all non-digit characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Handle Indonesian numbers
        if phone.startswith('0'):
            phone = '62' + phone[1:]
        elif phone.startswith('8'):
            phone = '62' + phone
        
        return phone
    
    async def send_message(self, phone: str, message: str, connection_id: str = None) -> Dict[str, Any]:
        """
        Send a text message via WhatsApp.
        
        Args:
            phone: Destination phone number
            message: Message content
            connection_id: WhatsApp connection ID (optional, uses default if not specified)
        
        Returns:
            dict with success status and message details
        """
        if not phone:
            return {"success": False, "error": "Phone number is required"}
        
        if not message:
            return {"success": False, "error": "Message is required"}
        
        conn_id = connection_id or self.default_connection_id
        formatted_phone = self._format_phone_number(phone)
        
        url = f"{self.base_url}/api/{conn_id}/send-message"
        
        try:
            session = await self._get_session()
            
            payload = {
                "number": formatted_phone,
                "message": message
            }
            
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with session.post(url, json=payload, timeout=timeout) as response:
                response_text = await response.text()
                
                try:
                    import json
                    response_data = json.loads(response_text)
                except:
                    response_data = {"raw": response_text}
                
                if response.status < 400:
                    return {
                        "success": True,
                        "phone": formatted_phone,
                        "message": message[:50] + "..." if len(message) > 50 else message,
                        "response": response_data
                    }
                else:
                    return {
                        "success": False,
                        "status_code": response.status,
                        "error": f"HTTP {response.status}",
                        "response": response_data
                    }
                    
        except aiohttp.ClientConnectorError as e:
            return {
                "success": False,
                "error": f"Cannot connect to WhatsApp API at {self.base_url}. Is the server running?"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def send_media(self, phone: str, media_url: str, caption: str = "", connection_id: str = None) -> Dict[str, Any]:
        """
        Send a media file via WhatsApp.
        
        Args:
            phone: Destination phone number
            media_url: URL or path to media file
            caption: Optional caption for the media
            connection_id: WhatsApp connection ID
        
        Returns:
            dict with success status
        """
        if not phone:
            return {"success": False, "error": "Phone number is required"}
        
        if not media_url:
            return {"success": False, "error": "Media URL is required"}
        
        conn_id = connection_id or self.default_connection_id
        formatted_phone = self._format_phone_number(phone)
        
        url = f"{self.base_url}/api/{conn_id}/send-message"
        
        try:
            session = await self._get_session()
            
            payload = {
                "number": formatted_phone,
                "message": caption,
                "file": {
                    "url": media_url
                }
            }
            
            timeout = aiohttp.ClientTimeout(total=60)
            
            async with session.post(url, json=payload, timeout=timeout) as response:
                if response.status < 400:
                    return {
                        "success": True,
                        "phone": formatted_phone,
                        "media": media_url
                    }
                else:
                    return {
                        "success": False,
                        "status_code": response.status,
                        "error": f"HTTP {response.status}"
                    }
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def check_connection(self, connection_id: str = None) -> Dict[str, Any]:
        """
        Check if WhatsApp connection is active.
        
        Args:
            connection_id: WhatsApp connection ID
        
        Returns:
            dict with connection status
        """
        conn_id = connection_id or self.default_connection_id
        url = f"{self.base_url}/api/{conn_id}/status"
        
        try:
            session = await self._get_session()
            
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with session.get(url, timeout=timeout) as response:
                if response.status < 400:
                    import json
                    try:
                        data = await response.json()
                    except:
                        data = {"status": "unknown"}
                    
                    return {
                        "success": True,
                        "connection_id": conn_id,
                        "status": data.get("status", "connected"),
                        "data": data
                    }
                else:
                    return {
                        "success": False,
                        "connection_id": conn_id,
                        "status": "disconnected",
                        "error": f"HTTP {response.status}"
                    }
                    
        except aiohttp.ClientConnectorError:
            return {
                "success": False,
                "connection_id": conn_id,
                "status": "offline",
                "error": f"WhatsApp API server not reachable at {self.base_url}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def list_connections(self) -> Dict[str, Any]:
        """
        List available WhatsApp connections.
        
        Returns:
            dict with list of connections
        """
        url = f"{self.base_url}/api/connections"
        
        try:
            session = await self._get_session()
            
            async with session.get(url) as response:
                if response.status < 400:
                    data = await response.json()
                    return {
                        "success": True,
                        "connections": data
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}"
                    }
                    
        except aiohttp.ClientConnectorError:
            return {
                "success": False,
                "error": f"WhatsApp API server not reachable at {self.base_url}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton instance
_agent_instance: Optional[WhatsAppAgent] = None


def get_whatsapp_agent() -> WhatsAppAgent:
    """Get or create the singleton WhatsAppAgent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = WhatsAppAgent()
    return _agent_instance


# Test function
async def test_agent():
    """Test the WhatsApp Agent."""
    agent = get_whatsapp_agent()
    
    print(f"Base URL: {agent.base_url}")
    print(f"Default Connection: {agent.default_connection_id}")
    
    print("\n1. Check connection...")
    result = await agent.check_connection()
    print(f"   {result}")
    
    await agent.close()


if __name__ == "__main__":
    asyncio.run(test_agent())
