# Google Workspace Tools Definitions

google_authenticate_tool = {
    "name": "google_authenticate",
    "description": "Authenticates with Google Workspace services. Opens a browser window for user to log in. Use this first before any Google Workspace operations.",
    "parameters": {
        "type": "OBJECT",
        "properties": {},
    }
}

# Calendar Tools
google_list_events_tool = {
    "name": "google_list_events",
    "description": "Lists upcoming events from Google Calendar. Use when user asks about their schedule, meetings, or upcoming appointments.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "max_results": {"type": "INTEGER", "description": "Maximum number of events to return. Default 10."},
            "time_min": {"type": "STRING", "description": "Start time in ISO format. Defaults to now."},
            "time_max": {"type": "STRING", "description": "End time in ISO format. Optional."}
        },
        "required": []
    }
}

google_create_event_tool = {
    "name": "google_create_event",
    "description": "Creates a new event in Google Calendar. Use when user wants to schedule a meeting, appointment, or reminder.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "summary": {"type": "STRING", "description": "Event title/name."},
            "start_time": {"type": "STRING", "description": "Start time (ISO format or natural language like 'tomorrow 10am')."},
            "end_time": {"type": "STRING", "description": "End time (ISO format). Optional, defaults to 1 hour after start."},
            "description": {"type": "STRING", "description": "Event description. Optional."},
            "location": {"type": "STRING", "description": "Event location. Optional."},
            "attendees": {"type": "STRING", "description": "Comma-separated email addresses to invite. Optional."}
        },
        "required": ["summary", "start_time"]
    }
}

google_delete_event_tool = {
    "name": "google_delete_event",
    "description": "Deletes an event from Google Calendar.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "event_id": {"type": "STRING", "description": "The ID of the event to delete."}
        },
        "required": ["event_id"]
    }
}

# Sheets Tools
google_read_spreadsheet_tool = {
    "name": "google_read_spreadsheet",
    "description": "Reads data from a Google Spreadsheet. Use when user wants to view or get data from a spreadsheet.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "spreadsheet_id": {"type": "STRING", "description": "The ID of the spreadsheet (from URL)."},
            "range_name": {"type": "STRING", "description": "The range to read (e.g., 'Sheet1!A1:D10'). Default 'Sheet1!A1:Z100'."}
        },
        "required": ["spreadsheet_id"]
    }
}

google_write_spreadsheet_tool = {
    "name": "google_write_spreadsheet",
    "description": "Writes or updates data in a Google Spreadsheet. Use when user wants to update specific cells.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "spreadsheet_id": {"type": "STRING", "description": "The ID of the spreadsheet."},
            "range_name": {"type": "STRING", "description": "The range to write to (e.g., 'Sheet1!A1')."},
            "values": {"type": "STRING", "description": "JSON array of rows to write, e.g., '[[\"Name\", \"Age\"], [\"John\", 30]]'."}
        },
        "required": ["spreadsheet_id", "range_name", "values"]
    }
}

google_append_spreadsheet_tool = {
    "name": "google_append_spreadsheet",
    "description": "Appends new rows to a Google Spreadsheet. Use when user wants to add data without overwriting existing data.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "spreadsheet_id": {"type": "STRING", "description": "The ID of the spreadsheet."},
            "range_name": {"type": "STRING", "description": "The range to append to (e.g., 'Sheet1!A:D')."},
            "values": {"type": "STRING", "description": "JSON array of rows to append, e.g., '[[\"John\", 30, \"Engineer\"]]'."}
        },
        "required": ["spreadsheet_id", "range_name", "values"]
    }
}

google_create_spreadsheet_tool = {
    "name": "google_create_spreadsheet",
    "description": "Creates a new Google Spreadsheet. Use when user wants to create a new spreadsheet.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "title": {"type": "STRING", "description": "Title of the new spreadsheet."},
            "sheets": {"type": "STRING", "description": "Comma-separated list of sheet names to create. Optional."}
        },
        "required": ["title"]
    }
}

google_add_sheet_tool = {
    "name": "google_add_sheet",
    "description": "Adds a new sheet to an existing Google Spreadsheet.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "spreadsheet_id": {"type": "STRING", "description": "The ID of the spreadsheet."},
            "title": {"type": "STRING", "description": "Title of the new sheet."}
        },
        "required": ["spreadsheet_id", "title"]
    }
}

google_delete_sheet_tool = {
    "name": "google_delete_sheet",
    "description": "Deletes a sheet from a Google Spreadsheet. PLEASE BE CAREFUL: This action is permanent.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "spreadsheet_id": {"type": "STRING", "description": "The ID of the spreadsheet."},
            "sheet_title": {"type": "STRING", "description": "The title of the sheet to delete."}
        },
        "required": ["spreadsheet_id", "sheet_title"]
    }
}

# Drive Tools
google_list_drive_files_tool = {
    "name": "google_list_drive_files",
    "description": "Lists files in Google Drive. Use when user wants to see files in their Drive.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query": {"type": "STRING", "description": "Search query (e.g., \"name contains 'report'\"). Optional."},
            "max_results": {"type": "INTEGER", "description": "Maximum number of files to return. Default 20."},
            "folder_id": {"type": "STRING", "description": "ID of folder to list. Optional."}
        },
        "required": []
    }
}

