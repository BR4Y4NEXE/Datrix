<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React_19-61DAFB?style=for-the-badge&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/Vite_6-646CFF?style=for-the-badge&logo=vite&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/WebSocket-010101?style=for-the-badge&logo=socket.io&logoColor=white" />
</p>

# ⚡ FluxCLI — Sales ETL Pipeline & Real-Time Dashboard

> **A CLI-first ETL pipeline that evolved into a full-stack web platform** — featuring real-time pipeline monitoring via WebSocket, interactive analytics dashboards, and bilingual i18n support (EN/ES).

---

## 🎯 Purpose

FluxCLI automates the daily processing of sales data through a robust **Extract → Transform → Load → Notify** pipeline. It was originally built as a Python CLI tool, then migrated to a modern web platform to provide:

- **Real-time visibility** into ETL execution via WebSocket-streamed logs
- **Interactive dashboards** with sales analytics, data quality metrics, and execution history
- **Data governance** through a quarantine system that isolates invalid records for review
- **Automated notifications** via Email and Slack upon pipeline completion

---

## 🏗️ Architecture

```
┌─────────────────────────────────┐      ┌──────────────────────────────────┐
│     React 19 + Vite 6           │      │        FastAPI Backend            │
│                                 │      │                                  │
│  Dashboard ─ Analytics          │ HTTP │  /pipeline/run  → PipelineRunner │
│  DataExplorer ─ History   ◄─────┼──────┼► /data/*        → SQLite queries │
│  Quarantine ─ Notifications     │  WS  │  /ws/{run_id}  → Live logs       │
│                                 │      │                                  │
│  i18n (EN/ES) ─ Recharts        │      │  Services:                       │
└─────────────────────────────────┘      │   ├─ pipeline_runner.py          │
                                         │   ├─ log_handler.py (WS bridge)  │
                                         │   └─ connection_manager.py       │
                                         │                                  │
                                         │  Core ETL:                       │
                                         │   ├─ extractor.py                │
                                         │   ├─ transformer.py              │
                                         │   ├─ loader.py (SQLite upsert)   │
                                         │   └─ notifier.py (Email/Slack)   │
                                         └──────────────────────────────────┘
```

---

## 🔥 The Migration Challenge

This project wasn't just "add a frontend." It was a **full architectural transformation** from a synchronous CLI script to an async, event-driven web platform. Here's what made it hard:

### 🧩 Synchronous → Asynchronous Execution

The original pipeline blocks the process for 30+ seconds during execution. In a web context, that means HTTP timeouts and frozen UIs. **Solution:** Rewrote the orchestration layer using `asyncio.to_thread()`, returning a `run_id` immediately and streaming progress via WebSocket.

### 📡 stdout → WebSocket Log Streaming

The CLI printed logs to the terminal. The web dashboard needed them in real time. **Solution:** Built a custom `logging.Handler` that intercepts log messages and broadcasts them to connected WebSocket clients — supporting multiple concurrent sessions per `run_id`.

### 📁 File Paths → HTTP Uploads

The CLI receives `--file path/to/file.csv`. Browsers don't work that way. **Solution:** Implemented `multipart/form-data` upload with an auto-detect mode that scans for today's sales file in the `data/` directory.

### 🗃️ Ephemeral → Persistent State

The CLI had no memory — each run was fire-and-forget. The dashboard needs execution history, metrics, and trends. **Solution:** Designed a `pipeline_runs` table in SQLite tracking `total_read`, `total_valid`, `total_rejected`, `db_inserts`, `db_updates`, `duration`, and `status`.

### 🐼 Pandas 3.0 Breaking Change

Pandas 3.0 changed how `NaN` values behave — they no longer auto-cast to strings. This caused a subtle `AttributeError: float has no attribute 'lower'` deep in the transformer. A single missing `str()` wrapper was the fix, but finding it required tracing through real production data.

### 🎨 Two UI Rewrites

The first frontend used glassmorphism (blur, gradients, heavy shadows). It didn't match the target Flatkit design language. **The entire CSS was rewritten** to a flat, clean aesthetic with subtle borders and minimal shadows.

