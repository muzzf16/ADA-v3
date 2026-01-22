from typing import Dict, Any
from whatsapp_agent import WhatsAppAgent

class WhatsAppHandler:
    def __init__(self, agent: WhatsAppAgent):
        self.agent = agent

    async def handle_wa_send_message(self, phone, message):
        """Handle sending a WhatsApp message."""
        print(f"[ADA DEBUG] [WA] Sending message to: {phone}")
        result = await self.agent.send_message(phone, message)

        if result.get("success"):
            msg = f"Pesan WhatsApp berhasil dikirim ke {result.get('phone', phone)}!"
        else:
            msg = f"Gagal mengirim WhatsApp: {result.get('error', 'Unknown error')}"

        return {"result": msg}

    async def handle_wa_check_status(self):
        """Handle checking WhatsApp connection status."""
        print(f"[ADA DEBUG] [WA] Checking status")
        result = await self.agent.check_connection()

        if result.get("success"):
            status = result.get("status", "unknown")
            msg = f"WhatsApp status: {status}. Connection ID: {result.get('connection_id', 'default')}"
        else:
            msg = f"WhatsApp tidak terhubung: {result.get('error', 'Unknown error')}"

        return {"result": msg}
