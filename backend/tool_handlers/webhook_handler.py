from typing import Dict, Any
from webhook_agent import WebhookAgent

class WebhookHandler:
    def __init__(self, agent: WebhookAgent):
        self.agent = agent

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

        result = await self.agent.send_webhook(url, parsed_data, method)

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

        result = await self.agent.send_to_saved_webhook(webhook_name, parsed_data)

        if result.get("success"):
            message = f"Webhook '{webhook_name}' sent successfully!"
        else:
            message = f"Failed to send webhook: {result.get('error', 'Unknown error')}"

        return {"result": message}

    async def handle_webhook_list(self):
        """Handle listing all webhooks."""
        print(f"[ADA DEBUG] [WEBHOOK] Listing webhooks")

        saved = self.agent.list_saved_webhooks()
        registered = self.agent.list_registered_webhooks()

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