google_upload_to_drive_tool = {
    "name": "google_upload_to_drive",
    "description": "Uploads a file to Google Drive. Use when user wants to upload a local file to Drive.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "file_path": {"type": "STRING", "description": "Local path to the file to upload."},
            "folder_id": {"type": "STRING", "description": "ID of the folder to upload to. Optional."},
            "file_name": {"type": "STRING", "description": "Name for the file in Drive. Optional, uses original name."}
        },
        "required": ["file_path"]
    }
}

google_download_from_drive_tool = {
    "name": "google_download_from_drive",
    "description": "Downloads a file from Google Drive. Use when user wants to download a file from Drive.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "file_id": {"type": "STRING", "description": "ID of the file to download."},
            "destination_path": {"type": "STRING", "description": "Local path to save the file."}
        },
        "required": ["file_id", "destination_path"]
    }
}

google_create_drive_folder_tool = {
    "name": "google_create_drive_folder",
    "description": "Creates a new folder in Google Drive. Use when user wants to create a new folder.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "folder_name": {"type": "STRING", "description": "Name of the new folder."},
            "parent_id": {"type": "STRING", "description": "ID of parent folder. Optional."}
        },
        "required": ["folder_name"]
    }
}

# Gmail Tools
google_send_email_tool = {
    "name": "google_send_email",
    "description": "Sends an email via Gmail. Use when user wants to send an email.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "to": {"type": "STRING", "description": "Recipient email address."},
            "subject": {"type": "STRING", "description": "Email subject."},
            "body": {"type": "STRING", "description": "Email body content."},
            "cc": {"type": "STRING", "description": "CC recipients (comma-separated). Optional."},
            "bcc": {"type": "STRING", "description": "BCC recipients (comma-separated). Optional."}
        },
        "required": ["to", "subject", "body"]
    }
}

google_list_emails_tool = {
    "name": "google_list_emails",
    "description": "Lists emails from Gmail inbox. Use when user wants to check their emails.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "max_results": {"type": "INTEGER", "description": "Maximum number of emails to return. Default 10."},
            "query": {"type": "STRING", "description": "Gmail search query (e.g., 'is:unread', 'from:someone@gmail.com'). Optional."}
        },
        "required": []
    }
}

google_read_email_tool = {
    "name": "google_read_email",
    "description": "Reads a specific email by ID. Use when user wants to view an email's full content.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "message_id": {"type": "STRING", "description": "ID of the email to read."}
        },
        "required": ["message_id"]
    }
}

# Docs Tools
google_create_document_tool = {
    "name": "google_create_document",
    "description": "Creates a new Google Document. Use when user wants to create a new document.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "title": {"type": "STRING", "description": "Document title."},
            "content": {"type": "STRING", "description": "Initial content to add. Optional."}
        },
        "required": ["title"]
    }
}

google_read_document_tool = {
    "name": "google_read_document",
    "description": "Reads content from a Google Document. Use when user wants to view document content.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "document_id": {"type": "STRING", "description": "ID of the document to read."}
        },
        "required": ["document_id"]
    }
}

google_append_document_tool = {
    "name": "google_append_document",
    "description": "Appends text to the end of a Google Document. Use when user wants to add content to a document.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "document_id": {"type": "STRING", "description": "ID of the document."},
            "content": {"type": "STRING", "description": "Text content to append."}
        },
        "required": ["document_id", "content"]
    }
}

# Forms Tools
google_create_form_tool = {
    "name": "google_create_form",
    "description": "Creates a new Google Form. Use when user wants to create a survey, questionnaire, or form.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "title": {"type": "STRING", "description": "Title of the form."},
            "document_title": {"type": "STRING", "description": "Filename in Drive. Optional, defaults to title."}
        },
        "required": ["title"]
    }
}

# Slides Tools
google_create_presentation_tool = {
    "name": "google_create_presentation",
    "description": "Creates a new Google Slides presentation. Use when user wants to create slides or a presentation.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "title": {"type": "STRING", "description": "Title of the presentation."}
        },
        "required": ["title"]
    }
}

# Google Workspace tools list
definitions = [
    google_authenticate_tool,
    google_list_events_tool,
    google_create_event_tool,
    google_delete_event_tool,
    google_read_spreadsheet_tool,
    google_write_spreadsheet_tool,
    google_append_spreadsheet_tool,
    google_create_spreadsheet_tool,
    google_add_sheet_tool,
    google_delete_sheet_tool,
    google_list_drive_files_tool,
    google_upload_to_drive_tool,
    google_download_from_drive_tool,
    google_create_drive_folder_tool,
    google_send_email_tool,
    google_list_emails_tool,
    google_read_email_tool,
    google_create_document_tool,
    google_read_document_tool,
    google_append_document_tool,
    google_create_form_tool,
    google_create_presentation_tool,
]
