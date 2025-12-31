
print("Start test...")
try:
    import google.oauth2.credentials
    print("Imported google.oauth2")
    from google_workspace_agent import get_workspace_agent
    print("Imported google_workspace_agent")
except Exception as e:
    print(f"Error: {e}")
print("End test")
