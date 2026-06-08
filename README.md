# 🛡️ API Watchdog

API Watchdog is a self-hosted, high-performance API monitoring tool designed to keep tabs on your endpoints in real-time. It features a modern Vercel-inspired dashboard, parallelized background checks, automatic downtime incident tracking, and instant alerts pushed to your Telegram app via a decoupled Redis queue.

---

## 🏗️ Architecture Overview

API Watchdog splits responsibilities between a FastAPI web server, a concurrent monitoring service, and an asynchronous Redis-backed notification worker.

```mermaid
graph TD
    subgraph Client
        FE[Frontend - HTML5/CSS/JS]
    end

    subgraph API Watchdog Backend
        API[FastAPI Server]
        MON[Monitor Task - asyncio]
        WRK[Telegram Worker - asyncio]
    end

    subgraph Cache & Storage
        DB[(PostgreSQL Database)]
        RED[(Redis - Cache & Queue)]
    end

    subgraph External
        TG[Telegram Bot API]
        EXT[Target API Endpoints]
    end

    FE -->|HTTP Requests| API
    API -->|Read/Write Auth & Endpoints| DB
    API -->|Rate Limiting| RED
    MON -->|Query Active Sites| DB
    MON -->|Concurrent Health Checks| EXT
    MON -->|Log Incidents & Statuses| DB
    MON -->|Push Alerts to telegram_queue| RED
    RED -->|BLPOP Jobs| WRK
    WRK -->|Send Alerts| TG
    TG -->|Downtime/Uptime Alerts| User[User Telegram App]
```

---

## ✨ Key Features

- **Concurrent Async Health Checks**: Monitors all target endpoints concurrently using Python's `asyncio.gather` and a shared `httpx.AsyncClient`. It is capable of scaling to check hundreds of sites in seconds.
- **Transient Down Protection (Double-Check)**: To prevent false alarms due to transient network blips, the monitor instantly schedules a double-check 2 seconds after any initial `DOWN` detection before triggering an incident.
- **Downtime Incident Tracking**: Instead of just logging status strings, it aggregates downtime into a dedicated `incidents` table. It tracks the exact timestamp an endpoint goes offline, the time it recovers, and calculates total downtime duration.
- **Asynchronous Alerting Pipeline**: Alerts are pushed as jobs onto a Redis queue (`telegram_queue`). A background asyncio worker processes queue items sequentially with `BLPOP` to guarantee delivery without blocking the main health-check cycle.
- **OAuth2 JWT Authentication**: Secures your dashboard with user accounts, password hashing (bcrypt), and signed JWT access tokens.
- **Redis Rate Limiting**: Features a sliding-window rate limiter preventing endpoint-addition spam (rate limited to 8 actions per minute per user).
- **Auto-Pruning Log Retention**: A hourly cleanup worker runs in the background to delete raw ping logs older than 24 hours, keeping your PostgreSQL storage footprint lean and fast.
- **Premium Dark-Theme Dashboard**: A minimalist, high-contrast dashboard with micro-interactions, live status counters, and visual charts for raw checks and resolved incidents.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.12)
- **Frontend**: Vanilla HTML5, CSS3 (Custom Theme), JavaScript (with Lucide Icons)
- **Database**: PostgreSQL (SQLAlchemy ORM + Alembic Migrations)
- **Cache & Message Queue**: Redis (redis-py client)
- **Concurrency**: Python `asyncio` Event Loop
- **Containerization**: Docker & Docker Compose

---

## 📁 Repository Structure

```text
api-watchdog/
├── alembic/              # Database migration scripts
├── app/
│   ├── api/
│   │   ├── deps.py       # API dependency injection (auth)
│   │   └── routes/       # API routers (auth, endpoints, telegram, users)
│   ├── cache/            # Redis client and rate limiting
│   ├── core/             # Configuration settings and security
│   ├── db/               # Database session and base configuration
│   ├── models/           # SQLAlchemy database schemas
│   ├── queues/           # Redis queue handlers
│   ├── schemas/          # Pydantic validation schemas
│   ├── services/         # Monitor loop and Telegram alerting
│   ├── workers/          # Background worker tasks
│   └── main.py           # Application entrypoint
├── static/
│   └── index.html        # Single-page frontend app
├── Dockerfile            # Container definition
├── docker-compose.yml    # Development compose file
├── requirements.txt      # Python dependencies
└── render.yaml           # Deployment blueprint (static frontend)
```

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.12+**
- **PostgreSQL** database
- **Redis** server
- **Telegram Bot** (optional, for alerts)

---

### Configuration (`.env`)

Create a `.env` file in the root directory and configure the following parameters:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# JWT Security
SECRET_KEY=generate_a_strong_random_secret_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Telegram Bot Integration
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
TELEGRAM_CHAT_ID=987654321
ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
```

---

### Local Installation & Run

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/api-watchdog.git
   cd api-watchdog
   ```

2. **Set up a Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Apply Database Migrations**
   ```bash
   alembic upgrade head
   ```

4. **Start the FastAPI Application**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

   The app is now running at [http://localhost:8000](http://localhost:8000). The frontend dashboard will serve automatically at the root `/` route.

---

### Running with Docker Compose

To spin up the application with a single command (excluding database setup if you're using Supabase/external DB, or adjusting compose to include DB and Redis):

```bash
docker-compose up --build
```

---

## 🤖 Connecting the Telegram Bot

API Watchdog utilizes a unique verification token system to link a dashboard user account to their Telegram chat ID securely:

1. Create a bot via Telegram's **@BotFather** to get your `TELEGRAM_BOT_TOKEN`.
2. Configure your server to listen for Telegram webhooks (via `/webhook/telegram` API endpoint), or set up a polling service.
3. On the dashboard, click **"Connect Telegram"**. This redirects you to the bot with a start token parameter:
   `https://t.me/YourBotName?start=<user_link_token>`
4. Clicking **"Start"** in Telegram sends the link token to the webhook, which binds your `chat_id` to your user account.
5. All future downtime alerts will be dispatched directly to your Telegram chat.
