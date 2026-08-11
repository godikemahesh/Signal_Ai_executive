# Signal — Personal AI Executive Assistant

<div align="center">

  <h1 align="center">⚡ Signal</h1>
  <p align="center">
    <strong>Turn 147 raw inbox signals into 4 clear executive decisions.</strong>
  </p>

  <p align="center">
    <a href="#-key-features">Key Features</a> •
    <a href="#-system-architecture">Architecture</a> •
    <a href="#-tech-stack">Tech Stack</a> •
    <a href="#-getting-started">Getting Started</a> •
    <a href="#-deployment-guide">Deployment</a>
  </p>

  <p align="center">
    <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
    <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React" />
    <img src="https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript" />
    <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
    <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
    <img src="https://img.shields.io/badge/Gemini_AI-8E75B2?style=for-the-badge&logo=google&logoColor=white" alt="Gemini AI" />
    <img src="https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=white" alt="Render" />
    <img src="https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white" alt="Vercel" />
  </p>

</div>

---

## 🌟 Executive Overview

Inboxes are bloated with noise: security alerts, promotional digests, transactional updates, and multi-stage interview threads. **Signal** acts as your personal AI Chief of Staff. 

Instead of treating emails as endless static rows in an inbox, Signal extracts real-world **events**, **deadlines**, **multi-stage life entities** (Job Applications, Orders, Bills, Travel), and **action items**—filtering out noise automatically and presenting a calm executive dashboard.

```
       📥 147 Raw Emails Ingested
                   │
    ┌──────────────┴──────────────┐
    ▼                             ▼
🛡️  143 Noisy Signals         🔥 4 Executive Decisions
    (Newsletters, Promo,         (Action required: Reply,
     Security, Receipts)          Pay, Upload, Complete)
    [Handled Automatically]      [Surfaced in Do Now / Today]
```

---

## ✨ Key Features & Innovations

### 🧠 1. Smart 3-Tier Processing Pipeline (Zero-LLM Cost Strategy)
To optimize speed and minimize LLM API costs by up to **85%**, Signal routes emails through 3 intelligent tiers:
- **Tier 0 (Blocklist & Auto-Filter)**: Known marketing/newsletter senders are auto-archived immediately with **$0 LLM cost**.
- **Tier 1 (Rule & Heuristics Engine)**: Pattern-matched notifications and digest emails are categorized and summarized using rule heuristics with **$0 LLM cost**.
- **Tier 2 (Full AI Intelligence)**: High-priority, complex emails are sanitized via **PII Masker** (scrubbing PAN, Aadhaar, credit cards, phone numbers) before sending to **Google Gemini 2.0 Flash** (with automatic fallback to **Groq Llama 3.1 70B**).

---

### ⏳ 2. Multi-Stage Entity & Timeline Tracker
Collapses multi-month, multi-email threads into clean, chronological **Life Entity Cards**:
- **Job Applications & Interviews**: Tracks progress from application $\rightarrow$ recruiter call $\rightarrow$ assessment link $\rightarrow$ interview schedule.
- **Orders & Deliveries**: Merges purchase confirmation $\rightarrow$ dispatch $\rightarrow$ out-for-delivery tracking.
- **Bills & Payments**: Tracks bill generation $\rightarrow$ due date reminders $\rightarrow$ payment confirmation.
- **Smart Merging Engine**: Automatically merges new events into existing active entities rather than duplicating cards.
- **Noise Gatekeeper**: Filters out one-off security alerts (*"Google Account data shared"*), login alerts, marketing, and newsletters.

---

### 🤖 3. Self-Adapting Behavioral Learning Engine
Signal continuously learns from how you interact with your inbox:
- **Engagement Scoring**: Calculates a dynamic score $\text{Engagement} = \frac{\text{Opened} + \text{Replied}}{\text{Total Received}}$ for every sender.
- **Auto-Demotion Rule**: Senders you ignore 10 times consecutively are automatically demoted to Tier 0 auto-archiving.
- **Dynamic Priority Boosting**: Senders you open quickly or reply to often receive automatic priority boosts to *Do Now*.
- **Live Behavior Metrics**: Displays real-time time saved, % auto-filtered, and active learned heuristics.

---

### 🎯 4. Differentiated 1-Click Action System
- **Mark Handled**: Completes items locally in Signal **without launching Gmail**.
- **Reply Now / Start Now / Pay Now / Open in Gmail**: Launches Gmail in a new browser tab AND **automatically completes the signal** in Signal.
- **Dynamic Handled Automatically Card**: Automatically groups and counts archived emails into clean categories (*Newsletters, Security Alerts, GitHub, Social, Financial Receipts*).

---

### 💬 5. Ask Signal (AI Life Search)
Ask natural language questions across your entire digital life backed by **pgvector 384-dimensional semantic embeddings** (`all-MiniLM-L6-v2`):
- *"Which companies rejected me this month?"*
- *"What needs my attention right now?"*
- *"Show all interview invitations"*
- *"Applications with no reply > 10 days"*

---

## 🏗️ System Architecture

