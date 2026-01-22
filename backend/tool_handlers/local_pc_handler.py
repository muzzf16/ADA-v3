from typing import Dict, Any
from local_pc_agent import LocalPcAgent

class LocalPcHandler:
    def __init__(self, agent: LocalPcAgent):
        self.agent = agent

    async def handle_pc_create_file(self, path, content=""):
        """Handle creating a file on local PC."""
        print(f"[ADA DEBUG] [PC] Creating file: {path}")
        result = await self.agent.create_file(path, content)

        if result.get("success"):
            message = f"File created successfully at: {result.get('path')}"
        else:
            message = f"Failed to create file: {result.get('error', 'Unknown error')}"

        return {"result": message}

    async def handle_pc_read_file(self, path):
        """Handle reading a file from local PC."""
        print(f"[ADA DEBUG] [PC] Reading file: {path}")
        result = await self.agent.read_file(path)

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
        result = await self.agent.write_file(path, content)

        if result.get("success"):
            message = f"File written successfully: {result.get('path')}"
        else:
            message = f"Failed to write file: {result.get('error', 'Unknown error')}"

        return {"result": message}

    async def handle_pc_list_folder(self, path="Documents"):
        """Handle listing folder contents on local PC."""
        print(f"[ADA DEBUG] [PC] Listing folder: {path}")
        result = await self.agent.list_folder(path)

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
        result = await self.agent.create_folder(path)

        if result.get("success"):
            message = f"Folder created successfully: {result.get('path')}"
        else:
            message = f"Failed to create folder: {result.get('error', 'Unknown error')}"

        return {"result": message}

    async def handle_pc_open_app(self, app_name, args=None):
        """Handle opening an application on local PC."""
        print(f"[ADA DEBUG] [PC] Opening app: {app_name}")
        result = await self.agent.open_application(app_name, args)

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
        result = await self.agent.search_files(
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
