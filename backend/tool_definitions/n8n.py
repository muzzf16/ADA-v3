# N8N MCP Tools Definitions

n8n_connect_tool = {
    "name": "n8n_connect",
    "description": "Connect to n8n MCP Server. Use this to test the connection to n8n workflow automation.",
    "parameters": {
        "type": "OBJECT",
        "properties": {},
    }
}

n8n_list_workflows_tool = {
    "name": "n8n_list_workflows",
    "description": "List all available workflows in n8n that are exposed via MCP. Use when user wants to see what automations are available.",
    "parameters": {
        "type": "OBJECT",
        "properties": {},
    }
}

n8n_search_workflows_tool = {
    "name": "n8n_search_workflows",
    "description": "Search for workflows in n8n by name or description.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query": {"type": "STRING", "description": "Search query to find workflows."}
        },
        "required": ["query"]
    }
}

n8n_execute_workflow_tool = {
    "name": "n8n_execute_workflow",
    "description": "Execute an n8n workflow with optional input data. Use when user wants to run an automation workflow.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "workflow_name": {"type": "STRING", "description": "Name of the workflow to execute (from list_workflows)."},
            "input_data": {"type": "STRING", "description": "JSON string of input data to pass to the workflow. Optional."}
        },
        "required": ["workflow_name"]
    }
}

n8n_get_workflow_info_tool = {
    "name": "n8n_get_workflow_info",
    "description": "Get detailed information about a specific n8n workflow including its input schema.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "workflow_name": {"type": "STRING", "description": "Name of the workflow to get info about."}
        },
        "required": ["workflow_name"]
    }
}

# n8n MCP tools list
definitions = [
    n8n_connect_tool,
    n8n_list_workflows_tool,
    n8n_search_workflows_tool,
    n8n_execute_workflow_tool,
    n8n_get_workflow_info_tool,
]
