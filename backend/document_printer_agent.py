"""
Document Printer Agent - Handles document printing to local and network printers.
Allows A.D.A to print documents, PDFs, and images.
"""

import os
import asyncio
import subprocess
import platform
from typing import Optional, Dict, Any, List
from pathlib import Path

# For Windows printing
if platform.system() == 'Windows':
    try:
        import win32print
        import win32api
        WIN32_AVAILABLE = True
    except ImportError:
        WIN32_AVAILABLE = False
else:
    WIN32_AVAILABLE = False


class DocumentPrinterAgent:
    """
    Agent for document printing operations.
    
    Provides methods to:
    - List available printers
    - Print documents/files
    - Get printer status
    - Set default printer
    """
    
    # Supported file extensions for direct printing
    SUPPORTED_EXTENSIONS = ['.pdf', '.txt', '.doc', '.docx', '.xls', '.xlsx', '.png', '.jpg', '.jpeg', '.bmp']
    
    def __init__(self):
        """Initialize the Document Printer Agent."""
        self.system = platform.system()
        self._default_printer = None
    
    async def list_printers(self) -> Dict[str, Any]:
        """
        List all available printers on the system.
        
        Returns:
            dict with list of printers and default printer
        """
        printers = []
        default = None
        
        try:
            if self.system == 'Windows':
                if WIN32_AVAILABLE:
                    # Get all printers using win32print
                    printer_enum = win32print.EnumPrinters(
                        win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
                    )
                    
                    for printer in printer_enum:
                        # printer tuple: (flags, description, name, comment)
                        printers.append({
                            "name": printer[2],
                            "description": printer[1],
                            "comment": printer[3] if len(printer) > 3 else ""
                        })
                    
                    # Get default printer
                    default = win32print.GetDefaultPrinter()
                else:
                    # Fallback: use wmic command
                    result = await asyncio.to_thread(
                        subprocess.run,
                        ['wmic', 'printer', 'get', 'name,default,status'],
                        capture_output=True,
                        text=True,
                        shell=True
                    )
                    
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')[1:]  # Skip header
                        for line in lines:
                            if line.strip():
                                parts = line.strip().split()
                                if parts:
                                    name = ' '.join(parts[:-2]) if len(parts) > 2 else parts[0]
                                    is_default = 'TRUE' in line.upper()
                                    printers.append({"name": name, "is_default": is_default})
                                    if is_default:
                                        default = name
            
            elif self.system == 'Darwin':  # macOS
                result = await asyncio.to_thread(
                    subprocess.run,
                    ['lpstat', '-p'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if line.startswith('printer'):
                            parts = line.split()
                            if len(parts) >= 2:
                                printers.append({"name": parts[1]})
                
                # Get default
                result_default = await asyncio.to_thread(
                    subprocess.run,
                    ['lpstat', '-d'],
                    capture_output=True,
                    text=True
                )
                if result_default.returncode == 0:
                    default = result_default.stdout.split(':')[-1].strip()
            
            else:  # Linux
                result = await asyncio.to_thread(
                    subprocess.run,
                    ['lpstat', '-p'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if 'printer' in line.lower():
                            parts = line.split()
                            if len(parts) >= 2:
                                printers.append({"name": parts[1]})
            
            return {
                "success": True,
                "printers": printers,
                "default": default,
                "count": len(printers)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_default_printer(self) -> Dict[str, Any]:
        """Get the default printer name."""
        try:
            if self.system == 'Windows' and WIN32_AVAILABLE:
                default = win32print.GetDefaultPrinter()
                return {"success": True, "printer": default}
            else:
                result = await self.list_printers()
                if result.get("success"):
                    return {"success": True, "printer": result.get("default", "Unknown")}
                else:
                    return result
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def print_file(self, file_path: str, printer_name: str = None, copies: int = 1) -> Dict[str, Any]:
        """
        Print a file to a specified printer.
        
        Args:
            file_path: Path to the file to print
            printer_name: Name of printer (uses default if not specified)
            copies: Number of copies to print
        
        Returns:
            dict with success status
        """
        # Validate file
        path = Path(file_path)
        
        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}
        
        ext = path.suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            return {
                "success": False, 
                "error": f"Unsupported file type: {ext}. Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}"
            }
        
        try:
            if self.system == 'Windows':
                # Use Windows ShellExecute for printing
                if WIN32_AVAILABLE:
                    printer = printer_name or win32print.GetDefaultPrinter()
                    
                    # For PDF and images, use ShellExecute "print" verb
                    for _ in range(copies):
                        win32api.ShellExecute(
                            0,
                            "print",
                            str(path.absolute()),
                            f'/d:"{printer}"',
                            ".",
                            0
                        )
                    
                    return {
                        "success": True,
                        "file": path.name,
                        "printer": printer,
                        "copies": copies,
                        "message": f"Print job sent to {printer}"
                    }
                else:
                    # Fallback: use start /print
                    cmd = f'start /min /wait "" "{path.absolute()}"'
                    result = await asyncio.to_thread(
                        subprocess.run,
                        cmd,
                        shell=True,
                        capture_output=True
                    )
                    return {
                        "success": result.returncode == 0,
                        "file": path.name,
                        "message": "Print job sent"
                    }
            
            elif self.system in ['Darwin', 'Linux']:
                # Use lp command for macOS/Linux
                cmd = ['lp']
                if printer_name:
                    cmd.extend(['-d', printer_name])
                cmd.extend(['-n', str(copies)])
                cmd.append(str(path.absolute()))
                
                result = await asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    return {
                        "success": True,
                        "file": path.name,
                        "printer": printer_name or "default",
                        "copies": copies,
                        "message": f"Print job sent"
                    }
                else:
                    return {
                        "success": False,
                        "error": result.stderr or "Print failed"
                    }
            
            else:
                return {"success": False, "error": f"Unsupported OS: {self.system}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def print_text(self, text: str, printer_name: str = None, title: str = "ADA Print") -> Dict[str, Any]:
        """
        Print text directly.
        
        Args:
            text: Text content to print
            printer_name: Name of printer
            title: Document title
        
        Returns:
            dict with success status
        """
        try:
            # Create temp file with text
            import tempfile
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(text)
                temp_path = f.name
            
            # Print the temp file
            result = await self.print_file(temp_path, printer_name)
            
            # Clean up temp file (with delay to allow printing to start)
            await asyncio.sleep(2)
            try:
                os.remove(temp_path)
            except:
                pass
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def get_printer_status(self, printer_name: str = None) -> Dict[str, Any]:
        """
        Get status of a printer.
        
        Args:
            printer_name: Name of printer (uses default if not specified)
        
        Returns:
            dict with printer status
        """
        try:
            if self.system == 'Windows' and WIN32_AVAILABLE:
                printer = printer_name or win32print.GetDefaultPrinter()
                
                # Open printer to get status
                try:
                    handle = win32print.OpenPrinter(printer)
                    info = win32print.GetPrinter(handle, 2)
                    win32print.ClosePrinter(handle)
                    
                    status_code = info.get('Status', 0)
                    
                    # Decode status
                    status_map = {
                        0: "Ready",
                        1: "Paused",
                        2: "Error",
                        4: "Pending Deletion",
                        8: "Paper Jam",
                        16: "Paper Out",
                        32: "Manual Feed",
                        64: "Paper Problem",
                        128: "Offline",
                        256: "IO Active",
                        512: "Busy",
                        1024: "Printing",
                    }
                    
                    status = status_map.get(status_code, f"Status code: {status_code}")
                    
                    return {
                        "success": True,
                        "printer": printer,
                        "status": status,
                        "jobs": info.get('cJobs', 0)
                    }
                except Exception as e:
                    return {"success": False, "error": str(e)}
            
            else:
                # Use lpstat for Linux/macOS
                cmd = ['lpstat', '-p']
                if printer_name:
                    cmd.append(printer_name)
                
                result = await asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    return {
                        "success": True,
                        "printer": printer_name or "default",
                        "status": result.stdout.strip()
                    }
                else:
                    return {"success": False, "error": result.stderr}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton instance
_agent_instance: Optional[DocumentPrinterAgent] = None


def get_document_printer_agent() -> DocumentPrinterAgent:
    """Get or create the singleton DocumentPrinterAgent instance."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = DocumentPrinterAgent()
    return _agent_instance


# Test function
async def test_agent():
    """Test the Document Printer Agent."""
    agent = get_document_printer_agent()
    
    print(f"System: {agent.system}")
    print(f"Win32 Available: {WIN32_AVAILABLE}")
    
    print("\n1. List printers...")
    result = await agent.list_printers()
    print(f"   {result}")
    
    print("\n2. Get default printer...")
    result = await agent.get_default_printer()
    print(f"   {result}")


if __name__ == "__main__":
    asyncio.run(test_agent())
