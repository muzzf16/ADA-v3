
import os
import asyncio
import aiohttp
from dotenv import load_dotenv

# Load the latest .env file
load_dotenv()

async def test_connection():
    base_url = os.getenv("WHATSAPP_API_URL")
    conn_id = os.getenv("WHATSAPP_CONNECTION_ID")
    
    print(f"Testing Config:")
    print(f"URL: {base_url}")
    print(f"ID: {conn_id}")
    
    if not base_url:
        print("ERROR: WHATSAPP_API_URL not found in .env")
        return

    # Test Status Endpoint
    # Expected: https://api.kenes.biz.id/api/ipad/status
    url = f"{base_url}/api/{conn_id}/status"
    print(f"Hitting: {url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                print(f"Status Code: {resp.status}")
                text = await resp.text()
                print(f"Response: {text}")
                
    except Exception as e:
        print(f"Connection Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection())
