import asyncio
import base64
import io
import os
import sys
import traceback
from dotenv import load_dotenv
import cv2
import pyaudio
import PIL.Image
import mss
import argparse
import math
import struct
import time

from google import genai
from google.genai import types

if sys.version_info < (3, 11, 0):
    import taskgroup, exceptiongroup
    asyncio.TaskGroup = taskgroup.TaskGroup
    asyncio.ExceptionGroup = exceptiongroup.ExceptionGroup

from tools import tools_list

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

MODEL = "models/gemini-2.5-flash-native-audio-preview-12-2025"
DEFAULT_MODE = "camera"

load_dotenv()
client = genai.Client(http_options={"api_version": "v1beta"}, api_key=os.getenv("GEMINI_API_KEY"))



run_web_agent = {
    "name": "run_web_agent",
    "description": "Opens a web browser and performs a task according to the prompt.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "prompt": {"type": "STRING", "description": "The detailed instructions for the web browser agent."}
        },
        "required": ["prompt"]
    },
    "behavior": "NON_BLOCKING"
}

create_project_tool = {
    "name": "create_project",
    "description": "Creates a new project folder to organize files.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "name": {"type": "STRING", "description": "The name of the new project."}
        },
        "required": ["name"]
    }
}

switch_project_tool = {
    "name": "switch_project",
    "description": "Switches the current active project context.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "name": {"type": "STRING", "description": "The name of the project to switch to."}
        },
        "required": ["name"]
    }
}

list_projects_tool = {
    "name": "list_projects",
    "description": "Lists all available projects.",
    "parameters": {
        "type": "OBJECT",
        "properties": {},
    }
}

list_smart_devices_tool = {
    "name": "list_smart_devices",
    "description": "Lists all available smart home devices (lights, plugs, etc.) on the network.",
    "parameters": {
        "type": "OBJECT",
        "properties": {},
    }
}

control_light_tool = {
    "name": "control_light",
    "description": "Controls a smart light device.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "target": {
                "type": "STRING",
                "description": "The IP address of the device to control. Always prefer the IP address over the alias for reliability."
            },
            "action": {
                "type": "STRING",
                "description": "The action to perform: 'turn_on', 'turn_off', or 'set'."
            },
            "brightness": {
                "type": "INTEGER",
                "description": "Optional brightness level (0-100)."
            },
            "color": {
                "type": "STRING",
                "description": "Optional color name (e.g., 'red', 'cool white') or 'warm'."
            }
        },
        "required": ["target", "action"]
    }
}









# ==================== GOOGLE WORKSPACE TOOLS ====================

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
google_workspace_tools = [
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


# ==================== N8N MCP TOOLS ====================

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
n8n_mcp_tools = [
    n8n_connect_tool,
    n8n_list_workflows_tool,
    n8n_search_workflows_tool,
    n8n_execute_workflow_tool,
    n8n_get_workflow_info_tool,
]

# ==================== LOCAL PC TOOLS ====================

pc_create_file_tool = {
    "name": "pc_create_file",
    "description": "Create a new file on the local PC. Use when user wants to create a new file. Paths are relative to user folders like Desktop, Documents, Downloads.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "path": {"type": "STRING", "description": "File path, e.g., 'Desktop/notes.txt' or 'Documents/report.md'"},
            "content": {"type": "STRING", "description": "Content to write to the file. Optional."}
        },
        "required": ["path"]
    }
}

pc_read_file_tool = {
    "name": "pc_read_file",
    "description": "Read content from a file on the local PC. Use when user wants to see what's in a file.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "path": {"type": "STRING", "description": "File path to read, e.g., 'Desktop/notes.txt'"}
        },
        "required": ["path"]
    }
}

pc_write_file_tool = {
    "name": "pc_write_file",
    "description": "Write content to a file on the local PC. Creates or overwrites the file.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "path": {"type": "STRING", "description": "File path to write to"},
            "content": {"type": "STRING", "description": "Content to write"}
        },
        "required": ["path", "content"]
    }
}

pc_list_folder_tool = {
    "name": "pc_list_folder",
    "description": "List contents of a folder on the local PC. Use when user wants to see files in a folder.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "path": {"type": "STRING", "description": "Folder path, e.g., 'Desktop', 'Documents', 'Downloads'. Defaults to Documents."}
        },
        "required": []
    }
}

pc_create_folder_tool = {
    "name": "pc_create_folder",
    "description": "Create a new folder on the local PC.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "path": {"type": "STRING", "description": "Folder path to create, e.g., 'Documents/Projects/NewFolder'"}
        },
        "required": ["path"]
    }
}

pc_open_app_tool = {
    "name": "pc_open_app",
    "description": "Open an application on the local PC. Available apps: notepad, calculator, paint, chrome, edge, firefox, vscode, word, excel, terminal, browser.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "app_name": {"type": "STRING", "description": "Name of the application, e.g., 'notepad', 'chrome', 'vscode'"},
            "args": {"type": "STRING", "description": "Optional arguments, e.g., URL for browser, file path for editor"}
        },
        "required": ["app_name"]
    }
}

pc_search_files_tool = {
    "name": "pc_search_files",
    "description": "Search for files on the local PC by name, extension, or content. Use when user wants to find files, locate documents, or search for specific file types.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "query": {"type": "STRING", "description": "Search query - filename pattern or substring to match (e.g., 'report', '*.pdf', 'invoice*')"},
            "search_path": {"type": "STRING", "description": "Directory to search in (e.g., 'Documents', 'Desktop'). Defaults to all allowed directories."},
            "file_extension": {"type": "STRING", "description": "File extension filter without dot (e.g., 'pdf', 'docx', 'txt')"},
            "max_results": {"type": "INTEGER", "description": "Maximum results to return (default: 50)"},
            "search_content": {"type": "BOOLEAN", "description": "If true, also search within file contents (slower, only for text files)"}
        },
        "required": ["query"]
    }
}

# Local PC tools list
local_pc_tools = [
    pc_create_file_tool,
    pc_read_file_tool,
    pc_write_file_tool,
    pc_list_folder_tool,
    pc_create_folder_tool,
    pc_open_app_tool,
    pc_search_files_tool,
]

# ==================== WEBHOOK TOOLS ====================

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
webhook_tools = [
    webhook_send_tool,
    webhook_send_saved_tool,
    webhook_list_tool,
]

# ==================== WHATSAPP TOOLS ====================

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
whatsapp_tools = [
    wa_send_message_tool,
    wa_check_status_tool,
]

# ==================== DOCUMENT PRINTER TOOLS ====================

doc_list_printers_tool = {
    "name": "doc_list_printers",
    "description": "List all available printers installed on the PC or network.",
    "parameters": {
        "type": "OBJECT",
        "properties": {},
        "required": []
    }
}

doc_print_file_tool = {
    "name": "doc_print_file",
    "description": "Print a document file (PDF, Word, Excel, Image, Text) to a printer.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "file_path": {"type": "STRING", "description": "Path to the file to print"},
            "printer_name": {"type": "STRING", "description": "Name of printer (optional, uses default)"},
            "copies": {"type": "INTEGER", "description": "Number of copies (default: 1)"}
        },
        "required": ["file_path"]
    }
}

doc_print_text_tool = {
    "name": "doc_print_text",
    "description": "Print text content directly to a printer.",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "text": {"type": "STRING", "description": "Text content to print"},
            "printer_name": {"type": "STRING", "description": "Name of printer (optional)"}
        },
        "required": ["text"]
    }
}

doc_printer_status_tool = {
    "name": "doc_printer_status",
    "description": "Get status of a printer (ready, busy, error, etc).",
    "parameters": {
        "type": "OBJECT",
        "properties": {
            "printer_name": {"type": "STRING", "description": "Name of printer (optional)"}
        },
        "required": []
    }
}

# Document printer tools list
document_printer_tools = [
    doc_list_printers_tool,
    doc_print_file_tool,
    doc_print_text_tool,
    doc_printer_status_tool,
]

# ==================== YAHOO MAIL TOOLS ====================

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
yahoo_mail_tools = [
    yahoo_send_email_tool,
    yahoo_list_emails_tool,
]

tools = [{'google_search': {}}, {"function_declarations": [run_web_agent, create_project_tool, switch_project_tool, list_projects_tool, list_smart_devices_tool, control_light_tool] + google_workspace_tools + n8n_mcp_tools + local_pc_tools + webhook_tools + whatsapp_tools + document_printer_tools + yahoo_mail_tools + tools_list[0]['function_declarations'][1:]}]


# --- CONFIG UPDATE: Enabled Transcription ---
config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    # We switch these from [] to {} to enable them with default settings
    output_audio_transcription={}, 
    input_audio_transcription={},
    system_instruction="Your name is Aspa, which stands for Advanced Smart Personal Assistant. "
        "You have a witty and charming personality. "
        "Your creator is Naz, and you address him as 'Sir'. "
        "When answering, respond using complete and concise sentences to keep a quick pacing and keep the conversation flowing. "
        "You have a fun personality.",
    tools=tools,
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                voice_name="Kore"
            )
        )
    )
)

pya = pyaudio.PyAudio()


from web_agent import WebAgent
from kasa_agent import KasaAgent

from google_workspace_agent import get_workspace_agent
from n8n_mcp_agent import get_n8n_agent
from local_pc_agent import get_local_pc_agent
from webhook_agent import get_webhook_agent
from whatsapp_agent import get_whatsapp_agent
from document_printer_agent import get_document_printer_agent
from yahoo_mail_agent import get_yahoo_agent

