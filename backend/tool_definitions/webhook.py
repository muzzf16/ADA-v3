webhook_send_tool = {
    "name": "webhook_send",
    "description": "Send data to a webhook URL. Use to trigger external automations, notify services, or send data to n8n/Discord/Slack.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "url": {"type": "STRING", "description": "Webhook URL to send to"},
            "data": {"type": "STRING", "description": "JSON data to send (as string)"},
            "method": {"type": "STRING", "description": "HTTP method: POST (default), PUT, etc."}
        },
        "required": ["url", "data"]
    }
}

webhook_send_saved_tool = {
    "name": "webhook_send_saved",
    "description": "Send data to a saved webhook by name. Saved webhooks: n8n, discord, slack, custom.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "webhook_name": {"type": "STRING", "description": "Name of saved webhook: n8n, discord, slack, custom"},
            "data": {"type": "STRING", "description": "JSON data to send (as string)"}
        },
        "required": ["webhook_name", "data"]
    }
}

webhook_list_tool = {
    "name": "webhook_list",
    "description": "List all saved and registered webhooks.",
    "parameters": {
        "type": "OBJECT",
        "properties": {},
        "required": []
    }
}

# Webhook tools list
definitions = [
    webhook_send_tool,
    webhook_send_saved_tool,
    webhook_list_tool,
]
