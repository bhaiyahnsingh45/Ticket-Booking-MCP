# Ticket-Booking-MCP

An MCP (Model Context Protocol) server that connects Claude to a local SQLite database, providing a complete train ticket booking system — search trains, book tickets, check PNR status, cancel bookings, and more — all through natural language.

Built with [FastMCP](https://github.com/jlowin/fastmcp) and designed to work with [Claude Code](https://docs.anthropic.com/en/docs/claude-code).

## Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

> **Note:** No external database setup required — the server uses SQLite and auto-creates the database on first run.

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/Ticket-Booking-MCP.git
cd Ticket-Booking-MCP
```

### 2. Install dependencies

**Using uv (recommended):**

```bash
pip install uv

uv init

uv add fastmcp
```

This reads `pyproject.toml` and creates a virtual environment with all dependencies automatically.


### 3. Test the server locally

```bash
uv run fastmcp run main.py
```

## for debugging

```bash
npx @modelcontextprotocol/inspector
```



The server auto-creates `train_booking.db` and seeds it with sample data (6 trains, 5 stations, schedules, and fare classes) on first run.

## Connecting to Claude Code

### Option A: Project-level config (recommended)

Create a `.mcp.json` file in your project root:

```json
{
  "mcpServers": {
    "ticket_booking": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/Ticket-Booking-MCP",
        "run",
        "fastmcp",
        "run",
        "main.py"
      ]
    }
  }
}
```

> **Important:** Replace `/absolute/path/to/Ticket-Booking-MCP` with the actual absolute path to this project on your machine. On Windows use `\\` as path separators (e.g. `C:\\MyRepos\\Ticket-Booking-MCP`).

### Option B: Global config

To make the server available in all your Claude Code sessions:

```bash
claude mcp add ticket_booking -- uv --directory /absolute/path/to/Ticket-Booking-MCP run fastmcp run main.py
```

### Verify the connection

After configuring, start Claude Code in the project directory:

```bash
claude
```

Then ask Claude to search trains or book a ticket:

```
> show me trains from New Delhi to Mumbai on 2025-04-15
> book a ticket on Rajdhani Express for Rahul, age 28
```

## Available Tools

### Booking Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_trains` | Search available trains between two stations | `source`, `destination`, `date` |
| `book_ticket` | Book train tickets | `train_number`, `passenger_name`, `age`, `source`, `destination`, `date`, `class_type`, `num_seats` |
| `cancel_ticket` | Cancel a booked ticket with 80% refund | `pnr` |
| `check_pnr_status` | Check booking status using PNR | `pnr` |

### Information Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_all_stations` | List all available stations | none |
| `get_train_schedule` | Get complete schedule and stops of a train | `train_number` |
| `list_all_bookings` | List all bookings with optional status filter | `status` (optional) |
| `list_bookings_by_passenger` | List bookings for a specific passenger | `passenger_name` |

## Database Schema

The server uses SQLite with 5 tables, auto-created and seeded on startup:

```
stations        - 5 stations (New Delhi, Prayagraj, Ballia, Mumbai, Dehradun)
trains          - 6 trains (Rajdhani, Shatabdi, Doon, Pushpak, Ganga Kaveri, Dehradun Express)
train_classes   - Fare and seat info per train per class (1A, 2A, 3A, SL, CC, EC, 2S)
train_schedule  - Departure/arrival times for each stop
bookings        - Ticket bookings with PNR, status, fare, and cancellation info
```

## Sample Trains

| Train No. | Name | Route |
|-----------|------|-------|
| 12301 | Rajdhani Express | New Delhi → Prayagraj → Mumbai |
| 12302 | Shatabdi Express | New Delhi → Dehradun |
| 13009 | Doon Express | Dehradun → Prayagraj → Ballia |
| 12533 | Pushpak Express | Mumbai → Prayagraj → Ballia → New Delhi |
| 15004 | Ganga Kaveri Express | New Delhi → Prayagraj → Ballia → Mumbai |
| 19019 | Dehradun Express | Mumbai → New Delhi → Dehradun |

## Example Prompts for Claude

```
# Searching Trains
"Show me trains from New Delhi to Mumbai on 2025-04-15"
"Find trains between Prayagraj and Ballia for tomorrow"

# Booking Tickets
"Book a 3A ticket on Rajdhani Express for Rahul, age 28, from New Delhi to Mumbai on 2025-04-15"
"Book 2 sleeper class seats on Pushpak Express for Priya, age 32"

# PNR & Status
"Check PNR status for PNR1001"
"Show me all confirmed bookings"

# Cancellations
"Cancel ticket PNR1001"

# Train Info
"Show the schedule for train 12301"
"What stations are available?"
"List all bookings for passenger Rahul"
```

## Project Structure

```
Ticket-Booking-MCP/
├── main.py              # MCP server with all 8 tool definitions
├── pyproject.toml       # Project metadata and dependencies (uv)
├── requirement.txt      # Dependencies (pip)
├── train_booking.db     # SQLite database (auto-created)
├── .mcp.json            # Claude Code MCP configuration
└── README.md
```

## License

MIT
