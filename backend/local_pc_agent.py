"""
Local PC Agent - Handles local file system and application operations
Allows A.D.A to interact with the user's local PC.
"""

import os
import subprocess
import shutil
import platform
from typing import Optional, Dict, Any, List
from pathlib import Path


class LocalPCAgent:
    """
    Agent for local PC operations.
    
    Provides methods to:
    - Create, read, write, delete files
    - Create, list, delete folders
    - Open applications
    - Run system commands (with restrictions)
    """
    
    # Allowed base directories (relative to user home)
    ALLOWED_DIRS = ['Desktop', 'Documents', 'Downloads', 'Pictures', 'Videos', 'Music']
    
    # Allowed drives (Windows) - add more as needed
    ALLOWED_DRIVES = ['C:', 'D:', 'E:', 'F:', 'G:']
    
    # Blocked file extensions for write/delete operations
    BLOCKED_EXTENSIONS = ['.exe', '.dll', '.sys', '.bat', '.cmd', '.ps1', '.vbs', '.msi']
    
    # Whitelisted applications that can be opened
    # Using Windows 'start' command which works universally
    ALLOWED_APPS = {
        'notepad': 'notepad',
        'calculator': 'calc',
        'paint': 'mspaint',
        'explorer': 'explorer',
        'browser': 'start',
        'chrome': 'start chrome',
        'edge': 'start msedge',
        'firefox': 'start firefox',
        'vscode': 'code',
        'word': 'start winword',
        'excel': 'start excel',
        'powerpoint': 'start powerpnt',
        'terminal': 'wt',
        'cmd': 'cmd',
        'powershell': 'powershell',
    }
    
    def __init__(self):
        """Initialize the Local PC Agent."""
        self.home_dir = Path.home()
        self.system = platform.system()  # 'Windows', 'Linux', 'Darwin'
        
    def _get_safe_path(self, path: str) -> Optional[Path]:
        """
        Validate and return a safe path within allowed directories or drives.
        Returns None if path is not allowed.
        """
        try:
            # Expand path
            if path.startswith('~'):
                full_path = Path(path).expanduser()
            elif not os.path.isabs(path):
                # Check if it starts with an allowed directory name
                parts = path.replace('\\', '/').split('/')
                if parts[0] in self.ALLOWED_DIRS:
                    full_path = self.home_dir / path
                else:
                    # Default to Documents if no base specified
                    full_path = self.home_dir / 'Documents' / path
            else:
                full_path = Path(path)
            
            # Resolve to absolute path
            full_path = full_path.resolve()
            
            # Check if path is on an allowed drive (Windows)
            if self.system == 'Windows':
                drive = full_path.drive.upper()
                if drive and any(drive.startswith(d.upper().rstrip(':')) for d in self.ALLOWED_DRIVES):
                    return full_path
            
            # Check if path is within allowed directories (user home)
            for allowed_dir in self.ALLOWED_DIRS:
                allowed_path = (self.home_dir / allowed_dir).resolve()
                try:
                    full_path.relative_to(allowed_path)
                    return full_path
                except ValueError:
                    continue
            
            # Also allow direct home directory
            try:
                full_path.relative_to(self.home_dir)
                return full_path
            except ValueError:
                pass
                
            return None
            
        except Exception:
            return None
    
    def _is_blocked_extension(self, path: Path) -> bool:
        """Check if file has a blocked extension."""
        return path.suffix.lower() in self.BLOCKED_EXTENSIONS
    
    async def create_file(self, path: str, content: str = "") -> Dict[str, Any]:
        """
        Create a new file with optional content.
        
        Args:
            path: File path (relative to user dirs or absolute within allowed)
            content: Optional content to write
        """
        safe_path = self._get_safe_path(path)
        
        if safe_path is None:
            return {
                "success": False,
                "error": f"Path not allowed. Use directories like: {', '.join(self.ALLOWED_DIRS)}"
            }
        
        if self._is_blocked_extension(safe_path):
            return {
                "success": False,
                "error": f"Cannot create files with extension: {safe_path.suffix}"
            }
        
        try:
            # Create parent directories if needed
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file already exists
            if safe_path.exists():
                return {
                    "success": False,
                    "error": f"File already exists: {safe_path}"
                }
            
            # Write file
            safe_path.write_text(content, encoding='utf-8')
            
            return {
                "success": True,
                "path": str(safe_path),
                "message": f"File created successfully: {safe_path.name}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def read_file(self, path: str) -> Dict[str, Any]:
        """Read content from a file."""
        safe_path = self._get_safe_path(path)
        
        if safe_path is None:
            return {
                "success": False,
                "error": f"Path not allowed. Use directories like: {', '.join(self.ALLOWED_DIRS)}"
            }
        
        try:
            if not safe_path.exists():
                return {"success": False, "error": f"File not found: {path}"}
            
            if not safe_path.is_file():
                return {"success": False, "error": f"Not a file: {path}"}
            
            # Limit file size to 1MB
            if safe_path.stat().st_size > 1_000_000:
                return {"success": False, "error": "File too large (max 1MB)"}
            
            content = safe_path.read_text(encoding='utf-8', errors='replace')
            
            return {
                "success": True,
                "path": str(safe_path),
                "content": content,
                "size": len(content)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to an existing file or create new one."""
        safe_path = self._get_safe_path(path)
        
        if safe_path is None:
            return {
                "success": False,
                "error": f"Path not allowed. Use directories like: {', '.join(self.ALLOWED_DIRS)}"
            }
        
        if self._is_blocked_extension(safe_path):
            return {
                "success": False,
                "error": f"Cannot write to files with extension: {safe_path.suffix}"
            }
        
        try:
            # Create parent directories if needed
            safe_path.parent.mkdir(parents=True, exist_ok=True)
            
            safe_path.write_text(content, encoding='utf-8')
            
            return {
                "success": True,
                "path": str(safe_path),
                "message": f"File written successfully: {safe_path.name}",
                "size": len(content)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file (requires confirmation in handler)."""
        safe_path = self._get_safe_path(path)
        
        if safe_path is None:
            return {
                "success": False,
                "error": f"Path not allowed. Use directories like: {', '.join(self.ALLOWED_DIRS)}"
            }
        
        if self._is_blocked_extension(safe_path):
            return {
                "success": False,
                "error": f"Cannot delete files with extension: {safe_path.suffix}"
            }
        
        try:
            if not safe_path.exists():
                return {"success": False, "error": f"File not found: {path}"}
            
            if not safe_path.is_file():
                return {"success": False, "error": f"Not a file: {path}"}
            
            safe_path.unlink()
            
            return {
                "success": True,
                "path": str(safe_path),
                "message": f"File deleted: {safe_path.name}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def create_folder(self, path: str) -> Dict[str, Any]:
        """Create a new folder."""
        safe_path = self._get_safe_path(path)
        
        if safe_path is None:
            return {
                "success": False,
                "error": f"Path not allowed. Use directories like: {', '.join(self.ALLOWED_DIRS)}"
            }
        
        try:
            if safe_path.exists():
                return {"success": False, "error": f"Folder already exists: {path}"}
            
            safe_path.mkdir(parents=True, exist_ok=False)
            
            return {
                "success": True,
                "path": str(safe_path),
                "message": f"Folder created: {safe_path.name}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def list_folder(self, path: str = "Documents") -> Dict[str, Any]:
        """List contents of a folder."""
        safe_path = self._get_safe_path(path)
        
        if safe_path is None:
            return {
                "success": False,
                "error": f"Path not allowed. Use directories like: {', '.join(self.ALLOWED_DIRS)}"
            }
        
        try:
            if not safe_path.exists():
                return {"success": False, "error": f"Folder not found: {path}"}
            
            if not safe_path.is_dir():
                return {"success": False, "error": f"Not a folder: {path}"}
            
            items = []
            for item in safe_path.iterdir():
                try:
                    stat = item.stat()
                    items.append({
                        "name": item.name,
                        "type": "folder" if item.is_dir() else "file",
                        "size": stat.st_size if item.is_file() else None
                    })
                except:
                    items.append({"name": item.name, "type": "unknown"})
            
            # Sort: folders first, then files
            items.sort(key=lambda x: (0 if x["type"] == "folder" else 1, x["name"].lower()))
            
            return {
                "success": True,
                "path": str(safe_path),
                "items": items[:50],  # Limit to 50 items
                "total": len(items)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def delete_folder(self, path: str) -> Dict[str, Any]:
        """Delete a folder (requires confirmation, must be empty or use force)."""
        safe_path = self._get_safe_path(path)
        
        if safe_path is None:
            return {
                "success": False,
                "error": f"Path not allowed. Use directories like: {', '.join(self.ALLOWED_DIRS)}"
            }
        
        try:
            if not safe_path.exists():
                return {"success": False, "error": f"Folder not found: {path}"}
            
            if not safe_path.is_dir():
                return {"success": False, "error": f"Not a folder: {path}"}
            
            # Check if empty
            if any(safe_path.iterdir()):
                return {
                    "success": False,
                    "error": "Folder is not empty. Cannot delete non-empty folders."
                }
            
            safe_path.rmdir()
            
            return {
                "success": True,
                "path": str(safe_path),
                "message": f"Folder deleted: {safe_path.name}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def open_application(self, app_name: str, args: str = None) -> Dict[str, Any]:
        """
        Open an application.
        
        Args:
            app_name: Name of application (notepad, chrome, etc.)
            args: Optional arguments (e.g., URL for browser)
        """
        app_lower = app_name.lower().strip()
        
        # Check if app is whitelisted
        if app_lower not in self.ALLOWED_APPS:
            available = ', '.join(sorted(self.ALLOWED_APPS.keys()))
            return {
                "success": False,
                "error": f"Application '{app_name}' not in allowed list. Available: {available}"
            }
        
        try:
            cmd = self.ALLOWED_APPS[app_lower]
            
            if self.system == 'Windows':
                # Build full command string for shell execution
                if args:
                    full_cmd = f'{cmd} "{args}"'
                else:
                    full_cmd = cmd
                
                print(f"[LOCAL_PC] Executing: {full_cmd}")
                subprocess.Popen(full_cmd, shell=True)
            else:
                # Linux/macOS - use open or xdg-open
                opener = 'open' if self.system == 'Darwin' else 'xdg-open'
                if args:
                    subprocess.Popen([opener, args])
                else:
                    subprocess.Popen([opener, cmd])
            
            return {
                "success": True,
                "app": app_name,
                "message": f"Application '{app_name}' opened successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def run_command(self, command: str) -> Dict[str, Any]:
        """
        Run a system command (restricted to safe commands).
        Only informational commands are allowed.
        """
        # Whitelist of safe commands (info only)
        safe_commands = ['dir', 'ls', 'echo', 'date', 'time', 'hostname', 'whoami', 'ipconfig', 'ifconfig']
        
        cmd_lower = command.lower().strip().split()[0] if command.strip() else ''
        
        if cmd_lower not in safe_commands:
            return {
                "success": False,
                "error": f"Command not allowed. Safe commands: {', '.join(safe_commands)}"
            }
        
        try:
            if self.system == 'Windows':
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            else:
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            
            output = result.stdout or result.stderr
            
            return {
                "success": result.returncode == 0,
                "command": command,
                "output": output[:5000] if output else "No output",
                "return_code": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out (10s limit)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def search_files(self, query: str, search_path: str = None, 
                           file_extension: str = None, max_results: int = 50,
                           search_content: bool = False) -> Dict[str, Any]:
        """
        Search for files on the local PC.
        
        Args:
            query: Search query - filename pattern or substring to match
            search_path: Directory to search in (e.g., 'Documents', 'Desktop')
            file_extension: File extension filter without dot (e.g., 'pdf', 'docx')
            max_results: Maximum number of results to return
            search_content: If True, also search within file contents (slower)
        
        Returns:
            Dict with success status and list of matching files
        """
        import fnmatch
        
        results = []
        searched_paths = []
        
        try:
            # Determine search directories
            if search_path:
                safe_path = self._get_safe_path(search_path)
                if safe_path is None:
                    return {
                        "success": False,
                        "error": f"Path not allowed. Use directories like: {', '.join(self.ALLOWED_DIRS)}"
                    }
                search_dirs = [safe_path]
            else:
                # Search all allowed directories
                search_dirs = []
                for allowed_dir in self.ALLOWED_DIRS:
                    dir_path = self.home_dir / allowed_dir
                    if dir_path.exists():
                        search_dirs.append(dir_path)
            
            # Prepare search patterns
            query_lower = query.lower()
            has_wildcard = '*' in query or '?' in query
            
            # Search each directory
            for search_dir in search_dirs:
                searched_paths.append(str(search_dir))
                
                if len(results) >= max_results:
                    break
                
                try:
                    # Use rglob for recursive search
                    if has_wildcard:
                        # Use the pattern directly for glob
                        pattern = query if file_extension is None else f"{query}.{file_extension}"
                        for file_path in search_dir.rglob(pattern):
                            if len(results) >= max_results:
                                break
                            if file_path.is_file():
                                results.append(self._format_file_result(file_path, search_dir))
                    else:
                        # Search by substring match
                        for file_path in search_dir.rglob("*"):
                            if len(results) >= max_results:
                                break
                            
                            if not file_path.is_file():
                                continue
                            
                            # Check extension filter
                            if file_extension:
                                if file_path.suffix.lower() != f".{file_extension.lower()}":
                                    continue
                            
                            # Check filename match
                            if query_lower in file_path.name.lower():
                                results.append(self._format_file_result(file_path, search_dir))
                                continue
                            
                            # Optionally search content
                            if search_content and file_path.suffix.lower() in ['.txt', '.md', '.py', '.js', '.css', '.html', '.json', '.csv', '.log']:
                                try:
                                    # Only search small files
                                    if file_path.stat().st_size <= 500_000:  # 500KB limit
                                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                                        if query_lower in content.lower():
                                            result = self._format_file_result(file_path, search_dir)
                                            result['content_match'] = True
                                            results.append(result)
                                except Exception:
                                    pass
                                    
                except PermissionError:
                    continue
                except Exception as e:
                    print(f"[LOCAL_PC] Error searching {search_dir}: {e}")
                    continue
            
            return {
                "success": True,
                "query": query,
                "searched_paths": searched_paths,
                "results": results,
                "total_found": len(results),
                "max_results": max_results
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _format_file_result(self, file_path: Path, base_dir: Path) -> Dict[str, Any]:
        """Format a file path into a result dict."""
        try:
            stat = file_path.stat()
            size = stat.st_size
            
            # Format size
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            
            return {
                "name": file_path.name,
                "path": str(file_path),
                "relative_path": str(file_path.relative_to(base_dir)),
                "size": size_str,
                "extension": file_path.suffix.lower(),
                "content_match": False
            }
        except Exception:
            return {
                "name": file_path.name,
                "path": str(file_path),
                "size": "unknown"
            }


# Singleton instance
_agent_instance: Optional[LocalPCAgent] = None


def get_local_pc_agent() -> LocalPCAgent:
    """Get or create the singleton LocalPCAgent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = LocalPCAgent()
    return _agent_instance


# Test function
async def test_agent():
    """Test the Local PC Agent."""
    agent = get_local_pc_agent()
    
    print(f"System: {agent.system}")
    print(f"Home: {agent.home_dir}")
    
    print("\n1. List Desktop...")
    result = await agent.list_folder("Desktop")
    print(f"   {result}")
    
    print("\n2. List Documents...")
    result = await agent.list_folder("Documents")
    print(f"   {result}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_agent())
