wa_send_message_tool = {
    "name": "wa_send_message",
    "description": "Send a WhatsApp message to a phone number. Use Indonesian format (08xxx or 628xxx).",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "phone": {"type": "STRING", "description": "Destination phone number (e.g., 08123456789 or 628123456789)"},
            "message": {"type": "STRING", "description": "Message content to send"}
        },
        "required": ["phone", "message"]
    }
}

wa_check_status_tool = {
    "name": "wa_check_status",
    "description": "Check WhatsApp connection status.",
    "parameters": {
        "type": "OBJECT",
        "properties": {},
        "required": []
    }
}

# WhatsApp tools list
definitions = [
    wa_send_message_tool,
    wa_check_status_tool,
]
