from typing import Dict, Any, List
from google_workspace_agent import GoogleWorkspaceAgent

class GoogleWorkspaceHandler:
    def __init__(self, agent: GoogleWorkspaceAgent):
        self.agent = agent

    async def handle_google_authenticate(self):
        """Handle Google Workspace authentication."""
        print(f"[ADA DEBUG] [GOOGLE] Starting authentication...")
        result = await self.agent.authenticate()

        if result.get("success"):
            message = "Successfully authenticated with Google Workspace! You can now use Calendar, Sheets, Drive, Gmail, and Docs."
        else:
            message = f"Google authentication failed: {result.get('error', 'Unknown error')}"

        print(f"[ADA DEBUG] [GOOGLE] Auth result: {message}")
        return {"result": message}

    async def handle_google_list_events(self, max_results=10, time_min=None, time_max=None):
        """Handle listing calendar events."""
        print(f"[ADA DEBUG] [GOOGLE] Listing calendar events...")
        result = await self.agent.list_calendar_events(
            max_results=max_results,
            time_min=time_min,
            time_max=time_max
        )

        if result.get("success"):
            events = result.get("events", [])
            if events:
                event_list = "\n".join([
                    f"- {e['summary']} at {e['start']}" for e in events
                ])
                message = f"Found {len(events)} upcoming events:\n{event_list}"
            else:
                message = "No upcoming events found."
        else:
            message = f"Failed to list events: {result.get('error', 'Unknown error')}"

        print(f"[ADA DEBUG] [GOOGLE] List events result: {message[:100]}...")
        return {"result": message}

    async def handle_google_create_event(self, summary, start_time, end_time=None, description="", location="", attendees=None):
        """Handle creating a calendar event."""
        print(f"[ADA DEBUG] [GOOGLE] Creating event: {summary}")

        attendees_list = None
        if attendees:
            attendees_list = [a.strip() for a in attendees.split(",")]

        result = await self.agent.create_calendar_event(
            summary=summary,
            start_time=start_time,
            end_time=end_time,
            description=description,
            location=location,
            attendees=attendees_list
        )

        if result.get("success"):
            message = f"Event '{summary}' created successfully! Link: {result.get('link', 'N/A')}"
        else:
            message = f"Failed to create event: {result.get('error', 'Unknown error')}"

        print(f"[ADA DEBUG] [GOOGLE] Create event result: {message}")
        return {"result": message}

    async def handle_google_delete_event(self, event_id):
        """Handle deleting a calendar event."""
        print(f"[ADA DEBUG] [GOOGLE] Deleting event: {event_id}")
        result = await self.agent.delete_calendar_event(event_id=event_id)

        if result.get("success"):
            message = f"Event deleted successfully."
        else:
            message = f"Failed to delete event: {result.get('error', 'Unknown error')}"

        return {"result": message}

    async def handle_google_read_spreadsheet(self, spreadsheet_id, range_name="Sheet1!A1:Z100"):
        """Handle reading from a spreadsheet."""
        print(f"[ADA DEBUG] [GOOGLE] Reading spreadsheet: {spreadsheet_id}")
        result = await self.agent.read_spreadsheet(
            spreadsheet_id=spreadsheet_id,
            range_name=range_name
        )

        if result.get("success"):
            data = result.get("data", [])
            rows = len(data)
            # Format as simple table for display
            if data:
                formatted = "\n".join([" | ".join(str(cell) for cell in row) for row in data[:20]])
                message = f"Read {rows} rows from spreadsheet:\n{formatted}"
                if rows > 20:
                    message += f"\n... and {rows - 20} more rows"
            else:
                message = "Spreadsheet is empty or range contains no data."
        else:
            message = f"Failed to read spreadsheet: {result.get('error', 'Unknown error')}"

        return {"result": message, "data": result.get("data", [])}

    async def handle_google_write_spreadsheet(self, spreadsheet_id, range_name, values):
        """Handle writing to a spreadsheet."""
        print(f"[ADA DEBUG] [GOOGLE] Writing to spreadsheet: {spreadsheet_id}")

        import json
        try:
            values_list = json.loads(values)
        except:
            values_list = [[values]]  # Wrap single value

        result = await self.agent.write_spreadsheet(
            spreadsheet_id=spreadsheet_id,
            range_name=range_name,
            values=values_list
        )

        if result.get("success"):
            message = f"Successfully updated {result.get('updated_cells', 'N/A')} cells."
        else:
            message = f"Failed to write to spreadsheet: {result.get('error', 'Unknown error')}"

        return {"result": message}

    async def handle_google_append_spreadsheet(self, spreadsheet_id, range_name, values):
        """Handle appending to a spreadsheet."""
        print(f"[ADA DEBUG] [GOOGLE] Appending to spreadsheet: {spreadsheet_id}")

        import json
        try:
            values_list = json.loads(values)
        except:
            values_list = [[values]]

        result = await self.agent.append_spreadsheet(
            spreadsheet_id=spreadsheet_id,
            range_name=range_name,
            values=values_list
        )

        if result.get("success"):
            message = "Data appended successfully to spreadsheet."
        else:
            message = f"Failed to append to spreadsheet: {result.get('error', 'Unknown error')}"

        return {"result": message}

    async def handle_google_create_spreadsheet(self, title, sheets=None):
        """Handle creating a new spreadsheet."""
        print(f"[ADA DEBUG] [GOOGLE] Creating spreadsheet: {title}")

        sheets_list = None
        if sheets:
            sheets_list = [s.strip() for s in sheets.split(",")]

        result = await self.agent.create_spreadsheet(
            title=title,
            sheets=sheets_list
        )

        if result.get("success"):
            message = f"Spreadsheet '{title}' created! URL: {result.get('url', 'N/A')}"
        else:
            message = f"Failed to create spreadsheet: {result.get('error', 'Unknown error')}"

        return {"result": message, "spreadsheet_id": result.get("spreadsheet_id")}

    async def handle_google_add_sheet(self, spreadsheet_id, title):
        """Handle adding a sheet."""
        print(f"[ADA DEBUG] [GOOGLE] Adding sheet: {title}")
        result = await self.agent.add_sheet(
            spreadsheet_id=spreadsheet_id,
            title=title
        )

        if result.get("success"):
            message = f"Sheet '{title}' added successfully! ID: {result.get('sheet_id')}"
        else:
            message = f"Failed to add sheet: {result.get('error', 'Unknown error')}"

        return {"result": message}

    async def handle_google_delete_sheet(self, spreadsheet_id, sheet_title):
        """Handle deleting a sheet."""
        print(f"[ADA DEBUG] [GOOGLE] Deleting sheet: {sheet_title}")
        result = await self.agent.delete_sheet(
            spreadsheet_id=spreadsheet_id,
            sheet_title=sheet_title
        )

        if result.get("success"):
            message = f"Sheet '{sheet_title}' deleted successfully."
        else:
            message = f"Failed to delete sheet: {result.get('error', 'Unknown error')}"

        return {"result": message}

    async def handle_google_list_drive_files(self, query=None, max_results=20, folder_id=None):
        """Handle listing Drive files."""
        print(f"[ADA DEBUG] [GOOGLE] Listing Drive files...")
        result = await self.agent.list_drive_files(
            query=query,
            max_results=max_results,
            folder_id=folder_id
        )

        if result.get("success"):
            files = result.get("files", [])
            if files:
                file_list = "\n".join([
                    f"- {f['name']} ({f.get('mimeType', 'unknown')})" for f in files
                ])
                message = f"Found {len(files)} files:\n{file_list}"
            else:
                message = "No files found in Drive."
        else:
            message = f"Failed to list files: {result.get('error', 'Unknown error')}"

        return {"result": message, "files": result.get("files", [])}

    async def handle_google_upload_to_drive(self, file_path, folder_id=None, file_name=None):
        """Handle uploading file to Drive."""
        print(f"[ADA DEBUG] [GOOGLE] Uploading to Drive: {file_path}")
        result = await self.agent.upload_to_drive(
            file_path=file_path,
            folder_id=folder_id,
            file_name=file_name
        )

        if result.get("success"):
            message = f"File uploaded successfully! Link: {result.get('link', 'N/A')}"
        else:
            message = f"Failed to upload file: {result.get('error', 'Unknown error')}"

        return {"result": message}

    async def handle_google_download_from_drive(self, file_id, destination_path):
        """Handle downloading file from Drive."""
        print(f"[ADA DEBUG] [GOOGLE] Downloading from Drive: {file_id}")
        result = await self.agent.download_from_drive(
            file_id=file_id,
            destination_path=destination_path
        )

        if result.get("success"):
            message = f"File downloaded to: {destination_path}"
        else:
            message = f"Failed to download file: {result.get('error', 'Unknown error')}"

        return {"result": message}

    async def handle_google_create_drive_folder(self, folder_name, parent_id=None):
        """Handle creating a Drive folder."""
        print(f"[ADA DEBUG] [GOOGLE] Creating Drive folder: {folder_name}")
        result = await self.agent.create_drive_folder(
            folder_name=folder_name,
            parent_id=parent_id
        )

        if result.get("success"):
            message = f"Folder '{folder_name}' created! Link: {result.get('link', 'N/A')}"
        else:
            message = f"Failed to create folder: {result.get('error', 'Unknown error')}"

        return {"result": message, "folder_id": result.get("folder_id")}

    async def handle_google_send_email(self, to, subject, body, cc=None, bcc=None):
        """Handle sending an email."""
        print(f"[ADA DEBUG] [GOOGLE] Sending email to: {to}")
        result = await self.agent.send_email(
            to=to,
            subject=subject,
            body=body,
            cc=cc,
            bcc=bcc
        )

        if result.get("success"):
            message = f"Email sent successfully to {to}!"
        else:
            message = f"Failed to send email: {result.get('error', 'Unknown error')}"

        return {"result": message}

    async def handle_google_list_emails(self, max_results=10, query=None):
        """Handle listing emails."""
        print(f"[ADA DEBUG] [GOOGLE] Listing emails...")
        result = await self.agent.list_emails(
            max_results=max_results,
            query=query
        )

        if result.get("success"):
            emails = result.get("emails", [])
            if emails:
                email_list = "\n".join([
                    f"- From: {e['from'][:30]}... Subject: {e['subject'][:40]}..." for e in emails
                ])
                message = f"Found {len(emails)} emails:\n{email_list}"
            else:
                message = "No emails found."
        else:
            message = f"Failed to list emails: {result.get('error', 'Unknown error')}"

        return {"result": message, "emails": result.get("emails", [])}

    async def handle_google_read_email(self, message_id):
        """Handle reading a specific email."""
        print(f"[ADA DEBUG] [GOOGLE] Reading email: {message_id}")
        result = await self.agent.read_email(message_id=message_id)

        if result.get("success"):
            message = f"From: {result.get('from')}\nSubject: {result.get('subject')}\nDate: {result.get('date')}\n\n{result.get('body', result.get('snippet', ''))}"
        else:
            message = f"Failed to read email: {result.get('error', 'Unknown error')}"

        return {"result": message}

    async def handle_google_create_document(self, title, content=None):
        """Handle creating a Google Document."""
        print(f"[ADA DEBUG] [GOOGLE] Creating document: {title}")
        result = await self.agent.create_document(
            title=title,
            content=content
        )

        if result.get("success"):
            message = f"Document '{title}' created! URL: {result.get('url', 'N/A')}"
        else:
            message = f"Failed to create document: {result.get('error', 'Unknown error')}"

        return {"result": message, "document_id": result.get("document_id")}

    async def handle_google_read_document(self, document_id):
        """Handle reading a Google Document."""
        print(f"[ADA DEBUG] [GOOGLE] Reading document: {document_id}")
        result = await self.agent.read_document(document_id=document_id)

        if result.get("success"):
            content = result.get("content", "")
            if len(content) > 2000:
                content = content[:2000] + "... (truncated)"
            message = f"Document: {result.get('title')}\n\n{content}"
        else:
            message = f"Failed to read document: {result.get('error', 'Unknown error')}"

        return {"result": message}

    async def handle_google_append_document(self, document_id, content):
        """Handle appending to a Google Document."""
        print(f"[ADA DEBUG] [GOOGLE] Appending to document: {document_id}")
        result = await self.agent.append_to_document(
            document_id=document_id,
            content=content
        )

        if result.get("success"):
            message = f"Content appended successfully! URL: {result.get('url', 'N/A')}"
        else:
            message = f"Failed to append to document: {result.get('error', 'Unknown error')}"

        return {"result": message}

    async def handle_google_create_form(self, title, document_title=None):
        """Handle creating a Google Form."""
        print(f"[ADA DEBUG] [GOOGLE] Creating form: {title}")
        result = await self.agent.create_form(title, document_title)

        if result.get("success"):
            msg = f"Form '{title}' berhasil dibuat!\nURL: {result.get('url')}\nEdit: {result.get('edit_url')}"
        else:
            msg = f"Gagal membuat form: {result.get('error')}"

        return {"result": msg}

    async def handle_google_create_presentation(self, title):
        """Handle creating a Google Slides presentation."""
        print(f"[ADA DEBUG] [GOOGLE] Creating presentation: {title}")
        result = await self.agent.create_presentation(title)

        if result.get("success"):
            msg = f"Presentasi '{title}' berhasil dibuat!\nURL: {result.get('edit_url')}"
        else:
            msg = f"Gagal membuat presentasi: {result.get('error')}"

        return {"result": msg}
