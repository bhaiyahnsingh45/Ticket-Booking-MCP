# Bhaiya & Company — Voice Ticket Booking

A real-time speech-to-speech train ticket booking app powered by **Amazon Nova Sonic** and custom **MCP servers**.

Users speak in **English, Hindi, French, or German** to search trains, book tickets, process payment, and receive an email confirmation — without typing a single character.

---

## Architecture

```
┌─────────────┐    WebSocket     ┌─────────────────────────────┐
│   React     │ ←──────────────→ │  FastAPI Backend            │
│  Frontend   │  audio + JSON    │  (nova_sonic.py + main.py)  │
└─────────────┘                  └────────────┬────────────────┘
                                              │ MCP SSE
                              ┌───────────────┴───────────────┐
                              │                               │
                   ┌──────────┴──────────┐   ┌───────────────┴──────────┐
                   │ ticket_booking MCP  │   │      gmail MCP           │
                   │   (port 8001)       │   │    (port 8002)           │
                   │                     │   │                          │
                   │ • search_trains     │   │ • send_booking_email     │
                   │ • book_ticket       │   │ • send_test_email        │
                   │ • process_payment   │   └──────────────────────────┘
                   │ • get_confirmation  │
                   └─────────────────────┘
                              │
                   ┌──────────┴──────────┐
                   │  AWS Bedrock        │
                   │  Nova Sonic         │
                   │  amazon.nova-sonic- │
                   │  v1:0               │
                   └─────────────────────┘
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- `pip install uv` (then use `uv` for MCP servers)
- AWS account with Bedrock access (Nova Sonic model enabled in `us-east-1`)
- Google Cloud project with Gmail API enabled

---

### 1. Setup MCP Servers

```bash
# Ticket Booking MCP
cd mcp/ticket_booking
uv init
uv add fastmcp pydantic
# Run on port 8001:
uv run fastmcp run booking_mcp_main.py --transport sse --port 8001
```

```bash
# Gmail MCP
cd mcp/gmail
uv init
uv add fastmcp google-api-python-client google-auth-oauthlib google-auth-httplib2
# Place credentials.json from Google Cloud Console here
# Run on port 8002:
uv run fastmcp run gmail_mcp_main.py --transport sse --port 8002
```

#### Gmail API Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project → Enable **Gmail API**
3. Create OAuth credentials → **Desktop app** type → Download `credentials.json`
4. Place `credentials.json` in `mcp/gmail/`
5. First run will open a browser for OAuth consent → generates `token.json`

---

### 2. Setup Backend

```bash
cd backend
cp .env.example .env
# Fill in your AWS credentials in .env

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**`backend/.env`:**
```
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
MCP_BOOKING_URL=http://localhost:8001/sse
MCP_GMAIL_URL=http://localhost:8002/sse
```

---

### 3. Setup Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

---

### Run Order (4 terminals)

```bash
# Terminal 1 — Ticket Booking MCP
cd mcp/ticket_booking && uv run fastmcp run booking_mcp_main.py --transport sse --port 8001

# Terminal 2 — Gmail MCP
cd mcp/gmail && uv run fastmcp run gmail_mcp_main.py --transport sse --port 8002

# Terminal 3 — Backend
cd backend && uvicorn main:app --reload --port 8000

# Terminal 4 — Frontend
cd frontend && npm run dev
```

---

## Voice Commands (Examples)

| Language | Example |
|----------|---------|
| English | *"I want to go from Delhi to Mumbai on 15 March for 2 people"* |
| Hindi | *"मैं दिल्ली से मुंबई जाना चाहता हूँ, 15 मार्च को, 2 लोग"* |
| French | *"Je veux aller de Delhi à Mumbai le 15 mars pour 2 personnes"* |
| German | *"Ich möchte am 15. März mit 2 Personen von Delhi nach Mumbai reisen"* |

If you provide all required info at once (from, to, date, passengers) → trains are searched immediately.
If any field is missing → the AI asks a follow-up question in the same language.

---

## Available Train Routes

- Delhi ↔ Mumbai (Rajdhani Express, Duronto Express)
- Delhi ↔ Lucknow (Shatabdi, Lucknow Mail)
- Delhi ↔ Kolkata (Poorva Express)
- Delhi ↔ Jaipur (Ajmer Shatabdi)
- Delhi ↔ Bangalore (Rajdhani Express)
- Mumbai → Delhi (Mumbai Rajdhani)

---

## Voice Languages & Voices

| Language | Code | Voice |
|----------|------|-------|
| English (US) | en | tiffany |
| Hindi | hi | kiara |
| French | fr | ambre |
| German | de | tina |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Voice | Amazon Nova Sonic (Bedrock) |
| Tool Protocol | MCP (FastMCP) |
| Backend | Python FastAPI + WebSocket |
| Frontend | React 19 + Vite + Tailwind CSS |
| Animations | Framer Motion |
| Icons | Lucide React |
| Email | Gmail API (OAuth2) |
