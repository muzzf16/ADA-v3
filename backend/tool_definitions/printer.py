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
definitions = [
    doc_list_printers_tool,
    doc_print_file_tool,
    doc_print_text_tool,
    doc_printer_status_tool,
]