<details>
<summary><b>📊 Full Issue Tracker (11 problems solved)</b></summary>

| # | Problem | Severity | Category |
|---|---------|----------|----------|
| 1 | Blocking synchronous execution | 🔴 High | Architecture |
| 2 | Logs to stdout with no web channel | 🔴 High | Architecture |
| 3 | File upload vs local paths | 🟡 Medium | Architecture |
| 4 | No execution history | 🟡 Medium | Architecture |
| 5 | Pandas 3.0 NaN + `.lower()` | 🔴 High | Compatibility |
| 6 | Vite scaffolding failure | 🟡 Medium | Compatibility |
| 7 | CORS cross-origin blocking | 🟡 Medium | Compatibility |
| 8 | Recharts tooltip unreadable on dark theme | 🟢 Low | UI/UX |
| 9 | Sidebar active color mismatch | 🟢 Low | UI/UX |
| 10 | Glassmorphism vs flat design mismatch | 🟡 Medium | UI/UX |
| 11 | `$HOME` env variable missing on Windows | 🟢 Low | Environment |

</details>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **ETL Pipeline** | Extract → Transform → Load with data validation, deduplication, and upsert strategies |
| **Real-Time Logs** | WebSocket-powered live log streaming during pipeline execution |
| **Dashboard** | KPI cards, execution timeline, and quick-action controls |
| **Analytics** | Sales trends, category breakdown, and monthly comparisons via Recharts |
| **Data Explorer** | Browse, search, and paginate loaded sales records |
| **Quarantine** | Review invalid/rejected rows with reason codes |
| **History** | Full execution log with duration, status, and row-level metrics |
| **Notifications** | Email and Slack reports on pipeline completion |
| **i18n** | Bilingual support (English / Español) with persistent language selection |
| **CLI Mode** | Original command-line interface still fully functional |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**

### 1. Clone & Configure

```bash
git clone https://github.com/BR4Y4NEXE/FluxCLI.git
cd FluxCLI
cp .env.example .env
# Edit .env with your SMTP, Slack, and DB settings
```

### 2. Backend

```bash
pip install -r requirements.txt
pip install -r requirements-api.txt
python -m uvicorn backend.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** — the Vite dev server proxies API calls to the backend automatically.

### 4. CLI Mode (Optional)

```bash
# Auto-detect today's sales file
python etl.py --auto

# Dry run (no DB writes, no notifications)
python etl.py --auto --dry-run

# Process a specific file
python etl.py --file data/input/sales_20240119.csv
```

---

## 📂 Project Structure

```
FluxCLI/
├── etl.py                    # Original CLI entry point
├── mock_data_gen.py          # Test data generator
├── backend/
│   ├── main.py               # FastAPI application
│   ├── database.py            # SQLite connection + pipeline_runs table
│   ├── models.py              # Pydantic schemas
│   ├── routes/                # API endpoints (pipeline, data, stats)
│   └── services/
│       ├── pipeline_runner.py # Async orchestration layer
│       ├── log_handler.py     # WebSocket log bridge
│       └── connection_manager.py
├── frontend/
│   └── src/
│       ├── App.jsx            # Router + sidebar layout
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── Analytics.jsx
│       │   ├── DataExplorer.jsx
│       │   ├── History.jsx
│       │   ├── Quarantine.jsx
│       │   └── Notifications.jsx
│       ├── hooks/             # Custom React hooks
│       ├── i18n/              # EN/ES translation files
│       └── services/          # API client layer
├── src/                       # Core ETL modules
│   ├── extractor.py
│   ├── transformer.py
│   ├── loader.py
│   └── notifier.py
├── config/                    # Environment configuration
├── data/                      # Input files + quarantine reports
├── logs/                      # Execution logs
└── tests/                     # Unit tests
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **ETL Core** | Python, Pandas, SQLite |
| **Backend** | FastAPI, Uvicorn, WebSocket |
| **Frontend** | React 19, Vite 6, React Router 7 |
| **Charts** | Recharts |
| **Icons** | Lucide React |
| **Notifications** | SMTP (Email), Slack Webhooks |
| **Testing** | Pytest |

---

## 📝 License

This project is licensed under the MIT License.
