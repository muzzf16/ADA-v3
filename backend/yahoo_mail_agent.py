import os
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from dotenv import load_dotenv

load_dotenv()

class YahooMailAgent:
    def __init__(self):
        self.email_address = os.getenv("YAHOO_EMAIL")
        self.password = os.getenv("YAHOO_PASSWORD")
        self.imap_server = "imap.mail.yahoo.com"
        self.smtp_server = "smtp.mail.yahoo.com"
        
        if self.email_address:
            print(f"[YAHOO] Initialized with email: {self.email_address}")
        else:
            print("[YAHOO] WARNING: YAHOO_EMAIL not found in env.")
            
    def _connect_smtp(self):
        if not self.email_address or not self.password:
            raise ValueError("Yahoo credentials not found in env.")
        server = smtplib.SMTP_SSL(self.smtp_server, 465)
        server.login(self.email_address, self.password)
        return server

    def _connect_imap(self):
        if not self.email_address or not self.password:
            raise ValueError("Yahoo credentials not found in env.")
        mail = imaplib.IMAP4_SSL(self.imap_server)
        mail.login(self.email_address, self.password)
        return mail

    def send_email(self, to_email, subject, body):
        if not self.email_address or not self.password:
            return {"success": False, "error": "Yahoo credentials not configured"}

        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            server = self._connect_smtp()
            server.send_message(msg)
            server.quit()
            return {"success": True, "message": f"Email sent to {to_email}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_recent_emails(self, limit=5):
        if not self.email_address or not self.password:
            return {"success": False, "error": "Yahoo credentials not configured"}

        try:
            mail = self._connect_imap()
            mail.select("inbox")

            status, messages = mail.search(None, "ALL")
            if status != "OK":
                return {"success": False, "error": "Failed to search emails"}

            mail_ids = messages[0].split()
            # Get latest 'limit' emails
            latest_ids = mail_ids[-limit:]
            
            email_list = []
            
            for i in reversed(latest_ids):
                status, msg_data = mail.fetch(i, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        # Decode Subject
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                            
                        # Decode From
                        from_ = msg.get("From")
                        
                        # Get snippet (simplistic)
                        snippet = "No content"
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    snippet = part.get_payload(decode=True).decode(errors='ignore')[:100] + "..."
                                    break
                        else:
                            snippet = msg.get_payload(decode=True).decode(errors='ignore')[:100] + "..."

                        email_list.append({
                            "id": i.decode(),
                            "subject": subject,
                            "from": from_,
                            "snippet": snippet
                        })
            
            mail.logout()
            return {"success": True, "emails": email_list}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

# Singleton
_yahoo_agent = None
def get_yahoo_agent():
    global _yahoo_agent
    if _yahoo_agent is None:
        _yahoo_agent = YahooMailAgent()
    return _yahoo_agent
