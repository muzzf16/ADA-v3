yahoo_send_email_tool = {
    "name": "yahoo_send_email",
    "description": "Sends an email via Yahoo Mail. Use when user wants to send email from their Yahoo account.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "to": {"type": "STRING", "description": "Recipient email address."},
            "subject": {"type": "STRING", "description": "Email subject."},
            "body": {"type": "STRING", "description": "Email body content."}
        },
        "required": ["to", "subject", "body"]
    }
}

yahoo_list_emails_tool = {
    "name": "yahoo_list_emails",
    "description": "Lists recent emails from Yahoo Mail inbox. Use when user wants to check their Yahoo emails.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "limit": {"type": "INTEGER", "description": "Maximum emails to return. Default 5."}
        },
        "required": []
    }
}

# Yahoo Mail tools list
definitions = [
    yahoo_send_email_tool,
    yahoo_list_emails_tool,
]