class AudioLoop:
    def __init__(self, video_mode=DEFAULT_MODE, on_audio_data=None, on_video_frame=None, on_cad_data=None, on_web_data=None, on_transcription=None, on_tool_confirmation=None, on_cad_status=None, on_cad_thought=None, on_project_update=None, on_device_update=None, on_error=None, input_device_index=None, input_device_name=None, output_device_index=None, kasa_agent=None):
        self.video_mode = video_mode
        self.on_audio_data = on_audio_data
        self.on_video_frame = on_video_frame
        self.on_cad_data = on_cad_data
        self.on_web_data = on_web_data
        self.on_transcription = on_transcription
        self.on_tool_confirmation = on_tool_confirmation 
        self.on_cad_status = on_cad_status
        self.on_cad_thought = on_cad_thought
        self.on_project_update = on_project_update
        self.on_device_update = on_device_update
        self.on_error = on_error
        self.input_device_index = input_device_index
        self.input_device_name = input_device_name
        self.output_device_index = output_device_index

        self.audio_in_queue = None
        self.out_queue = None
        self.paused = False

        self.chat_buffer = {"sender": None, "text": ""} # For aggregating chunks
        
        # Track last transcription text to calculate deltas (Gemini sends cumulative text)
        self._last_input_transcription = ""
        self._last_output_transcription = ""

        self.audio_in_queue = None
        self.out_queue = None
        self.paused = False

        self.session = None
        
        # Create CadAgent with thought callback
        self.web_agent = WebAgent()
        self.kasa_agent = kasa_agent if kasa_agent else KasaAgent()
        self.google_workspace_agent = get_workspace_agent()
        self.n8n_mcp_agent = get_n8n_agent()
        print("[SERVER] Startup: Initializing Yahoo Mail Agent...")
        self.yahoo_mail_agent = get_yahoo_agent()
        self.local_pc_agent = get_local_pc_agent()
        self.webhook_agent = get_webhook_agent()
        self.whatsapp_agent = get_whatsapp_agent()
        self.document_printer_agent = get_document_printer_agent()
        self.document_printer_agent = get_document_printer_agent()

        self.send_text_task = None
        self.stop_event = asyncio.Event()
        
        self.stop_event = asyncio.Event()
        
        self.permissions = {} # Default Empty (Will treat unset as True)
        self._pending_confirmations = {}

        # Video buffering state
        self._latest_image_payload = None
        # VAD State
        self._is_speaking = False
        self._silence_start_time = None
        
        # Initialize ProjectManager
        from project_manager import ProjectManager
        # Assuming we are running from backend/ or root? 
        # Using abspath of current file to find root
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # If ada.py is in backend/, project root is one up
        project_root = os.path.dirname(current_dir)
        self.project_manager = ProjectManager(project_root)
        
        # Sync Initial Project State
        if self.on_project_update:
            # We need to defer this slightly or just call it. 
            # Since this is init, loop might not be running, but on_project_update in server.py uses asyncio.create_task which needs a loop.
            # We will handle this by calling it in run() or just print for now.
            pass

    def flush_chat(self):
        """Forces the current chat buffer to be written to log."""
        if self.chat_buffer["sender"] and self.chat_buffer["text"].strip():
            self.project_manager.log_chat(self.chat_buffer["sender"], self.chat_buffer["text"])
            self.chat_buffer = {"sender": None, "text": ""}
        # Reset transcription tracking for new turn
        self._last_input_transcription = ""
        self._last_output_transcription = ""

    def update_permissions(self, new_perms):
        print(f"[ADA DEBUG] [CONFIG] Updating tool permissions: {new_perms}")
        self.permissions.update(new_perms)

    def set_paused(self, paused):
        self.paused = paused

    def stop(self):
        self.stop_event.set()
        
    def resolve_tool_confirmation(self, request_id, confirmed):
        print(f"[ADA DEBUG] [RESOLVE] resolve_tool_confirmation called. ID: {request_id}, Confirmed: {confirmed}")
        if request_id in self._pending_confirmations:
            future = self._pending_confirmations[request_id]
            if not future.done():
                print(f"[ADA DEBUG] [RESOLVE] Future found and pending. Setting result to: {confirmed}")
                future.set_result(confirmed)
            else:
                 print(f"[ADA DEBUG] [WARN] Request {request_id} future already done. Result: {future.result()}")
        else:
            print(f"[ADA DEBUG] [WARN] Confirmation Request {request_id} not found in pending dict. Keys: {list(self._pending_confirmations.keys())}")

    def clear_audio_queue(self):
        """Clears the queue of pending audio chunks to stop playback immediately."""
        try:
            count = 0
            while not self.audio_in_queue.empty():
                self.audio_in_queue.get_nowait()
                count += 1
            if count > 0:
                print(f"[ADA DEBUG] [AUDIO] Cleared {count} chunks from playback queue due to interruption.")
        except Exception as e:
            print(f"[ADA DEBUG] [ERR] Failed to clear audio queue: {e}")

    async def send_frame(self, frame_data):
        # Update the latest frame payload
        if isinstance(frame_data, bytes):
            b64_data = base64.b64encode(frame_data).decode('utf-8')
        else:
            b64_data = frame_data 

        # Store as the designated "next frame to send"
        self._latest_image_payload = {"mime_type": "image/jpeg", "data": b64_data}
        # No event signal needed - listen_audio pulls it

    async def send_realtime(self):
        while True:
            msg = await self.out_queue.get()
            await self.session.send(input=msg, end_of_turn=False)

    async def listen_audio(self):
        mic_info = pya.get_default_input_device_info()

        # Resolve Input Device by Name if provided
        resolved_input_device_index = None
        
        if self.input_device_name:
            print(f"[ADA] Attempting to find input device matching: '{self.input_device_name}'")
            count = pya.get_device_count()
            best_match = None
            
            for i in range(count):
                try:
                    info = pya.get_device_info_by_index(i)
                    if info['maxInputChannels'] > 0:
                        name = info.get('name', '')
                        # Simple case-insensitive check
                        if self.input_device_name.lower() in name.lower() or name.lower() in self.input_device_name.lower():
                             print(f"   Candidate {i}: {name}")
                             # Prioritize exact match or very close match if possible, but first match is okay for now
                             resolved_input_device_index = i
                             best_match = name
                             break
                except Exception:
                    continue
            
            if resolved_input_device_index is not None:
                print(f"[ADA] Resolved input device '{self.input_device_name}' to index {resolved_input_device_index} ({best_match})")
            else:
                print(f"[ADA] Could not find device matching '{self.input_device_name}'. Checking index...")

        # Fallback to index if Name lookup failed or wasn't provided
        if resolved_input_device_index is None and self.input_device_index is not None:
             try:
                 resolved_input_device_index = int(self.input_device_index)
                 print(f"[ADA] Requesting Input Device Index: {resolved_input_device_index}")
             except ValueError:
                 print(f"[ADA] Invalid device index '{self.input_device_index}', reverting to default.")
                 resolved_input_device_index = None

        if resolved_input_device_index is None:
             print("[ADA] Using Default Input Device")

        try:
            self.audio_stream = await asyncio.to_thread(
                pya.open,
                format=FORMAT,
                channels=CHANNELS,
                rate=SEND_SAMPLE_RATE,
                input=True,
                input_device_index=resolved_input_device_index if resolved_input_device_index is not None else mic_info["index"],
                frames_per_buffer=CHUNK_SIZE,
            )
        except OSError as e:
            print(f"[ADA] [ERR] Failed to open audio input stream: {e}")
            print("[ADA] [WARN] Audio features will be disabled. Please check microphone permissions.")
            return

        if __debug__:
            kwargs = {"exception_on_overflow": False}
        else:
            kwargs = {}
        
        # VAD Constants
        VAD_THRESHOLD = 800 # Adj based on mic sensitivity (800 is conservative for 16-bit)
        SILENCE_DURATION = 0.5 # Seconds of silence to consider "done speaking"
        
        while True:
            if self.paused:
                await asyncio.sleep(0.1)
                continue

            try:
                data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
                
                # 1. Send Audio
                if self.out_queue:
                    await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
                
                # 2. VAD Logic for Video
                # rms = audioop.rms(data, 2)
                # Replacement for audioop.rms(data, 2)
                count = len(data) // 2
                if count > 0:
                    shorts = struct.unpack(f"<{count}h", data)
                    sum_squares = sum(s**2 for s in shorts)
                    rms = int(math.sqrt(sum_squares / count))
                else:
                    rms = 0
                
                if rms > VAD_THRESHOLD:
                    # Speech Detected
                    self._silence_start_time = None
                    
                    if not self._is_speaking:
                        # NEW Speech Utterance Started
                        self._is_speaking = True
                        print(f"[ADA DEBUG] [VAD] Speech Detected (RMS: {rms}). Sending Video Frame.")
                        
                        # Send ONE frame
                        if self._latest_image_payload and self.out_queue:
                            await self.out_queue.put(self._latest_image_payload)
                        else:
                            print(f"[ADA DEBUG] [VAD] No video frame available to send.")
                            
                else:
                    # Silence
                    if self._is_speaking:
                        if self._silence_start_time is None:
                            self._silence_start_time = time.time()
                        
                        elif time.time() - self._silence_start_time > SILENCE_DURATION:
                            # Silence confirmed, reset state
                            print(f"[ADA DEBUG] [VAD] Silence detected. Resetting speech state.")
                            self._is_speaking = False
                            self._silence_start_time = None

            except Exception as e:
                print(f"Error reading audio: {e}")
                await asyncio.sleep(0.1)





    async def handle_write_file(self, path, content):
        print(f"[ADA DEBUG] [FS] Writing file: '{path}'")
        
        # Auto-create project if stuck in temp
        if self.project_manager.current_project == "temp":
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            new_project_name = f"Project_{timestamp}"
            print(f"[ADA DEBUG] [FS] Auto-creating project: {new_project_name}")
            
            success, msg = self.project_manager.create_project(new_project_name)
            if success:
                self.project_manager.switch_project(new_project_name)
                # Notify User
                try:
                    await self.session.send(input=f"System Notification: Automatic Project Creation. Switched to new project '{new_project_name}'.", end_of_turn=False)
                    if self.on_project_update:
                         self.on_project_update(new_project_name)
                except Exception as e:
                    print(f"[ADA DEBUG] [ERR] Failed to notify auto-project: {e}")
        
        # Force path to be relative to current project
        # If absolute path is provided, we try to strip it or just ignore it and use basename
        filename = os.path.basename(path)
        
        # If path contained subdirectories (e.g. "backend/server.py"), preserving that structure might be desired IF it's within the project.
        # But for safety, and per user request to "always create the file in the project", 
        # we will root it in the current project path.
        
        current_project_path = self.project_manager.get_current_project_path()
        final_path = current_project_path / filename # Simple flat structure for now, or allow relative?
        
        # If the user specifically wanted a subfolder, they might have provided "sub/file.txt".
        # Let's support relative paths if they don't start with /
        if not os.path.isabs(path):
             final_path = current_project_path / path
        
        print(f"[ADA DEBUG] [FS] Resolved path: '{final_path}'")

        try:
            # Ensure parent exists
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            with open(final_path, 'w', encoding='utf-8') as f:
                f.write(content)
            result = f"File '{final_path.name}' written successfully to project '{self.project_manager.current_project}'."
        except Exception as e:
            result = f"Failed to write file '{path}': {str(e)}"

        print(f"[ADA DEBUG] [FS] Result: {result}")
        try:
             await self.session.send(input=f"System Notification: {result}", end_of_turn=True)
        except Exception as e:
             print(f"[ADA DEBUG] [ERR] Failed to send fs result: {e}")

    async def handle_read_directory(self, path):
        print(f"[ADA DEBUG] [FS] Reading directory: '{path}'")
        try:
            if not os.path.exists(path):
                result = f"Directory '{path}' does not exist."
            else:
                items = os.listdir(path)
                result = f"Contents of '{path}': {', '.join(items)}"
        except Exception as e:
            result = f"Failed to read directory '{path}': {str(e)}"

        print(f"[ADA DEBUG] [FS] Result: {result}")
        try:
             await self.session.send(input=f"System Notification: {result}", end_of_turn=True)
        except Exception as e:
             print(f"[ADA DEBUG] [ERR] Failed to send fs result: {e}")

    async def handle_read_file(self, path):
        print(f"[ADA DEBUG] [FS] Reading file: '{path}'")
        try:
            if not os.path.exists(path):
                result = f"File '{path}' does not exist."
            else:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                result = f"Content of '{path}':\n{content}"
        except Exception as e:
            result = f"Failed to read file '{path}': {str(e)}"

        print(f"[ADA DEBUG] [FS] Result: {result}")
        try:
             await self.session.send(input=f"System Notification: {result}", end_of_turn=True)
        except Exception as e:
             print(f"[ADA DEBUG] [ERR] Failed to send fs result: {e}")

    async def handle_web_agent_request(self, prompt):
        print(f"[ADA DEBUG] [WEB] Web Agent Task: '{prompt}'")
        
        async def update_frontend(image_b64, log_text):
            if self.on_web_data:
                 self.on_web_data({"image": image_b64, "log": log_text})
                 
        # Run the web agent and wait for it to return
        result = await self.web_agent.run_task(prompt, update_callback=update_frontend)
        print(f"[ADA DEBUG] [WEB] Web Agent Task Returned: {result}")
        
        # Send the final result back to the main model
        try:
             await self.session.send(input=f"System Notification: Web Agent has finished.\nResult: {result}", end_of_turn=True)
        except Exception as e:
             print(f"[ADA DEBUG] [ERR] Failed to send web agent result to model: {e}")

    # ==================== GOOGLE WORKSPACE HANDLERS ====================

    async def handle_google_authenticate(self):
        """Handle Google Workspace authentication."""
        print(f"[ADA DEBUG] [GOOGLE] Starting authentication...")
        result = await self.google_workspace_agent.authenticate()
        
        if result.get("success"):
            message = "Successfully authenticated with Google Workspace! You can now use Calendar, Sheets, Drive, Gmail, and Docs."
        else:
            message = f"Google authentication failed: {result.get('error', 'Unknown error')}"
        
        print(f"[ADA DEBUG] [GOOGLE] Auth result: {message}")
        try:
            await self.session.send(input=f"System Notification: {message}", end_of_turn=True)
        except Exception as e:
            print(f"[ADA DEBUG] [ERR] Failed to send auth result: {e}")
        
        return result

    async def handle_google_list_events(self, max_results=10, time_min=None, time_max=None):
        """Handle listing calendar events."""
        print(f"[ADA DEBUG] [GOOGLE] Listing calendar events...")
        result = await self.google_workspace_agent.list_calendar_events(
            max_results=max_results,
            time_min=time_min,
            time_max=time_max
        )
        
        if result.get("success"):
            events = result.get("events", [])
            if events:
                event_list = "\n".join([
                    f"- {e['summary']} at {e['start']}" for e in events
                ])
                message = f"Found {len(events)} upcoming events:\n{event_list}"
            else:
                message = "No upcoming events found."
        else:
            message = f"Failed to list events: {result.get('error', 'Unknown error')}"
        
        print(f"[ADA DEBUG] [GOOGLE] List events result: {message[:100]}...")
        return {"result": message}

    async def handle_google_create_event(self, summary, start_time, end_time=None, description="", location="", attendees=None):
        """Handle creating a calendar event."""
        print(f"[ADA DEBUG] [GOOGLE] Creating event: {summary}")
        
        attendees_list = None
        if attendees:
            attendees_list = [a.strip() for a in attendees.split(",")]
        
        result = await self.google_workspace_agent.create_calendar_event(
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            attendees=attendees_list
        )
        
        if result.get("success"):
            message = f"Event '{summary}' created successfully! Link: {result.get('link', 'N/A')}"
        else:
            message = f"Failed to create event: {result.get('error', 'Unknown error')}"
        
        print(f"[ADA DEBUG] [GOOGLE] Create event result: {message}")
        return {"result": message}

    async def handle_google_delete_event(self, event_id):
        """Handle deleting a calendar event."""
        print(f"[ADA DEBUG] [GOOGLE] Deleting event: {event_id}")
        result = await self.google_workspace_agent.delete_calendar_event(event_id=event_id)
        
        if result.get("success"):
            message = f"Event deleted successfully."
        else:
            message = f"Failed to delete event: {result.get('error', 'Unknown error')}"
        
        return {"result": message}

    async def handle_google_read_spreadsheet(self, spreadsheet_id, range_name="Sheet1!A1:Z100"):
        """Handle reading from a spreadsheet."""
        print(f"[ADA DEBUG] [GOOGLE] Reading spreadsheet: {spreadsheet_id}")
        result = await self.google_workspace_agent.read_spreadsheet(
            spreadsheet_id=spreadsheet_id,
            range_name=range_name
        )
        
        if result.get("success"):
            data = result.get("data", [])
            rows = len(data)
            # Format as simple table for display
            if data:
                formatted = "\n".join([" | ".join(str(cell) for cell in row) for row in data[:20]])
                message = f"Read {rows} rows from spreadsheet:\n{formatted}"
                if rows > 20:
                    message += f"\n... and {rows - 20} more rows"
            else:
                message = "Spreadsheet is empty or range contains no data."
        else:
            message = f"Failed to read spreadsheet: {result.get('error', 'Unknown error')}"
        
        return {"result": message, "data": result.get("data", [])}

    async def handle_google_write_spreadsheet(self, spreadsheet_id, range_name, values):
        """Handle writing to a spreadsheet."""
        print(f"[ADA DEBUG] [GOOGLE] Writing to spreadsheet: {spreadsheet_id}")
        
        import json
        try:
            values_list = json.loads(values)
        except:
            values_list = [[values]]  # Wrap single value
        
        result = await self.google_workspace_agent.write_spreadsheet(
            spreadsheet_id=spreadsheet_id,
            range_name=range_name,
            values=values_list
        )
        
        if result.get("success"):
            message = f"Successfully updated {result.get('updated_cells', 'N/A')} cells."
        else:
            message = f"Failed to write to spreadsheet: {result.get('error', 'Unknown error')}"
        
        return {"result": message}

    async def handle_google_append_spreadsheet(self, spreadsheet_id, range_name, values):
        """Handle appending to a spreadsheet."""
        print(f"[ADA DEBUG] [GOOGLE] Appending to spreadsheet: {spreadsheet_id}")
        
        import json
        try:
            values_list = json.loads(values)
        except:
            values_list = [[values]]
        
        result = await self.google_workspace_agent.append_spreadsheet(
            spreadsheet_id=spreadsheet_id,
            range_name=range_name,
            values=values_list
        )
        
        if result.get("success"):
            message = "Data appended successfully to spreadsheet."
        else:
            message = f"Failed to append to spreadsheet: {result.get('error', 'Unknown error')}"
        
        return {"result": message}

    async def handle_google_create_spreadsheet(self, title, sheets=None):
        """Handle creating a new spreadsheet."""
        print(f"[ADA DEBUG] [GOOGLE] Creating spreadsheet: {title}")
        
        sheets_list = None
        if sheets:
            sheets_list = [s.strip() for s in sheets.split(",")]
        
        result = await self.google_workspace_agent.create_spreadsheet(
            title=title,
            sheets=sheets_list
        )
        
        if result.get("success"):
            message = f"Spreadsheet '{title}' created! URL: {result.get('url', 'N/A')}"
        else:
            message = f"Failed to create spreadsheet: {result.get('error', 'Unknown error')}"
        
        return {"result": message, "spreadsheet_id": result.get("spreadsheet_id")}

    async def handle_google_add_sheet(self, spreadsheet_id, title):
        """Handle adding a sheet."""
        print(f"[ADA DEBUG] [GOOGLE] Adding sheet: {title}")
        result = await self.google_workspace_agent.add_sheet(
            spreadsheet_id=spreadsheet_id,
            title=title
        )
        
        if result.get("success"):
            message = f"Sheet '{title}' added successfully! ID: {result.get('sheet_id')}"
        else:
            message = f"Failed to add sheet: {result.get('error', 'Unknown error')}"
            
        return {"result": message}

    async def handle_google_delete_sheet(self, spreadsheet_id, sheet_title):
        """Handle deleting a sheet."""
        print(f"[ADA DEBUG] [GOOGLE] Deleting sheet: {sheet_title}")
        result = await self.google_workspace_agent.delete_sheet(
            spreadsheet_id=spreadsheet_id,
            sheet_title=sheet_title
        )
        
        if result.get("success"):
            message = f"Sheet '{sheet_title}' deleted successfully."
        else:
            message = f"Failed to delete sheet: {result.get('error', 'Unknown error')}"
            
        return {"result": message}

    async def handle_google_list_drive_files(self, query=None, max_results=20, folder_id=None):
        """Handle listing Drive files."""
        print(f"[ADA DEBUG] [GOOGLE] Listing Drive files...")
        result = await self.google_workspace_agent.list_drive_files(
            query=query,
            max_results=max_results,
            folder_id=folder_id
        )
        
        if result.get("success"):
            files = result.get("files", [])
            if files:
                file_list = "\n".join([
                    f"- {f['name']} ({f.get('mimeType', 'unknown')})" for f in files
                ])
                message = f"Found {len(files)} files:\n{file_list}"
            else:
                message = "No files found in Drive."
        else:
            message = f"Failed to list files: {result.get('error', 'Unknown error')}"
        
        return {"result": message, "files": result.get("files", [])}

    async def handle_google_upload_to_drive(self, file_path, folder_id=None, file_name=None):
        """Handle uploading file to Drive."""
        print(f"[ADA DEBUG] [GOOGLE] Uploading to Drive: {file_path}")
        result = await self.google_workspace_agent.upload_to_drive(
            file_path=file_path,
            folder_id=folder_id,
            file_name=file_name
        )
        
        if result.get("success"):
            message = f"File uploaded successfully! Link: {result.get('link', 'N/A')}"
        else:
            message = f"Failed to upload file: {result.get('error', 'Unknown error')}"
        
        return {"result": message}

    async def handle_google_download_from_drive(self, file_id, destination_path):
        """Handle downloading file from Drive."""
        print(f"[ADA DEBUG] [GOOGLE] Downloading from Drive: {file_id}")
        result = await self.google_workspace_agent.download_from_drive(
            file_id=file_id,
            destination_path=destination_path
        )
        
        if result.get("success"):
            message = f"File downloaded to: {destination_path}"
        else:
            message = f"Failed to download file: {result.get('error', 'Unknown error')}"
        
        return {"result": message}

    async def handle_google_create_drive_folder(self, folder_name, parent_id=None):
        """Handle creating a Drive folder."""
        print(f"[ADA DEBUG] [GOOGLE] Creating Drive folder: {folder_name}")
        result = await self.google_workspace_agent.create_drive_folder(
            folder_name=folder_name,
            parent_id=parent_id
        )
        
        if result.get("success"):
            message = f"Folder '{folder_name}' created! Link: {result.get('link', 'N/A')}"
        else:
            message = f"Failed to create folder: {result.get('error', 'Unknown error')}"
        
        return {"result": message, "folder_id": result.get("folder_id")}

    async def handle_google_send_email(self, to, subject, body, cc=None, bcc=None):
        """Handle sending an email."""
        print(f"[ADA DEBUG] [GOOGLE] Sending email to: {to}")
        result = await self.google_workspace_agent.send_email(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc
        )
        
        if result.get("success"):
            message = f"Email sent successfully to {to}!"
        else:
            message = f"Failed to send email: {result.get('error', 'Unknown error')}"
        
        return {"result": message}

    async def handle_google_list_emails(self, max_results=10, query=None):
        """Handle listing emails."""
        print(f"[ADA DEBUG] [GOOGLE] Listing emails...")
        result = await self.google_workspace_agent.list_emails(
            max_results=max_results,
            query=query
        )
        
        if result.get("success"):
            emails = result.get("emails", [])
            if emails:
                email_list = "\n".join([
                    f"- From: {e['from'][:30]}... Subject: {e['subject'][:40]}..." for e in emails
                ])
                message = f"Found {len(emails)} emails:\n{email_list}"
            else:
                message = "No emails found."
        else:
            message = f"Failed to list emails: {result.get('error', 'Unknown error')}"
        
        return {"result": message, "emails": result.get("emails", [])}

    async def handle_google_read_email(self, message_id):
        """Handle reading a specific email."""
        print(f"[ADA DEBUG] [GOOGLE] Reading email: {message_id}")
        result = await self.google_workspace_agent.read_email(message_id=message_id)
        
        if result.get("success"):
            message = f"From: {result.get('from')}\nSubject: {result.get('subject')}\nDate: {result.get('date')}\n\n{result.get('body', result.get('snippet', ''))}"
        else:
            message = f"Failed to read email: {result.get('error', 'Unknown error')}"
        
        return {"result": message}

    async def handle_google_create_document(self, title, content=None):
        """Handle creating a Google Document."""
        print(f"[ADA DEBUG] [GOOGLE] Creating document: {title}")
        result = await self.google_workspace_agent.create_document(
            title=title,
            content=content
        )
        
        if result.get("success"):
            message = f"Document '{title}' created! URL: {result.get('url', 'N/A')}"
        else:
            message = f"Failed to create document: {result.get('error', 'Unknown error')}"
        
        return {"result": message, "document_id": result.get("document_id")}

    async def handle_google_read_document(self, document_id):
        """Handle reading a Google Document."""
        print(f"[ADA DEBUG] [GOOGLE] Reading document: {document_id}")
        result = await self.google_workspace_agent.read_document(document_id=document_id)
        
        if result.get("success"):
            content = result.get("content", "")
            if len(content) > 2000:
                content = content[:2000] + "... (truncated)"
            message = f"Document: {result.get('title')}\n\n{content}"
        else:
            message = f"Failed to read document: {result.get('error', 'Unknown error')}"
        
        return {"result": message}

    async def handle_google_append_document(self, document_id, content):
        """Handle appending to a Google Document."""
        print(f"[ADA DEBUG] [GOOGLE] Appending to document: {document_id}")
        result = await self.google_workspace_agent.append_to_document(
            document_id=document_id,
            content=content
        )
        
        if result.get("success"):
            message = f"Content appended successfully! URL: {result.get('url', 'N/A')}"
        else:
            message = f"Failed to append to document: {result.get('error', 'Unknown error')}"
        
        return {"result": message}

    # ==================== N8N MCP HANDLERS ====================

    async def handle_n8n_connect(self):
        """Handle connecting to n8n MCP Server."""
        print(f"[ADA DEBUG] [N8N] Connecting to n8n MCP Server...")
        result = await self.n8n_mcp_agent.connect()
        
        if result.get("success"):
            message = f"Connected to n8n MCP Server! Server: {result.get('server_name', 'n8n')}"
        else:
            message = f"Failed to connect to n8n: {result.get('error', 'Unknown error')}"
        
        print(f"[ADA DEBUG] [N8N] Connect result: {message}")
        return {"result": message}

    async def handle_n8n_list_workflows(self):
        """Handle listing available n8n workflows."""
        print(f"[ADA DEBUG] [N8N] Listing workflows...")
        result = await self.n8n_mcp_agent.list_workflows()
        
        if result.get("success"):
            workflows = result.get("workflows", [])
            # Extract actual workflow data from nested structure
            workflow_names = []  # List of (name, id) tuples
            for w in workflows:
                if isinstance(w, dict):
                    # Handle nested data structure: {data: [{id, name, ...}]}
                    if "data" in w:
                        for item in w.get("data", []):
                            if isinstance(item, dict) and "name" in item:
                                workflow_names.append((item.get("name", "Unknown"), item.get("id", "N/A")))
                    elif "name" in w:
                        workflow_names.append((w.get("name", "Unknown"), w.get("id", "N/A")))
            
            if workflow_names:
                workflow_list = "\n".join([f"- {name} (ID: {wid})" for name, wid in workflow_names[:10]])
                message = f"Found {len(workflow_names)} workflows:\n{workflow_list}"
                if len(workflow_names) > 10:
                    message += f"\n...and {len(workflow_names) - 10} more"
            else:
                message = "No workflows found. Make sure workflows are exposed to MCP in n8n settings."
        else:
            message = f"Failed to list workflows: {result.get('error', 'Unknown error')}"
        
        return {"result": message, "workflows": result.get("workflows", [])}

    async def handle_n8n_search_workflows(self, query):
        """Handle searching n8n workflows."""
        print(f"[ADA DEBUG] [N8N] Searching workflows: {query}")
        result = await self.n8n_mcp_agent.search_workflows(query)
        
        if result.get("success"):
            workflows = result.get("workflows", [])
            # Extract actual workflow data from nested structure
            workflow_names = []  # List of (name, id) tuples
            for w in workflows:
                if isinstance(w, dict):
                    # Handle nested data structure: {data: [{id, name, ...}]}
                    if "data" in w:
                        for item in w.get("data", []):
                            if isinstance(item, dict) and "name" in item:
                                workflow_names.append((item.get("name", "Unknown"), item.get("id", "N/A")))
                    elif "name" in w:
                        workflow_names.append((w.get("name", "Unknown"), w.get("id", "N/A")))
            
            if workflow_names:
                workflow_list = "\n".join([f"- {name} (ID: {wid})" for name, wid in workflow_names])
                message = f"Found {len(workflow_names)} matching workflows:\n{workflow_list}\n\nTo execute, use the workflow ID."
            else:
                message = f"No workflows found matching '{query}'."
        else:
            message = f"Search failed: {result.get('error', 'Unknown error')}"
        
        return {"result": message, "workflows": result.get("workflows", [])}

    async def handle_n8n_execute_workflow(self, workflow_name, input_data=None):
        """Handle executing an n8n workflow. workflow_name can be the workflow ID."""
        print(f"[ADA DEBUG] [N8N] Executing workflow: {workflow_name}")
        
        # Parse input_data if it's a JSON string
        parsed_data = {}
        if input_data:
            import json
            try:
                parsed_data = json.loads(input_data)
            except:
                parsed_data = {"input": input_data}
        
        # workflow_name is actually the workflow ID
        result = await self.n8n_mcp_agent.execute_workflow(workflow_name, parsed_data)
        
        if result.get("success"):
            exec_result = result.get("result", {})
            if isinstance(exec_result, dict):
                exec_id = exec_result.get("executionId", "N/A")
                if exec_result.get("success", True):
                    message = f"Workflow executed successfully! Execution ID: {exec_id}"
                else:
                    error_msg = exec_result.get("result", {}).get("error", {}).get("message", "Unknown error")
                    message = f"Workflow execution completed with warning. Execution ID: {exec_id}\nDetails: {str(error_msg)[:200]}"
            else:
                message = f"Workflow executed successfully! Result: {exec_result}"
        else:
            message = f"Workflow execution failed: {result.get('error', 'Unknown error')}"
        
        return {"result": message}

    async def handle_n8n_get_workflow_info(self, workflow_name):
        """Handle getting workflow details."""
        print(f"[ADA DEBUG] [N8N] Getting info for workflow: {workflow_name}")
        result = await self.n8n_mcp_agent.get_workflow_info(workflow_name)
        
        if result.get("success"):
            workflow = result.get("workflow", {})
            # Handle both string and dict responses
            if isinstance(workflow, str):
                message = f"Workflow Info: {workflow}"
            elif isinstance(workflow, dict):
                message = f"Workflow: {workflow.get('name', 'Unknown')}\n"
                message += f"Description: {workflow.get('description', 'No description')}\n"
                if workflow.get("input_schema"):
                    message += f"Input Schema: {workflow.get('input_schema')}"
            else:
                message = f"Workflow Info: {str(workflow)}"
        else:
            message = f"Failed to get workflow info: {result.get('error', 'Unknown error')}"
        
        return {"result": message, "workflow": result.get("workflow", {})}

    # ==================== LOCAL PC HANDLERS ====================

    async def handle_pc_create_file(self, path, content=""):
        """Handle creating a file on local PC."""
        print(f"[ADA DEBUG] [PC] Creating file: {path}")
        result = await self.local_pc_agent.create_file(path, content)
        
        if result.get("success"):
            message = f"File created successfully at: {result.get('path')}"
        else:
            message = f"Failed to create file: {result.get('error', 'Unknown error')}"
        
        return {"result": message}

    async def handle_pc_read_file(self, path):
        """Handle reading a file from local PC."""
        print(f"[ADA DEBUG] [PC] Reading file: {path}")
        result = await self.local_pc_agent.read_file(path)
        
        if result.get("success"):
            content = result.get("content", "")
            if len(content) > 1000:
                content = content[:1000] + "\n... (truncated, file is large)"
            message = f"File content:\n{content}"
        else:
            message = f"Failed to read file: {result.get('error', 'Unknown error')}"
        
        return {"result": message}

    async def handle_pc_write_file(self, path, content):
        """Handle writing to a file on local PC."""
        print(f"[ADA DEBUG] [PC] Writing to file: {path}")
        result = await self.local_pc_agent.write_file(path, content)
        
        if result.get("success"):
            message = f"File written successfully: {result.get('path')}"
        else:
            message = f"Failed to write file: {result.get('error', 'Unknown error')}"
        
        return {"result": message}

    async def handle_pc_list_folder(self, path="Documents"):
        """Handle listing folder contents on local PC."""
        print(f"[ADA DEBUG] [PC] Listing folder: {path}")
        result = await self.local_pc_agent.list_folder(path)
        
        if result.get("success"):
            items = result.get("items", [])
            if items:
                item_list = "\n".join([
                    f"📁 {item['name']}" if item['type'] == 'folder' else f"📄 {item['name']}"
                    for item in items[:20]
                ])
                message = f"Contents of {path}:\n{item_list}"
                if len(items) > 20:
                    message += f"\n... and {len(items) - 20} more items"
            else:
                message = f"Folder {path} is empty."
        else:
            message = f"Failed to list folder: {result.get('error', 'Unknown error')}"
        
        return {"result": message}

    async def handle_pc_create_folder(self, path):
        """Handle creating a folder on local PC."""
        print(f"[ADA DEBUG] [PC] Creating folder: {path}")
        result = await self.local_pc_agent.create_folder(path)
        
        if result.get("success"):
            message = f"Folder created successfully: {result.get('path')}"
        else:
            message = f"Failed to create folder: {result.get('error', 'Unknown error')}"
        
        return {"result": message}

    async def handle_pc_open_app(self, app_name, args=None):
        """Handle opening an application on local PC."""
        print(f"[ADA DEBUG] [PC] Opening app: {app_name}")
        result = await self.local_pc_agent.open_application(app_name, args)
        
        if result.get("success"):
            message = f"Application '{app_name}' opened successfully!"
        else:
            message = f"Failed to open application: {result.get('error', 'Unknown error')}"
        
        return {"result": message}

    async def handle_pc_search_files(self, query, search_path=None, 
                                      file_extension=None, max_results=50,
                                      search_content=False):
        """Handle searching for files on local PC."""
        print(f"[ADA DEBUG] [PC] Searching for files: {query}")
        result = await self.local_pc_agent.search_files(
            query, search_path, file_extension, max_results, search_content
        )
        
        if result.get("success"):
            files = result.get("results", [])
            total = result.get("total_found", 0)
            
            if total == 0:
                message = f"No files found matching '{query}'."
            else:
                # Format results for voice response
                file_list = []
                for f in files[:10]:  # Limit voice output to 10 files
                    name = f.get("name", "unknown")
                    size = f.get("size", "")
                    content_match = " (content match)" if f.get("content_match") else ""
                    file_list.append(f"📄 {name} ({size}){content_match}")
                
                message = f"Found {total} file(s) matching '{query}':\n" + "\n".join(file_list)
                if total > 10:
                    message += f"\n... and {total - 10} more files"
        else:
            message = f"Search failed: {result.get('error', 'Unknown error')}"
        
        return {"result": message}

    # ==================== WEBHOOK HANDLERS ====================

    async def handle_webhook_send(self, url, data, method="POST"):
        """Handle sending data to a webhook URL."""
        print(f"[ADA DEBUG] [WEBHOOK] Sending to: {url}")
        
        # Parse JSON data if string
        import json
        if isinstance(data, str):
            try:
                parsed_data = json.loads(data)
            except:
                parsed_data = {"message": data}
        else:
            parsed_data = data
        
        result = await self.webhook_agent.send_webhook(url, parsed_data, method)
        
        if result.get("success"):
            message = f"Webhook sent successfully! Status: {result.get('status_code', 'OK')}"
        else:
            message = f"Failed to send webhook: {result.get('error', 'Unknown error')}"
        
        return {"result": message}

    async def handle_webhook_send_saved(self, webhook_name, data):
        """Handle sending data to a saved webhook."""
        print(f"[ADA DEBUG] [WEBHOOK] Sending to saved webhook: {webhook_name}")
        
        # Parse JSON data if string
        import json
        if isinstance(data, str):
            try:
                parsed_data = json.loads(data)
            except:
                parsed_data = {"message": data}
        else:
            parsed_data = data
        
        result = await self.webhook_agent.send_to_saved_webhook(webhook_name, parsed_data)
        
        if result.get("success"):
            message = f"Webhook '{webhook_name}' sent successfully!"
        else:
            message = f"Failed to send webhook: {result.get('error', 'Unknown error')}"
        
        return {"result": message}

    async def handle_webhook_list(self):
        """Handle listing all webhooks."""
        print(f"[ADA DEBUG] [WEBHOOK] Listing webhooks")
        
        saved = self.webhook_agent.list_saved_webhooks()
        registered = self.webhook_agent.list_registered_webhooks()
        
        message = "Webhooks:\n"
        
        if saved.get("webhooks"):
            message += "\nSaved (for sending):\n"
            for w in saved["webhooks"]:
                message += f"  - {w['name']}\n"
        else:
            message += "\nNo saved webhooks. Set via .env: N8N_WEBHOOK_URL, DISCORD_WEBHOOK_URL, etc.\n"
        
        if registered.get("webhooks"):
            message += "\nReceiving endpoints:\n"
            for w in registered["webhooks"]:
                message += f"  - /webhook/{w['id']} ({w.get('source', 'unknown')})\n"
        
        return {"result": message}

    # ==================== WHATSAPP HANDLERS ====================

    async def handle_wa_send_message(self, phone, message):
        """Handle sending a WhatsApp message."""
        print(f"[ADA DEBUG] [WA] Sending message to: {phone}")
        result = await self.whatsapp_agent.send_message(phone, message)
        
        if result.get("success"):
            msg = f"Pesan WhatsApp berhasil dikirim ke {result.get('phone', phone)}!"
        else:
            msg = f"Gagal mengirim WhatsApp: {result.get('error', 'Unknown error')}"
        
        return {"result": msg}

    async def handle_wa_check_status(self):
        """Handle checking WhatsApp connection status."""
        print(f"[ADA DEBUG] [WA] Checking status")
        result = await self.whatsapp_agent.check_connection()
        
        if result.get("success"):
            status = result.get("status", "unknown")
            msg = f"WhatsApp status: {status}. Connection ID: {result.get('connection_id', 'default')}"
        else:
            msg = f"WhatsApp tidak terhubung: {result.get('error', 'Unknown error')}"
        
        return {"result": msg}

    # ==================== DOCUMENT PRINTER HANDLERS ====================

    async def handle_doc_list_printers(self):
        """Handle listing available printers."""
        print(f"[ADA DEBUG] [PRINTER] Listing printers")
        result = await self.document_printer_agent.list_printers()
        
        if result.get("success"):
            printers = result.get("printers", [])
            default = result.get("default", "Unknown")
            
            if printers:
                printer_list = "\n".join([f"  - {p['name']}" for p in printers[:10]])
                msg = f"Ditemukan {len(printers)} printer:\n{printer_list}\n\nDefault: {default}"
            else:
                msg = "Tidak ada printer yang ditemukan."
        else:
            msg = f"Gagal mendapatkan daftar printer: {result.get('error')}"
        
        return {"result": msg}

    async def handle_doc_print_file(self, file_path, printer_name=None, copies=1):
        """Handle printing a file."""
        print(f"[ADA DEBUG] [PRINTER] Printing file: {file_path}")
        result = await self.document_printer_agent.print_file(file_path, printer_name, copies)
        
        if result.get("success"):
            msg = f"File '{result.get('file')}' berhasil dikirim ke printer {result.get('printer')}!"
        else:
            msg = f"Gagal mencetak: {result.get('error')}"
        
        return {"result": msg}

    async def handle_doc_print_text(self, text, printer_name=None):
        """Handle printing text directly."""
        print(f"[ADA DEBUG] [PRINTER] Printing text")
        result = await self.document_printer_agent.print_text(text, printer_name)
        
        if result.get("success"):
            msg = f"Teks berhasil dikirim ke printer!"
        else:
            msg = f"Gagal mencetak teks: {result.get('error')}"
        
        return {"result": msg}

    async def handle_doc_printer_status(self, printer_name=None):
        """Handle getting printer status."""
        print(f"[ADA DEBUG] [PRINTER] Getting status")
        result = await self.document_printer_agent.get_printer_status(printer_name)
        
        if result.get("success"):
            msg = f"Printer: {result.get('printer')}\nStatus: {result.get('status')}"
            if result.get('jobs'):
                msg += f"\nAntrian: {result.get('jobs')} job"
        else:
            msg = f"Gagal mendapatkan status: {result.get('error')}"
        
        return {"result": msg}

    # ==================== GOOGLE FORMS HANDLERS ====================

    async def handle_google_create_form(self, title, document_title=None):
        """Handle creating a Google Form."""
        print(f"[ADA DEBUG] [GOOGLE] Creating form: {title}")
        result = await self.google_workspace_agent.create_form(title, document_title)
        
        if result.get("success"):
            msg = f"Form '{title}' berhasil dibuat!\nURL: {result.get('url')}\nEdit: {result.get('edit_url')}"
        else:
            msg = f"Gagal membuat form: {result.get('error')}"
        
        return {"result": msg}

    # ==================== GOOGLE SLIDES HANDLERS ====================

    async def handle_google_create_presentation(self, title):
        """Handle creating a Google Slides presentation."""
        print(f"[ADA DEBUG] [GOOGLE] Creating presentation: {title}")
        result = await self.google_workspace_agent.create_presentation(title)
        
        if result.get("success"):
            msg = f"Presentasi '{title}' berhasil dibuat!\nURL: {result.get('edit_url')}"
        else:
            msg = f"Gagal membuat presentasi: {result.get('error')}"
        
        return {"result": msg}

    # ==================== YAHOO MAIL HANDLERS ====================

    async def handle_yahoo_send_email(self, to, subject, body):
        """Handle sending email via Yahoo Mail."""
        print(f"[ADA DEBUG] [YAHOO] Sending email to: {to}")
        result = await asyncio.to_thread(
            self.yahoo_mail_agent.send_email, to, subject, body
        )
        
        if result.get("success"):
            msg = f"Email Yahoo berhasil dikirim ke {to}!"
        else:
            msg = f"Gagal mengirim email Yahoo: {result.get('error')}"
        
        return {"result": msg}

    async def handle_yahoo_list_emails(self, limit=5):
        """Handle listing Yahoo emails."""
        print(f"[ADA DEBUG] [YAHOO] Listing emails (limit={limit})")
        result = await asyncio.to_thread(
            self.yahoo_mail_agent.get_recent_emails, limit
        )
        
        if result.get("success"):
            emails = result.get("emails", [])
            if emails:
                email_list = []
                for e in emails[:5]:
                    email_list.append(f"- {e.get('subject')} (dari: {e.get('from')})")
                msg = f"Email terbaru di Yahoo ({len(emails)}):\n" + "\n".join(email_list)
            else:
                msg = "Tidak ada email di inbox Yahoo."
        else:
            msg = f"Gagal membaca email Yahoo: {result.get('error')}"
        
        return {"result": msg}


    async def receive_audio(self):
        "Background task to reads from the websocket and write pcm chunks to the output queue"
        try:
            while True:
                turn = self.session.receive()
                async for response in turn:
                    # 1. Handle Audio Data
                    if data := response.data:
                        self.audio_in_queue.put_nowait(data)
                        # NOTE: 'continue' removed here to allow processing transcription/tools in same packet

                    # 2. Handle Transcription (User & Model)
                    if response.server_content:
                        if response.server_content.input_transcription:
                            transcript = response.server_content.input_transcription.text
                            if transcript:
                                # Skip if this is an exact duplicate event
                                if transcript != self._last_input_transcription:
                                    # Calculate delta (Gemini may send cumulative or chunk-based text)
                                    delta = transcript
                                    if transcript.startswith(self._last_input_transcription):
                                        delta = transcript[len(self._last_input_transcription):]
                                    self._last_input_transcription = transcript
                                    
                                    # Only send if there's new text
                                    if delta:
                                        # User is speaking, so interrupt model playback!
                                        self.clear_audio_queue()

                                        # Send to frontend (Streaming)
                                        if self.on_transcription:
                                             self.on_transcription({"sender": "User", "text": delta})
                                        
                                        # Buffer for Logging
                                        if self.chat_buffer["sender"] != "User":
                                            # Flush previous if exists
                                            if self.chat_buffer["sender"] and self.chat_buffer["text"].strip():
                                                self.project_manager.log_chat(self.chat_buffer["sender"], self.chat_buffer["text"])
                                            # Start new
                                            self.chat_buffer = {"sender": "User", "text": delta}
                                        else:
                                            # Append
                                            self.chat_buffer["text"] += delta
                        
                        if response.server_content.output_transcription:
                            transcript = response.server_content.output_transcription.text
                            if transcript:
                                # Skip if this is an exact duplicate event
                                if transcript != self._last_output_transcription:
                                    # Calculate delta (Gemini may send cumulative or chunk-based text)
                                    delta = transcript
                                    if transcript.startswith(self._last_output_transcription):
                                        delta = transcript[len(self._last_output_transcription):]
                                    self._last_output_transcription = transcript
                                    
                                    # Only send if there's new text
                                    if delta:
                                        # Send to frontend (Streaming)
                                        if self.on_transcription:
                                             self.on_transcription({"sender": "ADA", "text": delta})
                                        
                                        # Buffer for Logging
                                        if self.chat_buffer["sender"] != "ADA":
                                            # Flush previous
                                            if self.chat_buffer["sender"] and self.chat_buffer["text"].strip():
                                                self.project_manager.log_chat(self.chat_buffer["sender"], self.chat_buffer["text"])
                                            # Start new
                                            self.chat_buffer = {"sender": "ADA", "text": delta}
                                        else:
                                            # Append
                                            self.chat_buffer["text"] += delta
                        
                        # Flush buffer on turn completion if needed, 
                        # but usually better to wait for sender switch or explicit end.
                        # We can also check turn_complete signal if available in response.server_content.model_turn etc

                    # 3. Handle Tool Calls
                    if response.tool_call:
                        print("The tool was called")
                        function_responses = []
                        for fc in response.tool_call.function_calls:
                            # All known tools including Google Workspace
                            known_tools = [
                                "run_web_agent", "write_file", "read_directory", "read_file",
                                "create_project", "switch_project", "list_projects",
                                "list_smart_devices", "control_light",
                                # Google Workspace tools
                                "google_authenticate", "google_list_events", "google_create_event", "google_delete_event",
                                "google_read_spreadsheet", "google_write_spreadsheet", "google_append_spreadsheet", "google_create_spreadsheet",
                                "google_add_sheet", "google_delete_sheet",
                                "google_list_drive_files", "google_upload_to_drive", "google_download_from_drive", "google_create_drive_folder",
                                "google_send_email", "google_list_emails", "google_read_email",
                                "google_create_document", "google_read_document", "google_append_document",
                                # Google Forms/Slides tools
                                "google_create_form", "google_create_presentation",
                                # n8n MCP tools
                                "n8n_connect", "n8n_list_workflows", "n8n_search_workflows", "n8n_execute_workflow", "n8n_get_workflow_info",
                                # Local PC tools
                                "pc_create_file", "pc_read_file", "pc_write_file", "pc_list_folder", "pc_create_folder", "pc_open_app", "pc_search_files",
                                # Webhook tools
                                "webhook_send", "webhook_send_saved", "webhook_list",
                                # WhatsApp tools
                                "wa_send_message", "wa_check_status",
                                # Document Printer tools
                                "doc_list_printers", "doc_print_file", "doc_print_text", "doc_printer_status",
                                # Yahoo Mail tools
                                "yahoo_send_email", "yahoo_list_emails"
                            ]
                            if fc.name in known_tools:
                                prompt = fc.args.get("prompt", "") # Prompt is not present for all tools
                                
                                # Check Permissions (Default to True if not set)
                                confirmation_required = self.permissions.get(fc.name, True)
                                
                                if not confirmation_required:
                                    print(f"[ADA DEBUG] [TOOL] Permission check: '{fc.name}' -> AUTO-ALLOW")
                                    # Skip confirmation block and jump to execution
                                    pass
                                else:
                                    # Confirmation Logic
                                    if self.on_tool_confirmation:
                                        import uuid
                                        request_id = str(uuid.uuid4())
                                    print(f"[ADA DEBUG] [STOP] Requesting confirmation for '{fc.name}' (ID: {request_id})")
                                    
                                    future = asyncio.Future()
                                    self._pending_confirmations[request_id] = future
                                    
                                    self.on_tool_confirmation({
                                        "id": request_id, 
                                        "tool": fc.name, 
                                        "args": fc.args
                                    })
                                    
                                    try:
                                        # Wait for user response
                                        confirmed = await future

                                    finally:
                                        self._pending_confirmations.pop(request_id, None)

                                    print(f"[ADA DEBUG] [CONFIRM] Request {request_id} resolved. Confirmed: {confirmed}")

                                    if not confirmed:
                                        print(f"[ADA DEBUG] [DENY] Tool call '{fc.name}' denied by user.")
                                        function_response = types.FunctionResponse(
                                            id=fc.id,
                                            name=fc.name,
                                            response={
                                                "result": "User denied the request to use this tool.",
                                            }
                                        )
                                        function_responses.append(function_response)
                                        continue

                                # If confirmed (or no callback configured, or auto-allowed), proceed
                                if fc.name == "run_web_agent":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'run_web_agent' with prompt='{prompt}'")
                                    asyncio.create_task(self.handle_web_agent_request(prompt))
                                    
                                    result_text = "Web Navigation started. Do not reply to this message."
                                    function_response = types.FunctionResponse(
                                        id=fc.id,
                                        name=fc.name,
                                        response={
                                            "result": result_text,
                                        }
                                    )
                                    print(f"[ADA DEBUG] [RESPONSE] Sending function response: {function_response}")
                                    function_responses.append(function_response)

                                elif fc.name == "google_create_spreadsheet":
                                    title = fc.args.get("title")
                                    sheets = fc.args.get("sheets")
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_create_spreadsheet' with title='{title}'")
                                    function_responses.append(await self._execute_tool(
                                        fc, self.handle_google_create_spreadsheet, title=title, sheets=sheets
                                    ))
                                
                                elif fc.name == "google_add_sheet":
                                    spreadsheet_id = fc.args.get("spreadsheet_id")
                                    title = fc.args.get("title")
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_add_sheet' with title='{title}'")
                                    function_responses.append(await self._execute_tool(
                                        fc, self.handle_google_add_sheet, spreadsheet_id=spreadsheet_id, title=title
                                    ))

                                elif fc.name == "google_delete_sheet":
                                    spreadsheet_id = fc.args.get("spreadsheet_id")
                                    sheet_title = fc.args.get("sheet_title")
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_delete_sheet' with title='{sheet_title}'")
                                    function_responses.append(await self._execute_tool(
                                        fc, self.handle_google_delete_sheet, spreadsheet_id=spreadsheet_id, sheet_title=sheet_title
                                    ))
                                elif fc.name == "write_file":
                                    path = fc.args["path"]
                                    content = fc.args["content"]
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'write_file' path='{path}'")
                                    asyncio.create_task(self.handle_write_file(path, content))
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": "Writing file..."}
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "read_directory":
                                    path = fc.args["path"]
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'read_directory' path='{path}'")
                                    asyncio.create_task(self.handle_read_directory(path))
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": "Reading directory..."}
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "read_file":
                                    path = fc.args["path"]
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'read_file' path='{path}'")
                                    asyncio.create_task(self.handle_read_file(path))
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": "Reading file..."}
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "create_project":
                                    name = fc.args["name"]
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'create_project' name='{name}'")
                                    success, msg = self.project_manager.create_project(name)
                                    if success:
                                        # Auto-switch to the newly created project
                                        self.project_manager.switch_project(name)
                                        msg += f" Switched to '{name}'."
                                        if self.on_project_update:
                                            self.on_project_update(name)
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": msg}
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "switch_project":
                                    name = fc.args["name"]
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'switch_project' name='{name}'")
                                    success, msg = self.project_manager.switch_project(name)
                                    if success:
                                        if self.on_project_update:
                                            self.on_project_update(name)
                                        # Gather project context and send to AI (silently, no response expected)
                                        context = self.project_manager.get_project_context()
                                        print(f"[ADA DEBUG] [PROJECT] Sending project context to AI ({len(context)} chars)")
                                        try:
                                            await self.session.send(input=f"System Notification: {msg}\n\n{context}", end_of_turn=False)
                                        except Exception as e:
                                            print(f"[ADA DEBUG] [ERR] Failed to send project context: {e}")
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": msg}
                                    )
                                    function_responses.append(function_response)
                                
                                elif fc.name == "list_projects":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'list_projects'")
                                    projects = self.project_manager.list_projects()
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": f"Available projects: {', '.join(projects)}"}
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "list_smart_devices":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'list_smart_devices'")
                                    # Use cached devices directly for speed
                                    # devices_dict is {ip: SmartDevice}
                                    
                                    dev_summaries = []
                                    frontend_list = []
                                    
                                    for ip, d in self.kasa_agent.devices.items():
                                        dev_type = "unknown"
                                        if d.is_bulb: dev_type = "bulb"
                                        elif d.is_plug: dev_type = "plug"
                                        elif d.is_strip: dev_type = "strip"
                                        elif d.is_dimmer: dev_type = "dimmer"
                                        
                                        # Format for Model
                                        info = f"{d.alias} (IP: {ip}, Type: {dev_type})"
                                        if d.is_on:
                                            info += " [ON]"
                                        else:
                                            info += " [OFF]"
                                        dev_summaries.append(info)
                                        
                                        # Format for Frontend
                                        frontend_list.append({
                                            "ip": ip,
                                            "alias": d.alias,
                                            "model": d.model,
                                            "type": dev_type,
                                            "is_on": d.is_on,
                                            "brightness": d.brightness if d.is_bulb or d.is_dimmer else None,
                                            "hsv": d.hsv if d.is_bulb and d.is_color else None,
                                            "has_color": d.is_color if d.is_bulb else False,
                                            "has_brightness": d.is_dimmable if d.is_bulb or d.is_dimmer else False
                                        })
                                    
                                    result_str = "No devices found in cache."
                                    if dev_summaries:
                                        result_str = "Found Devices (Cached):\n" + "\n".join(dev_summaries)
                                    
                                    # Trigger frontend update
                                    if self.on_device_update:
                                        self.on_device_update(frontend_list)

                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": result_str}
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "control_light":
                                    target = fc.args["target"]
                                    action = fc.args["action"]
                                    brightness = fc.args.get("brightness")
                                    color = fc.args.get("color")
                                    
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'control_light' Target='{target}' Action='{action}'")
                                    
                                    result_msg = f"Action '{action}' on '{target}' failed."
                                    success = False
                                    
                                    if action == "turn_on":
                                        success = await self.kasa_agent.turn_on(target)
                                        if success:
                                            result_msg = f"Turned ON '{target}'."
                                    elif action == "turn_off":
                                        success = await self.kasa_agent.turn_off(target)
                                        if success:
                                            result_msg = f"Turned OFF '{target}'."
                                    elif action == "set":
                                        success = True
                                        result_msg = f"Updated '{target}':"
                                    
                                    # Apply extra attributes if 'set' or if we just turned it on and want to set them too
                                    if success or action == "set":
                                        if brightness is not None:
                                            sb = await self.kasa_agent.set_brightness(target, brightness)
                                            if sb:
                                                result_msg += f" Set brightness to {brightness}."
                                        if color is not None:
                                            sc = await self.kasa_agent.set_color(target, color)
                                            if sc:
                                                result_msg += f" Set color to {color}."

                                    # Notify Frontend of State Change
                                    if success:
                                        # We don't need full discovery, just refresh known state or push update
                                        # But for simplicity, let's get the standard list representation
                                        # KasaAgent updates its internal state on control, so we can rebuild the list
                                        
                                        # Quick rebuild of list from internal dict
                                        updated_list = []
                                        for ip, dev in self.kasa_agent.devices.items():
                                            # We need to ensure we have the correct dict structure expected by frontend
                                            # We duplicate logic from KasaAgent.discover_devices a bit, but that's okay for now or we can add a helper
                                            # Ideally KasaAgent has a 'get_devices_list()' method.
                                            # Use the cached objects in self.kasa_agent.devices
                                            
                                            dev_type = "unknown"
                                            if dev.is_bulb: dev_type = "bulb"
                                            elif dev.is_plug: dev_type = "plug"
                                            elif dev.is_strip: dev_type = "strip"
                                            elif dev.is_dimmer: dev_type = "dimmer"

                                            d_info = {
                                                "ip": ip,
                                                "alias": dev.alias,
                                                "model": dev.model,
                                                "type": dev_type,
                                                "is_on": dev.is_on,
                                                "brightness": dev.brightness if dev.is_bulb or dev.is_dimmer else None,
                                                "hsv": dev.hsv if dev.is_bulb and dev.is_color else None,
                                                "has_color": dev.is_color if dev.is_bulb else False,
                                                "has_brightness": dev.is_dimmable if dev.is_bulb or dev.is_dimmer else False
                                            }
                                            updated_list.append(d_info)
                                            
                                        if self.on_device_update:
                                            self.on_device_update(updated_list)
                                    else:
                                        # Report Error
                                        if self.on_error:
                                            self.on_error(result_msg)

                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": result_msg}
                                    )
                                    function_responses.append(function_response)









                                # ==================== GOOGLE WORKSPACE TOOL ROUTING ====================
                                
                                elif fc.name == "google_authenticate":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_authenticate'")
                                    result = await self.handle_google_authenticate()
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response={"result": result.get("message", str(result))}
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "google_list_events":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_list_events'")
                                    result = await self.handle_google_list_events(
                                        max_results=fc.args.get("max_results", 10),
                                        time_min=fc.args.get("time_min"),
                                        time_max=fc.args.get("time_max")
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "google_create_event":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_create_event'")
                                    result = await self.handle_google_create_event(
                                        summary=fc.args["summary"],
                                        start_time=fc.args["start_time"],
                                        end_time=fc.args.get("end_time"),
                                        description=fc.args.get("description", ""),
                                        location=fc.args.get("location", ""),
                                        attendees=fc.args.get("attendees")
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "google_delete_event":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_delete_event'")
                                    result = await self.handle_google_delete_event(
                                        event_id=fc.args["event_id"]
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "google_read_spreadsheet":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_read_spreadsheet'")
                                    result = await self.handle_google_read_spreadsheet(
                                        spreadsheet_id=fc.args["spreadsheet_id"],
                                        range_name=fc.args.get("range_name", "Sheet1!A1:Z100")
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "google_write_spreadsheet":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_write_spreadsheet'")
                                    result = await self.handle_google_write_spreadsheet(
                                        spreadsheet_id=fc.args["spreadsheet_id"],
                                        range_name=fc.args["range_name"],
                                        values=fc.args["values"]
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "google_append_spreadsheet":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_append_spreadsheet'")
                                    result = await self.handle_google_append_spreadsheet(
                                        spreadsheet_id=fc.args["spreadsheet_id"],
                                        range_name=fc.args["range_name"],
                                        values=fc.args["values"]
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "google_create_spreadsheet":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_create_spreadsheet'")
                                    result = await self.handle_google_create_spreadsheet(
                                        title=fc.args["title"],
                                        sheets=fc.args.get("sheets")
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "google_list_drive_files":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_list_drive_files'")
                                    result = await self.handle_google_list_drive_files(
                                        query=fc.args.get("query"),
                                        max_results=fc.args.get("max_results", 20),
                                        folder_id=fc.args.get("folder_id")
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "google_upload_to_drive":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_upload_to_drive'")
                                    result = await self.handle_google_upload_to_drive(
                                        file_path=fc.args["file_path"],
                                        folder_id=fc.args.get("folder_id"),
                                        file_name=fc.args.get("file_name")
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "google_download_from_drive":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_download_from_drive'")
                                    result = await self.handle_google_download_from_drive(
                                        file_id=fc.args["file_id"],
                                        destination_path=fc.args["destination_path"]
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "google_create_drive_folder":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_create_drive_folder'")
                                    result = await self.handle_google_create_drive_folder(
                                        folder_name=fc.args["folder_name"],
                                        parent_id=fc.args.get("parent_id")
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "google_send_email":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_send_email'")
                                    result = await self.handle_google_send_email(
                                        to=fc.args["to"],
                                        subject=fc.args["subject"],
                                        body=fc.args["body"],
                                        cc=fc.args.get("cc"),
                                        bcc=fc.args.get("bcc")
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "google_list_emails":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_list_emails'")
                                    result = await self.handle_google_list_emails(
                                        max_results=fc.args.get("max_results", 10),
                                        query=fc.args.get("query")
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "google_read_email":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_read_email'")
                                    result = await self.handle_google_read_email(
                                        message_id=fc.args["message_id"]
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "google_create_document":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_create_document'")
                                    result = await self.handle_google_create_document(
                                        title=fc.args["title"],
                                        content=fc.args.get("content")
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "google_read_document":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_read_document'")
                                    result = await self.handle_google_read_document(
                                        document_id=fc.args["document_id"]
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "google_append_document":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_append_document'")
                                    result = await self.handle_google_append_document(
                                        document_id=fc.args["document_id"],
                                        content=fc.args["content"]
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                # ==================== N8N MCP TOOL ROUTING ====================

                                elif fc.name == "n8n_connect":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'n8n_connect'")
                                    result = await self.handle_n8n_connect()
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "n8n_list_workflows":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'n8n_list_workflows'")
                                    result = await self.handle_n8n_list_workflows()
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "n8n_search_workflows":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'n8n_search_workflows'")
                                    result = await self.handle_n8n_search_workflows(
                                        query=fc.args["query"]
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "n8n_execute_workflow":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'n8n_execute_workflow'")
                                    result = await self.handle_n8n_execute_workflow(
                                        workflow_name=fc.args["workflow_name"],
                                        input_data=fc.args.get("input_data")
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "n8n_get_workflow_info":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'n8n_get_workflow_info'")
                                    result = await self.handle_n8n_get_workflow_info(
                                        workflow_name=fc.args["workflow_name"]
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                # ==================== LOCAL PC TOOLS ====================

                                elif fc.name == "pc_create_file":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'pc_create_file'")
                                    result = await self.handle_pc_create_file(
                                        path=fc.args["path"],
                                        content=fc.args.get("content", "")
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "pc_read_file":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'pc_read_file'")
                                    result = await self.handle_pc_read_file(
                                        path=fc.args["path"]
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "pc_write_file":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'pc_write_file'")
                                    result = await self.handle_pc_write_file(
                                        path=fc.args["path"],
                                        content=fc.args["content"]
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "pc_list_folder":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'pc_list_folder'")
                                    result = await self.handle_pc_list_folder(
                                        path=fc.args.get("path", "Documents")
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "pc_create_folder":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'pc_create_folder'")
                                    result = await self.handle_pc_create_folder(
                                        path=fc.args["path"]
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "pc_open_app":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'pc_open_app'")
                                    result = await self.handle_pc_open_app(
                                        app_name=fc.args["app_name"],
                                        args=fc.args.get("args")
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "pc_search_files":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'pc_search_files'")
                                    result = await self.handle_pc_search_files(
                                        query=fc.args["query"],
                                        search_path=fc.args.get("search_path"),
                                        file_extension=fc.args.get("file_extension"),
                                        max_results=fc.args.get("max_results", 50),
                                        search_content=fc.args.get("search_content", False)
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                # ==================== WEBHOOK TOOLS ====================

                                elif fc.name == "webhook_send":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'webhook_send'")
                                    result = await self.handle_webhook_send(
                                        url=fc.args["url"],
                                        data=fc.args["data"],
                                        method=fc.args.get("method", "POST")
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "webhook_send_saved":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'webhook_send_saved'")
                                    result = await self.handle_webhook_send_saved(
                                        webhook_name=fc.args["webhook_name"],
                                        data=fc.args["data"]
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "webhook_list":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'webhook_list'")
                                    result = await self.handle_webhook_list()
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                # ==================== WHATSAPP TOOLS ====================

                                elif fc.name == "wa_send_message":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'wa_send_message'")
                                    result = await self.handle_wa_send_message(
                                        phone=fc.args["phone"],
                                        message=fc.args["message"]
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "wa_check_status":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'wa_check_status'")
                                    result = await self.handle_wa_check_status()
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                # ==================== DOCUMENT PRINTER TOOLS ====================

                                elif fc.name == "doc_list_printers":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'doc_list_printers'")
                                    result = await self.handle_doc_list_printers()
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "doc_print_file":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'doc_print_file'")
                                    result = await self.handle_doc_print_file(
                                        file_path=fc.args["file_path"],
                                        printer_name=fc.args.get("printer_name"),
                                        copies=fc.args.get("copies", 1)
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "doc_print_text":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'doc_print_text'")
                                    result = await self.handle_doc_print_text(
                                        text=fc.args["text"],
                                        printer_name=fc.args.get("printer_name")
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "doc_printer_status":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'doc_printer_status'")
                                    result = await self.handle_doc_printer_status(
                                        printer_name=fc.args.get("printer_name")
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                # ==================== GOOGLE FORMS/SLIDES TOOLS ====================

                                elif fc.name == "google_create_form":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_create_form'")
                                    result = await self.handle_google_create_form(
                                        title=fc.args["title"],
                                        document_title=fc.args.get("document_title")
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "google_create_presentation":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'google_create_presentation'")
                                    result = await self.handle_google_create_presentation(
                                        title=fc.args["title"]
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                # ==================== YAHOO MAIL TOOLS ====================

                                elif fc.name == "yahoo_send_email":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'yahoo_send_email'")
                                    result = await self.handle_yahoo_send_email(
                                        to=fc.args["to"],
                                        subject=fc.args["subject"],
                                        body=fc.args["body"]
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                                elif fc.name == "yahoo_list_emails":
                                    print(f"[ADA DEBUG] [TOOL] Tool Call: 'yahoo_list_emails'")
                                    result = await self.handle_yahoo_list_emails(
                                        limit=fc.args.get("limit", 5)
                                    )
                                    function_response = types.FunctionResponse(
                                        id=fc.id, name=fc.name, response=result
                                    )
                                    function_responses.append(function_response)

                        if function_responses:

                            await self.session.send_tool_response(function_responses=function_responses)
                
                # Turn/Response Loop Finished
                self.flush_chat()

                while not self.audio_in_queue.empty():
                    self.audio_in_queue.get_nowait()
        except Exception as e:
            print(f"Error in receive_audio: {e}")
            traceback.print_exc()
            # CRITICAL: Re-raise to crash the TaskGroup and trigger outer loop reconnect
            raise e

    async def play_audio(self):
        stream = await asyncio.to_thread(
            pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
            output_device_index=self.output_device_index,
        )
        while True:
            bytestream = await self.audio_in_queue.get()
            if self.on_audio_data:
                self.on_audio_data(bytestream)
            await asyncio.to_thread(stream.write, bytestream)

    async def get_frames(self):
        cap = await asyncio.to_thread(cv2.VideoCapture, 0, cv2.CAP_AVFOUNDATION)
        while True:
            if self.paused:
                await asyncio.sleep(0.1)
                continue
            frame = await asyncio.to_thread(self._get_frame, cap)
            if frame is None:
                break
            await asyncio.sleep(1.0)
            if self.out_queue:
                await self.out_queue.put(frame)
        cap.release()

    def _get_frame(self, cap):
        ret, frame = cap.read()
        if not ret:
            return None
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(frame_rgb)
        img.thumbnail([1024, 1024])
        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)
        image_bytes = image_io.read()
        return {"mime_type": "image/jpeg", "data": base64.b64encode(image_bytes).decode()}

    async def _get_screen(self):
        pass 
    async def get_screen(self):
         pass

    async def run(self, start_message=None):
        retry_delay = 1
        is_reconnect = False
        
        while not self.stop_event.is_set():
            try:
                print(f"[ADA DEBUG] [CONNECT] Connecting to Gemini Live API...")
                async with (
                    client.aio.live.connect(model=MODEL, config=config) as session,
                    asyncio.TaskGroup() as tg,
                ):
                    self.session = session

                    self.audio_in_queue = asyncio.Queue()
                    self.out_queue = asyncio.Queue(maxsize=10)

                    tg.create_task(self.send_realtime())
                    tg.create_task(self.listen_audio())
                    # tg.create_task(self._process_video_queue()) # Removed in favor of VAD

                    if self.video_mode == "camera":
                        tg.create_task(self.get_frames())
                    elif self.video_mode == "screen":
                        tg.create_task(self.get_screen())

                    tg.create_task(self.receive_audio())
                    tg.create_task(self.play_audio())

                    # Handle Startup vs Reconnect Logic
                    if not is_reconnect:
                        if start_message:
                            print(f"[ADA DEBUG] [INFO] Sending start message: {start_message}")
                            await self.session.send(input=start_message, end_of_turn=True)
                        
                        # Sync Project State
                        if self.on_project_update and self.project_manager:
                            self.on_project_update(self.project_manager.current_project)
                    
                    else:
                        print(f"[ADA DEBUG] [RECONNECT] Connection restored.")
                        # Restore Context
                        print(f"[ADA DEBUG] [RECONNECT] Fetching recent chat history to restore context...")
                        history = self.project_manager.get_recent_chat_history(limit=10)
                        
                        context_msg = "System Notification: Connection was lost and just re-established. Here is the recent chat history to help you resume seamlessly:\n\n"
                        for entry in history:
                            sender = entry.get('sender', 'Unknown')
                            text = entry.get('text', '')
                            context_msg += f"[{sender}]: {text}\n"
                        
                        context_msg += "\nPlease acknowledge the reconnection to the user (e.g. 'I lost connection for a moment, but I'm back...') and resume what you were doing."
                        
                        print(f"[ADA DEBUG] [RECONNECT] Sending restoration context to model...")
                        await self.session.send(input=context_msg, end_of_turn=True)

                    # Reset retry delay on successful connection
                    retry_delay = 1
                    
                    # Wait until stop event, or until the session task group exits (which happens on error)
                    # Actually, the TaskGroup context manager will exit if any tasks fail/cancel.
                    # We need to keep this block alive.
                    # The original code just waited on stop_event, but that doesn't account for session death.
                    # We should rely on the TaskGroup raising an exception when subtasks fail (like receive_audio).
                    
                    # However, since receive_audio is a task in the group, if it crashes (connection closed), 
                    # the group will cancel others and exit. We catch that exit below.
                    
                    # We can await stop_event, but if the connection dies, receive_audio crashes -> group closes -> we exit `async with` -> restart loop.
                    # To ensure we don't block indefinitely if connection dies silently (unlikely with receive_audio), we just wait.
                    await self.stop_event.wait()

            except asyncio.CancelledError:
                print(f"[ADA DEBUG] [STOP] Main loop cancelled.")
                break
                
            except Exception as e:
                # This catches the ExceptionGroup from TaskGroup or direct exceptions
                print(f"[ADA DEBUG] [ERR] Connection Error: {e}")
                
                if self.stop_event.is_set():
                    break
                
                print(f"[ADA DEBUG] [RETRY] Reconnecting in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 10) # Exponential backoff capped at 10s
                is_reconnect = True # Next loop will be a reconnect
                
            finally:
                # Cleanup before retry
                if hasattr(self, 'audio_stream') and self.audio_stream:
                    try:
                        self.audio_stream.close()
                    except: 
                        pass

def get_input_devices():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    devices = []
    for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            devices.append((i, p.get_device_info_by_host_api_device_index(0, i).get('name')))
    p.terminate()
    return devices

def get_output_devices():
    p = pyaudio.PyAudio()
    info = p.get_host_api_info_by_index(0)
    numdevices = info.get('deviceCount')
    devices = []
    for i in range(0, numdevices):
        if (p.get_device_info_by_host_api_device_index(0, i).get('maxOutputChannels')) > 0:
            devices.append((i, p.get_device_info_by_host_api_device_index(0, i).get('name')))
    p.terminate()
    return devices

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode",
        type=str,
        default=DEFAULT_MODE,
        help="pixels to stream from",
        choices=["camera", "screen", "none"],
    )
    args = parser.parse_args()
    main = AudioLoop(video_mode=args.mode)
    asyncio.run(main.run())