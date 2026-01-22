from typing import Dict, Any
from document_printer_agent import DocumentPrinterAgent

class PrinterHandler:
    def __init__(self, agent: DocumentPrinterAgent):
        self.agent = agent

    async def handle_doc_list_printers(self):
        """Handle listing available printers."""
        print(f"[ADA DEBUG] [PRINTER] Listing printers")
        result = await self.agent.list_printers()

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
        result = await self.agent.print_file(file_path, printer_name, copies)

        if result.get("success"):
            msg = f"File '{result.get('file')}' berhasil dikirim ke printer {result.get('printer')}!"
        else:
            msg = f"Gagal mencetak: {result.get('error')}"

        return {"result": msg}

    async def handle_doc_print_text(self, text, printer_name=None):
        """Handle printing text directly."""
        print(f"[ADA DEBUG] [PRINTER] Printing text")
        result = await self.agent.print_text(text, printer_name)

        if result.get("success"):
            msg = f"Teks berhasil dikirim ke printer!"
        else:
            msg = f"Gagal mencetak teks: {result.get('error')}"

        return {"result": msg}

    async def handle_doc_printer_status(self, printer_name=None):
        """Handle getting printer status."""
        print(f"[ADA DEBUG] [PRINTER] Getting status")
        result = await self.agent.get_printer_status(printer_name)

        if result.get("success"):
            msg = f"Printer: {result.get('printer')}\nStatus: {result.get('status')}"
            if result.get('jobs'):
                msg += f"\nAntrian: {result.get('jobs')} job"
        else:
            msg = f"Gagal mendapatkan status: {result.get('error')}"

        return {"result": msg}
