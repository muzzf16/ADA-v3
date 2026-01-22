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
definitions = [
    pc_create_file_tool,
    pc_read_file_tool,
    pc_write_file_tool,
    pc_list_folder_tool,
    pc_create_folder_tool,
    pc_open_app_tool,
    pc_search_files_tool,
]
