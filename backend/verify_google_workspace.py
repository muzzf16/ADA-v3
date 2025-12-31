
import asyncio
import os
import sys
from google_workspace_agent import get_workspace_agent

# Add backend directory to path so imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def verify():
    print("=== Google Workspace Verification ===")
    
    agent = get_workspace_agent()
    
    print(f"\n[1] Checking Credentials...")
    if not agent.is_authenticated():
        print("❌ Not authenticated. Please run the app and say 'Authenticate with Google'.")
        print(f"Credentials path: {agent.credentials_path}")
        print(f"Token path: {agent.token_path}")
        return
    else:
        print("✅ Credentials loaded and valid.")

    # 1. Calendar
    print(f"\n[2] Testing Google Calendar...")
    try:
        res = await agent.list_calendar_events(max_results=3)
        if res.get("success"):
            print(f"✅ Calendar Success! Found {res.get('count')} events.")
            for e in res.get("events", []):
                print(f"   - {e['summary']} ({e['start']})")
        else:
            print(f"❌ Calendar Failed: {res.get('error')}")
    except Exception as e:
         print(f"❌ Calendar Exception: {e}")

    # 2. Gmail
    print(f"\n[3] Testing Gmail...")
    try:
        res = await agent.list_emails(max_results=3)
        if res.get("success"):
            print(f"✅ Gmail Success! Found {res.get('count')} emails.")
            for e in res.get("emails", []):
                print(f"   - {e['subject']} (from: {e['from']})")
        else:
            print(f"❌ Gmail Failed: {res.get('error')}")
    except Exception as e:
         print(f"❌ Gmail Exception: {e}")

    # 3. Drive
    print(f"\n[4] Testing Google Drive...")
    try:
        res = await agent.list_drive_files(max_results=3)
        if res.get("success"):
            print(f"✅ Drive Success! Found {res.get('count')} files.")
            for f in res.get("files", []):
                print(f"   - {f['name']} ({f['mimeType']})")
        else:
            print(f"❌ Drive Failed: {res.get('error')}")
    except Exception as e:
         print(f"❌ Drive Exception: {e}")

    print("\n=== Verification Complete ===")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify())
