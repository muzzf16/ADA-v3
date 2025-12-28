"""Debug script to see raw MCP response from n8n."""
import asyncio
import aiohttp
import os
from dotenv import load_dotenv
import json

load_dotenv()

async def test():
    url = os.getenv('N8N_MCP_URL')
    token = os.getenv('N8N_MCP_TOKEN')
    
    print(f"URL: {url}")
    print(f"Token: {token[:10]}...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'Accept': 'application/json, text/event-stream',
    }
    
    async with aiohttp.ClientSession() as session:
        payload = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'tools/list'
        }
        
        async with session.post(url, json=payload, headers=headers) as resp:
            print(f'Status: {resp.status}')
            print(f'Content-Type: {resp.headers.get("Content-Type")}')
            print(f'Session-Id: {resp.headers.get("Mcp-Session-Id", "N/A")}')
            print()
            
            content_type = resp.headers.get("Content-Type", "")
            
            if "text/event-stream" in content_type:
                print("=== SSE Response ===")
                async for line in resp.content:
                    decoded = line.decode('utf-8').strip()
                    if decoded:
                        print(f"  {decoded}")
                        if decoded.startswith('data:'):
                            data_str = decoded[5:].strip()
                            if data_str:
                                try:
                                    data = json.loads(data_str)
                                    print(f"\nParsed JSON:")
                                    print(json.dumps(data, indent=2))
                                except json.JSONDecodeError as e:
                                    print(f"JSON parse error: {e}")
            else:
                print("=== JSON Response ===")
                text = await resp.text()
                print(text)
                try:
                    data = json.loads(text)
                    print("\nParsed:")
                    print(json.dumps(data, indent=2))
                except:
                    pass

asyncio.run(test())
