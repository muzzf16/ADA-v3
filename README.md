
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11-blue?logo=python)
![React](https://img.shields.io/badge/React-18.2-61DAFB?logo=react)
![Electron](https://img.shields.io/badge/Electron-28-47848F?logo=electron)
![Gemini](https://img.shields.io/badge/Google%20Gemini-Native%20Audio-4285F4?logo=google)
![License](https://img.shields.io/badge/License-MIT-green)

> **K.E.N.E.S**

KENES (K.E.N.E.S) is a sophisticated AI Personal Assistant for multimodal interaction. It combines Google's Gemini 2.5 Native Audio with computer vision, rich local system integration, and office automation to create a truly agentic experience.

---

## 🌟 Capabilities at a Glance

| Feature | Description |
|---------|-------------|
| **🗣️ Natural Voice** | Real-time conversation with specialized tools via Gemini 2.5 Native Audio |
| **🏢 Google Workspace** | Full integration with Gmail, Calendar, Sheets, Drive, Docs, Slides, and Forms |
| **💻 Local PC Control** | Create/read files, open apps, search file system, and list folders |
| **💬 Communication** | Send WhatsApp messages, trigger Webhooks, and send Yahoo emails |
| **🤖 N8N Automation** | Connect to N8N MCP to execute complex workflows |
| **🖨️ Document Printing** | Direct printing of files and text to local printers |
| **🌐 Web Agent** | Autonomous browser automation with Playwright |
| **🖐️ Interactive UI** | "Minority Report" style gesture control and face authentication |
| **🏠 Smart Home** | Voice control for TP-Link Kasa devices |

---

## 🚀 Features in Depth

### 🏢 Google Workspace Integration
KENES acts as your office manager. Authenticate once, and manage your cloud life via voice or text.
- **Gmail**: Read unread emails, send new emails, search inbox.
- **Calendar**: Schedule meetings, list events, delete appointments.
- **Sheets**: Read data, append rows, create new spreadsheets, add sheets.
- **Drive**: List files, upload local files, download to PC, create folders.
- **Office**: Create Docs, Slides, and Forms instantly.

> **Setup**: See `backend/GOOGLE_WORKSPACE_SETUP.md` for API key and credential configuration.

### 💻 Local System Control
KENES is a power user on your local machine.
- **File Management**: "Create a file called notes.txt on Desktop", "Read the project report", "Search for 'invoice' in Documents".
- **App Control**: "Open VS Code", "Open Calculator", "Launch Chrome".
- **Printing**: "Print this PDF to the Canon printer", "List available printers".

### 💬 Communication & Automation
- **WhatsApp**: Send messages to Indonesian numbers (Requires local dashboard API).
- **Webhooks**: Trigger external services (e.g., Discord, Slack, Zapier) via custom webhooks.
- **N8N**: Execute and search for N8N workflows directly from chat.
- **Yahoo Mail**: Alternative email support for Yahoo users.

---

## 🏗️ Architecture Overview

```mermaid
graph TB
    subgraph Frontend ["Frontend (Electron + React)"]
        UI[React UI]
        GESTURE[MediaPipe Gestures]
        SOCKET_C[Socket.IO Client]
    end
    
    subgraph Backend ["Backend (Python 3.11 + FastAPI)"]
        SERVER[server.py]
        KENES[ada.py (Gemini 2.5)]
        
        subgraph Agents
            WEB[Web Agent]
            G_SUITE[Google Workspace Agent]
            LOCAL[Local PC Agent]
            MSG[WhatsApp/Webhook Agent]
            PRINTER[Printer Agent]
            CAD[CAD Agent]
        end
    end
    
    UI --> SOCKET_C
    SOCKET_C <--> SERVER
    SERVER --> KENES
    KENES --> Agents
```

---

## 🛠️ Installation Requirements

### 1. Python Environment
Create a single Python 3.11 environment:

```bash
conda create -n ada_v2 python=3.11
conda activate ada_v2
pip install -r requirements.txt
playwright install chromium
```

### 2. Frontend Setup
```bash
npm install
# To run:
npm run dev
```

### 3. Key Configuration
Create a `.env` file in the root directory:

```env
# Required
GEMINI_API_KEY=your_gemini_key_here

# Optional: For Yahoo Mail
YAHOO_EMAIL=your_email@yahoo.com
YAHOO_PASSWORD=your_app_password

# Optional: For Webhooks/WhatsApp
# (See specific agent instructions)
```

### 4. Google Workspace Credentials
To enable Calendar, Drive, Gmail, etc:
1. Follow the guide in `backend/GOOGLE_WORKSPACE_SETUP.md`.
2. Place `credentials.json` in the `backend/` folder.
3. Authenticate by saying "Authenticate with Google".

---

## ⚙️ Configuration (`settings.json`)

| Key | Description |
| :--- | :--- |
| `face_auth_enabled` | If `true`, requires face recognition to access KENES. |
| `tool_permissions` | JSON object to granularly allow/deny tools (e.g. `run_web_agent`, `write_file`). |

---

## ❓ Troubleshooting

### Google Workspace Issues
- **"credentials.json not found"**: Ensure the file is in `backend/`.
- **"Token expired"**: Delete `backend/google_token.json` and re-authenticate.

### Camera/Microphone
- Ensure permissions are granted to your terminal/VS Code on macOS.
- Windows usually works out of the box.

---

## 📄 License

This project is licensed under the **MIT License**.