```
   ┌─────────────────────────────────────────────────────────────┐
   │                    Gmail API / Webhooks                     │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │               Parser Engine & PII Masker                    │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
   ┌─────────────┐         ┌─────────────┐         ┌─────────────┐
   │   Tier 0    │         │   Tier 1    │         │   Tier 2    │
   │  Blocklist  │         │ Rule Engine │         │ Full AI LLM │
   └──────┬──────┘         └──────┬──────┘         └──────┬──────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                                  ▼
   ┌─────────────────────────────────────────────────────────────┐
   │               Entity & Timeline Gatekeeper                  │
   └──────────────────────────────┬──────────────────────────────┘
                                  │
          ┌───────────────────────┴───────────────────────┐
          ▼                                               ▼
   ┌─────────────┐                                 ┌─────────────┐
   │ PostgreSQL  │ ◄─────── Semantic Search ──────►│ WebSocket   │
   │ + pgvector  │                                 │ Broadcast   │
   └─────────────┘                                 └──────┬──────┘
                                                          │
                                                          ▼
                                                   ┌─────────────┐
                                                   │ React UI    │
                                                   └─────────────┘
```

---

## 🛠️ Tech Stack

### **Backend**
- **Framework**: FastAPI (Async Python 3.11)
- **Database**: PostgreSQL with `pgvector` & `pg_trgm` extensions (SQLAlchemy Async + asyncpg)
- **Primary AI / LLM**: Google Gemini API (`gemini-2.0-flash`)
- **Fallback AI**: Groq API (`llama-3.1-70b-versatile`)
- **Embeddings**: SentenceTransformers (`all-MiniLM-L6-v2`) with TF-IDF fallback
- **Authentication**: Google OAuth 2.0 + Persistent JWT Sessions

### **Frontend**
- **Framework**: React 18 + TypeScript + Vite
- **Styling**: Vanilla CSS Design System + Tailwind CSS v4
- **Animations**: Framer Motion (`motion/react`)
- **Icons**: Lucide React
- **Real-Time**: Native WebSockets (`ws://` / `wss://`)

---

## 🌐 API Endpoint Matrix

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/overview` | Command center summary (Needs action, Changed, Due soon, Dynamic handled breakdown) |
| `GET` | `/api/v1/focus` | Priority bucket summaries (*Do Now*, *Today*, *This Week*, *Waiting*, *Completed*, *Ignored*) |
| `PATCH` | `/api/v1/focus/{id}/move` | Manually move signal bucket with instant UI update |
| `GET` | `/api/v1/timeline` | Multi-stage life entities (Jobs, Orders, Bills, Travel) & chronological event histories |
| `GET` | `/api/v1/behavior` | Live behavior metrics, auto-filtered %, time saved, and learned heuristics |
| `POST` | `/api/v1/ask` | Natural language RAG query engine over email history |
| `GET` | `/api/v1/signals` | Paginated signal list with optional bucket filtering |
| `POST` | `/api/v1/signals/{id}/archive` | Archive signal |
| `POST` | `/api/v1/signals/sync` | Trigger background Gmail synchronization |
| `WS` | `/ws` | Real-time WebSocket connection for instant signal updates |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL database (with `pgvector` extension)

---

### 1. Database Initialization

Run `schema.sql` on your PostgreSQL database (or Supabase SQL Editor) to create all 17 tables, vector indexes, and seed data:

```bash
psql -h localhost -U postgres -d signal -f schema.sql
```

---

### 2. Backend Setup

```bash
# Clone the repository
git clone https://github.com/your-username/personal-email-agent.git
cd personal-email-agent

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

Edit `.env` with your keys:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/signal
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
JWT_SECRET=your_super_secret_jwt_key
```

Run backend server:
```bash
uvicorn app.main:app --reload --port 8000
```
Swagger API Documentation will be live at `http://localhost:8000/docs`.

---

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## ☁️ Deployment Guide

### Deploy Backend on **Render**

1. Create a **PostgreSQL Database** on Render (`signal-db`).
2. Create a **Web Service** on Render connected to this repository:
   - **Environment**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. Add Environment Variables:
   - `DATABASE_URL`: *(Your Render PostgreSQL connection string)*
   - `GEMINI_API_KEY`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `JWT_SECRET`
   - `CORS_ORIGINS`: `https://your-app.vercel.app`

*(Note: `render.yaml` blueprint is included in the root directory for 1-click Render setup)*.

---

### Deploy Frontend on **Vercel**

1. Import the repository in **Vercel**.
2. Set **Root Directory** to `frontend`.
3. Add Environment Variable:
   - `VITE_API_BASE_URL`: `https://your-render-backend.onrender.com`
4. Click **Deploy**.

*(Note: `frontend/vercel.json` is included for SPA route rewrites)*.

---

## 🛡️ Privacy & Security

- **PII Masking**: Personal identifiers (Aadhaar, PAN, Credit Cards, Phone numbers) are scrubbed before sending prompt payloads to external LLM APIs.
- **1-Click OAuth**: Google OAuth tokens are stored encrypted; refresh tokens are persisted securely to allow 24/7 background syncing without constant re-login prompts.
- **Local Vectors**: Vector embeddings are generated and stored inside your own PostgreSQL instance.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

<div align="center">
  <br />
  <p>Crafted with ❤️ for peaceful, executive inbox control.</p>
</div>
