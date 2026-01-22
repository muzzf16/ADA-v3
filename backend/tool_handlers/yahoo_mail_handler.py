import asyncio
from typing import Dict, Any
from yahoo_mail_agent import YahooMailAgent

class YahooMailHandler:
    def __init__(self, agent: YahooMailAgent):
        self.agent = agent

    async def handle_yahoo_send_email(self, to, subject, body):
        """Handle sending email via Yahoo Mail."""
        print(f"[ADA DEBUG] [YAHOO] Sending email to: {to}")
        result = await asyncio.to_thread(
            self.agent.send_email, to, subject, body
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
            self.agent.get_recent_emails, limit
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
