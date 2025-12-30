"""
Google Workspace Agent for A.D.A V2
Integrates Google Calendar, Sheets, Drive, Gmail, and Docs
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

# Google API Libraries
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import io

# Scopes for all Google Workspace services
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/forms.body',
    'https://www.googleapis.com/auth/presentations',
]

class GoogleWorkspaceAgent:
    """
    Agent for interacting with Google Workspace services.
    Supports: Calendar, Sheets, Drive, Gmail, Docs
    """
    
    def __init__(self, credentials_path: str = None, token_path: str = None):
        """
        Initialize the Google Workspace Agent.
        
        Args:
            credentials_path: Path to OAuth credentials.json from Google Cloud Console
            token_path: Path to store/load user tokens
        """
        self.backend_dir = Path(__file__).parent
        self.credentials_path = credentials_path or str(self.backend_dir / "credentials.json")
        self.token_path = token_path or str(self.backend_dir / "google_token.json")
        
        self.creds = None
        self._calendar_service = None
        self._sheets_service = None
        self._drive_service = None
        self._gmail_service = None
        self._docs_service = None
        self._forms_service = None
        self._slides_service = None
        
        # Try to load existing credentials
        self._load_credentials()
    
    def _load_credentials(self):
        """Load credentials from token file if exists."""
        if os.path.exists(self.token_path):
            try:
                self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
                print("[GOOGLE] Loaded existing credentials from token file.")
            except Exception as e:
                print(f"[GOOGLE] Failed to load token: {e}")
                self.creds = None
        
        # Refresh if expired
        if self.creds and self.creds.expired and self.creds.refresh_token:
            try:
                self.creds.refresh(Request())
                self._save_credentials()
                print("[GOOGLE] Refreshed expired credentials.")
            except Exception as e:
                print(f"[GOOGLE] Failed to refresh credentials: {e}")
                self.creds = None
    
    def _save_credentials(self):
        """Save credentials to token file."""
        if self.creds:
            with open(self.token_path, 'w') as token:
                token.write(self.creds.to_json())
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return self.creds is not None and self.creds.valid
    
    async def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with Google. Opens browser for OAuth flow.
        
        Returns:
            Dict with status and message
        """
        if not os.path.exists(self.credentials_path):
            return {
                "success": False,
                "error": f"credentials.json not found at {self.credentials_path}. "
                         "Please download it from Google Cloud Console."
            }
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, SCOPES
            )
            # Run the OAuth flow in a separate thread to not block
            self.creds = await asyncio.to_thread(
                flow.run_local_server, port=0
            )
            self._save_credentials()
            
            return {
                "success": True,
                "message": "Successfully authenticated with Google Workspace!"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Authentication failed: {str(e)}"
            }
    
    def _get_calendar_service(self):
        """Get or create Calendar service."""
        if not self._calendar_service and self.creds:
            self._calendar_service = build('calendar', 'v3', credentials=self.creds)
        return self._calendar_service
    
    def _get_sheets_service(self):
        """Get or create Sheets service."""
        if not self._sheets_service and self.creds:
            self._sheets_service = build('sheets', 'v4', credentials=self.creds)
        return self._sheets_service
    
    def _get_drive_service(self):
        """Get or create Drive service."""
        if not self._drive_service and self.creds:
            self._drive_service = build('drive', 'v3', credentials=self.creds)
        return self._drive_service
    
    def _get_gmail_service(self):
        """Get or create Gmail service."""
        if not self._gmail_service and self.creds:
            self._gmail_service = build('gmail', 'v1', credentials=self.creds)
        return self._gmail_service
    
    def _get_docs_service(self):
        """Get or create Docs service."""
        if not self._docs_service and self.creds:
            self._docs_service = build('docs', 'v1', credentials=self.creds)
        return self._docs_service

    def _get_forms_service(self):
        """Get or create Forms service."""
        if not self._forms_service and self.creds:
            self._forms_service = build('forms', 'v1', credentials=self.creds)
        return self._forms_service

    def _get_slides_service(self):
        """Get or create Slides service."""
        if not self._slides_service and self.creds:
            self._slides_service = build('slides', 'v1', credentials=self.creds)
        return self._slides_service

    # ==================== CALENDAR FUNCTIONS ====================
    
    async def list_calendar_events(
        self, 
        max_results: int = 10, 
        time_min: str = None,
        time_max: str = None,
        calendar_id: str = 'primary'
    ) -> Dict[str, Any]:
        """
        List upcoming calendar events.
        
        Args:
            max_results: Maximum number of events to return
            time_min: Start time (ISO format), defaults to now
            time_max: End time (ISO format), optional
            calendar_id: Calendar ID, defaults to 'primary'
        
        Returns:
            Dict with events list or error
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated. Please run authenticate first."}
        
        try:
            service = self._get_calendar_service()
            
            if not time_min:
                time_min = datetime.utcnow().isoformat() + 'Z'
            
            events_result = await asyncio.to_thread(
                lambda: service.events().list(
                    calendarId=calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
            )
            
            events = events_result.get('items', [])
            
            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                formatted_events.append({
                    'id': event['id'],
                    'summary': event.get('summary', 'No title'),
                    'start': start,
                    'end': event['end'].get('dateTime', event['end'].get('date')),
                    'location': event.get('location', ''),
                    'description': event.get('description', '')
                })
            
            return {
                "success": True,
                "events": formatted_events,
                "count": len(formatted_events)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def create_calendar_event(
        self,
        summary: str,
        start_time: str,
        end_time: str = None,
        description: str = "",
        location: str = "",
        attendees: List[str] = None,
        calendar_id: str = 'primary'
    ) -> Dict[str, Any]:
        """
        Create a new calendar event.
        
        Args:
            summary: Event title
            start_time: Start time (ISO format or natural language like "tomorrow 10am")
            end_time: End time (ISO format), defaults to 1 hour after start
            description: Event description
            location: Event location
            attendees: List of email addresses to invite
            calendar_id: Calendar ID, defaults to 'primary'
        
        Returns:
            Dict with created event info or error
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated. Please run authenticate first."}
        
        try:
            service = self._get_calendar_service()
            
            # Parse start_time if it's not in ISO format
            try:
                start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except:
                # Try to parse natural language (basic support)
                start_dt = self._parse_natural_time(start_time)
            
            # Calculate end time if not provided (default 1 hour)
            if end_time:
                try:
                    end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
                except:
                    end_dt = start_dt + timedelta(hours=1)
            else:
                end_dt = start_dt + timedelta(hours=1)
            
            event = {
                'summary': summary,
                'location': location,
                'description': description,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': 'Asia/Jakarta',  # Default timezone
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': 'Asia/Jakarta',
                },
            }
            
            if attendees:
                event['attendees'] = [{'email': email} for email in attendees]
            
            created_event = await asyncio.to_thread(
                lambda: service.events().insert(
                    calendarId=calendar_id,
                    body=event
                ).execute()
            )
            
            return {
                "success": True,
                "event_id": created_event['id'],
                "link": created_event.get('htmlLink'),
                "message": f"Event '{summary}' created successfully!"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def delete_calendar_event(
        self,
        event_id: str,
        calendar_id: str = 'primary'
    ) -> Dict[str, Any]:
        """Delete a calendar event."""
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated."}
        
        try:
            service = self._get_calendar_service()
            await asyncio.to_thread(
                lambda: service.events().delete(
                    calendarId=calendar_id,
                    eventId=event_id
                ).execute()
            )
            return {"success": True, "message": f"Event {event_id} deleted."}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _parse_natural_time(self, time_str: str) -> datetime:
        """Basic natural language time parsing."""
        time_str = time_str.lower().strip()
        now = datetime.now()
        
        if 'tomorrow' in time_str:
            base = now + timedelta(days=1)
        elif 'today' in time_str:
            base = now
        else:
            base = now
        
        # Extract time if mentioned (basic parsing)
        import re
        time_match = re.search(r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?', time_str)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2) or 0)
            ampm = time_match.group(3)
            
            if ampm == 'pm' and hour < 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            
            base = base.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        return base

    # ==================== SHEETS FUNCTIONS ====================
    
    async def read_spreadsheet(
        self,
        spreadsheet_id: str,
        range_name: str = 'Sheet1!A1:Z100'
    ) -> Dict[str, Any]:
        """
        Read data from a Google Spreadsheet.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet (from URL)
            range_name: The range to read (e.g., 'Sheet1!A1:D10')
        
        Returns:
            Dict with data or error
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated."}
        
        try:
            service = self._get_sheets_service()
            result = await asyncio.to_thread(
                lambda: service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range=range_name
                ).execute()
            )
            
            values = result.get('values', [])
            return {
                "success": True,
                "data": values,
                "rows": len(values),
                "range": result.get('range')
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def write_spreadsheet(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]],
        value_input_option: str = 'USER_ENTERED'
    ) -> Dict[str, Any]:
        """
        Write data to a Google Spreadsheet.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            range_name: The range to write to (e.g., 'Sheet1!A1')
            values: 2D list of values to write
            value_input_option: How to interpret the data ('RAW' or 'USER_ENTERED')
        
        Returns:
            Dict with result or error
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated."}
        
        try:
            service = self._get_sheets_service()
            body = {'values': values}
            
            result = await asyncio.to_thread(
                lambda: service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption=value_input_option,
                    body=body
                ).execute()
            )
            
            return {
                "success": True,
                "updated_cells": result.get('updatedCells'),
                "updated_range": result.get('updatedRange'),
                "message": f"Updated {result.get('updatedCells')} cells."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def append_spreadsheet(
        self,
        spreadsheet_id: str,
        range_name: str,
        values: List[List[Any]]
    ) -> Dict[str, Any]:
        """
        Append data to a Google Spreadsheet.
        
        Args:
            spreadsheet_id: The ID of the spreadsheet
            range_name: The range to append to (e.g., 'Sheet1!A:D')
            values: 2D list of values to append
        
        Returns:
            Dict with result or error
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated."}
        
        try:
            service = self._get_sheets_service()
            body = {'values': values}
            
            result = await asyncio.to_thread(
                lambda: service.spreadsheets().values().append(
                    spreadsheetId=spreadsheet_id,
                    range=range_name,
                    valueInputOption='USER_ENTERED',
                    insertDataOption='INSERT_ROWS',
                    body=body
                ).execute()
            )
            
            return {
                "success": True,
                "updated_range": result.get('updates', {}).get('updatedRange'),
                "message": "Data appended successfully."
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def create_spreadsheet(
        self,
        title: str,
        sheets: List[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new Google Spreadsheet.
        
        Args:
            title: Title of the new spreadsheet
            sheets: List of sheet names to create (optional)
        
        Returns:
            Dict with spreadsheet info or error
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated."}
        
        try:
            service = self._get_sheets_service()
            
            spreadsheet_body = {
                'properties': {'title': title}
            }
            
            if sheets:
                spreadsheet_body['sheets'] = [
                    {'properties': {'title': sheet_name}}
                    for sheet_name in sheets
                ]
            
            spreadsheet = await asyncio.to_thread(
                lambda: service.spreadsheets().create(body=spreadsheet_body).execute()
            )
            
            return {
                "success": True,
                "spreadsheet_id": spreadsheet['spreadsheetId'],
                "url": spreadsheet['spreadsheetUrl'],
                "message": f"Spreadsheet '{title}' created successfully!"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== DRIVE FUNCTIONS ====================
    
    async def list_drive_files(
        self,
        query: str = None,
        max_results: int = 20,
        folder_id: str = None
    ) -> Dict[str, Any]:
        """
        List files in Google Drive.
        
        Args:
            query: Search query (e.g., "name contains 'report'")
            max_results: Maximum number of files to return
            folder_id: ID of folder to list files from
        
        Returns:
            Dict with files list or error
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated."}
        
        try:
            service = self._get_drive_service()
            
            q_parts = []
            if folder_id:
                q_parts.append(f"'{folder_id}' in parents")
            if query:
                q_parts.append(query)
            
            q = ' and '.join(q_parts) if q_parts else None
            
            results = await asyncio.to_thread(
                lambda: service.files().list(
                    q=q,
                    pageSize=max_results,
                    fields="files(id, name, mimeType, size, modifiedTime, webViewLink)"
                ).execute()
            )
            
            files = results.get('files', [])
            return {
                "success": True,
                "files": files,
                "count": len(files)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def upload_to_drive(
        self,
        file_path: str,
        folder_id: str = None,
        file_name: str = None
    ) -> Dict[str, Any]:
        """
        Upload a file to Google Drive.
        
        Args:
            file_path: Local path to the file to upload
            folder_id: ID of the folder to upload to (optional)
            file_name: Name for the file in Drive (optional, uses original name)
        
        Returns:
            Dict with uploaded file info or error
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated."}
        
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}
        
        try:
            service = self._get_drive_service()
            
            file_metadata = {
                'name': file_name or os.path.basename(file_path)
            }
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            # Determine MIME type
            import mimetypes
            mime_type, _ = mimetypes.guess_type(file_path)
            mime_type = mime_type or 'application/octet-stream'
            
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            
            file = await asyncio.to_thread(
                lambda: service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, webViewLink'
                ).execute()
            )
            
            return {
                "success": True,
                "file_id": file['id'],
                "name": file['name'],
                "link": file.get('webViewLink'),
                "message": f"File '{file['name']}' uploaded successfully!"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def download_from_drive(
        self,
        file_id: str,
        destination_path: str
    ) -> Dict[str, Any]:
        """
        Download a file from Google Drive.
        
        Args:
            file_id: ID of the file to download
            destination_path: Local path to save the file
        
        Returns:
            Dict with download result or error
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated."}
        
        try:
            service = self._get_drive_service()
            
            request = service.files().get_media(fileId=file_id)
            
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                status, done = await asyncio.to_thread(downloader.next_chunk)
            
            # Write to file
            os.makedirs(os.path.dirname(destination_path) or '.', exist_ok=True)
            with open(destination_path, 'wb') as f:
                f.write(fh.getvalue())
            
            return {
                "success": True,
                "path": destination_path,
                "message": f"File downloaded to {destination_path}"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def create_drive_folder(
        self,
        folder_name: str,
        parent_id: str = None
    ) -> Dict[str, Any]:
        """
        Create a folder in Google Drive.
        
        Args:
            folder_name: Name of the new folder
            parent_id: ID of parent folder (optional)
        
        Returns:
            Dict with folder info or error
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated."}
        
        try:
            service = self._get_drive_service()
            
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            folder = await asyncio.to_thread(
                lambda: service.files().create(
                    body=file_metadata,
                    fields='id, name, webViewLink'
                ).execute()
            )
            
            return {
                "success": True,
                "folder_id": folder['id'],
                "name": folder['name'],
                "link": folder.get('webViewLink'),
                "message": f"Folder '{folder_name}' created successfully!"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== GMAIL FUNCTIONS ====================
    
    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        cc: str = None,
        bcc: str = None,
        is_html: bool = False
    ) -> Dict[str, Any]:
        """
        Send an email via Gmail.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body content
            cc: CC recipients (comma-separated)
            bcc: BCC recipients (comma-separated)
            is_html: Whether body is HTML content
        
        Returns:
            Dict with send result or error
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated."}
        
        try:
            import base64
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            service = self._get_gmail_service()
            
            message = MIMEMultipart()
            message['to'] = to
            message['subject'] = subject
            
            if cc:
                message['cc'] = cc
            if bcc:
                message['bcc'] = bcc
            
            mime_type = 'html' if is_html else 'plain'
            message.attach(MIMEText(body, mime_type))
            
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            sent_message = await asyncio.to_thread(
                lambda: service.users().messages().send(
                    userId='me',
                    body={'raw': raw_message}
                ).execute()
            )
            
            return {
                "success": True,
                "message_id": sent_message['id'],
                "message": f"Email sent to {to} successfully!"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def list_emails(
        self,
        max_results: int = 10,
        query: str = None,
        label_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        List emails from Gmail.
        
        Args:
            max_results: Maximum number of emails to return
            query: Gmail search query (e.g., "is:unread")
            label_ids: List of label IDs to filter by
        
        Returns:
            Dict with emails list or error
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated."}
        
        try:
            service = self._get_gmail_service()
            
            results = await asyncio.to_thread(
                lambda: service.users().messages().list(
                    userId='me',
                    maxResults=max_results,
                    q=query,
                    labelIds=label_ids
                ).execute()
            )
            
            messages = results.get('messages', [])
            
            for msg in messages[:max_results]:
                msg_detail = await asyncio.to_thread(
                    lambda m=msg: service.users().messages().get(
                        userId='me',
                        id=m['id'],
                        format='metadata',
                        metadataHeaders=['From', 'Subject', 'Date']
                    ).execute()
                )
                
                headers = {h['name']: h['value'] for h in msg_detail.get('payload', {}).get('headers', [])}
                emails.append({
                    'id': msg['id'],
                    'from': headers.get('From', ''),
                    'subject': headers.get('Subject', ''),
                    'date': headers.get('Date', ''),
                    'snippet': msg_detail.get('snippet', '')
                })
            
            return {
                "success": True,
                "emails": emails,
                "count": len(emails)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def read_email(self, message_id: str) -> Dict[str, Any]:
        """
        Read a specific email by ID.
        
        Args:
            message_id: ID of the email to read
        
        Returns:
            Dict with email content or error
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated."}
        
        try:
            service = self._get_gmail_service()
            
            message = await asyncio.to_thread(
                lambda: service.users().messages().get(
                    userId='me',
                    id=message_id,
                    format='full'
                ).execute()
            )
            
            headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}
            
            # Extract body
            body = ""
            payload = message.get('payload', {})
            
            if 'body' in payload and payload['body'].get('data'):
                import base64
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
            elif 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain' and part.get('body', {}).get('data'):
                        import base64
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
            
            return {
                "success": True,
                "id": message_id,
                "from": headers.get('From', ''),
                "to": headers.get('To', ''),
                "subject": headers.get('Subject', ''),
                "date": headers.get('Date', ''),
                "body": body,
                "snippet": message.get('snippet', '')
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== DOCS FUNCTIONS ====================
    
    async def create_document(
        self,
        title: str,
        content: str = None
    ) -> Dict[str, Any]:
        """
        Create a new Google Document.
        
        Args:
            title: Document title
            content: Initial content to add (optional)
        
        Returns:
            Dict with document info or error
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated."}
        
        try:
            service = self._get_docs_service()
            
            document = await asyncio.to_thread(
                lambda: service.documents().create(
                    body={'title': title}
                ).execute()
            )
            
            doc_id = document['documentId']
            
            # Add content if provided
            if content:
                requests = [
                    {
                        'insertText': {
                            'location': {'index': 1},
                            'text': content
                        }
                    }
                ]
                
                await asyncio.to_thread(
                    lambda: service.documents().batchUpdate(
                        documentId=doc_id,
                        body={'requests': requests}
                    ).execute()
                )
            
            return {
                "success": True,
                "document_id": doc_id,
                "title": title,
                "url": f"https://docs.google.com/document/d/{doc_id}/edit",
                "message": f"Document '{title}' created successfully!"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def read_document(self, document_id: str) -> Dict[str, Any]:
        """
        Read content from a Google Document.
        
        Args:
            document_id: ID of the document to read
        
        Returns:
            Dict with document content or error
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated."}
        
        try:
            service = self._get_docs_service()
            
            document = await asyncio.to_thread(
                lambda: service.documents().get(documentId=document_id).execute()
            )
            
            # Extract text content
            content = ""
            for element in document.get('body', {}).get('content', []):
                if 'paragraph' in element:
                    for el in element['paragraph'].get('elements', []):
                        if 'textRun' in el:
                            content += el['textRun'].get('content', '')
            
            return {
                "success": True,
                "document_id": document_id,
                "title": document.get('title', ''),
                "content": content,
                "url": f"https://docs.google.com/document/d/{document_id}/edit"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def append_to_document(
        self,
        document_id: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Append text to the end of a Google Document.
        
        Args:
            document_id: ID of the document
            content: Text content to append
        
        Returns:
            Dict with result or error
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated."}
        
        try:
            service = self._get_docs_service()
            
            # Get current document to find end index
            document = await asyncio.to_thread(
                lambda: service.documents().get(documentId=document_id).execute()
            )
            
            # Find the end index
            end_index = document['body']['content'][-1]['endIndex'] - 1
            
            requests = [
                {
                    'insertText': {
                        'location': {'index': end_index},
                        'text': content
                    }
                }
            ]
            
            await asyncio.to_thread(
                lambda: service.documents().batchUpdate(
                    documentId=document_id,
                    body={'requests': requests}
                ).execute()
            )
            
            return {
                "success": True,
                "message": "Content appended successfully!",
                "url": f"https://docs.google.com/document/d/{document_id}/edit"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}



    # ==================== FORMS FUNCTIONS ====================
    
    def _get_forms_service(self):
        """Get or create Google Forms service."""
        if not self._forms_service:
            if not self.creds:
                self._load_credentials()
            if self.creds:
                self._forms_service = build('forms', 'v1', credentials=self.creds)
        return self._forms_service

    async def create_form(self, title: str, document_title: str = None) -> Dict[str, Any]:
        """
        Create a new Google Form.
        
        Args:
            title: Form title
            document_title: Filename in Drive (optional, defaults to title)
            
        Returns:
            Dict with form info (id, url, responderUri) or error
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated."}
            
        try:
            service = self._get_forms_service()
            
            form_body = {
                "info": {
                    "title": title,
                    "documentTitle": document_title or title
                }
            }
            
            form = await asyncio.to_thread(
                lambda: service.forms().create(body=form_body).execute()
            )
            
            return {
                "success": True,
                "form_id": form["formId"],
                "title": form["info"]["title"],
                "url": form["responderUri"],
                "edit_url": f"https://docs.google.com/forms/d/{form['formId']}/edit",
                "message": f"Form '{title}' created successfully!"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ==================== SLIDES FUNCTIONS ====================

    def _get_slides_service(self):
        """Get or create Google Slides service."""
        if not self._slides_service:
            if not self.creds:
                self._load_credentials()
            if self.creds:
                self._slides_service = build('slides', 'v1', credentials=self.creds)
        return self._slides_service

    async def create_presentation(self, title: str) -> Dict[str, Any]:
        """
        Create a new Google Slide Presentation.
        
        Args:
            title: Presentation title
            
        Returns:
            Dict with presentation info (id, url) or error
        """
        if not self.is_authenticated():
            return {"success": False, "error": "Not authenticated."}
            
        try:
            service = self._get_slides_service()
            
            presentation = await asyncio.to_thread(
                lambda: service.presentations().create(
                    body={'title': title}
                ).execute()
            )
            
            presentation_id = presentation.get('presentationId')
            
            return {
                "success": True,
                "presentation_id": presentation_id,
                "title": presentation.get('title'),
                "url": f"https://docs.google.com/presentation/d/{presentation_id}/embed?start=false&loop=false&delayms=3000",
                "edit_url": f"https://docs.google.com/presentation/d/{presentation_id}/edit",
                "message": f"Presentation '{title}' created successfully!"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

# Singleton instance
_workspace_agent = None

def get_workspace_agent() -> GoogleWorkspaceAgent:
    """Get or create the singleton GoogleWorkspaceAgent instance."""
    global _workspace_agent
    if _workspace_agent is None:
        _workspace_agent = GoogleWorkspaceAgent()
    return _workspace_agent
