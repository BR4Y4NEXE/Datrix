<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React_19-61DAFB?style=for-the-badge&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/Vite_6-646CFF?style=for-the-badge&logo=vite&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/WebSocket-010101?style=for-the-badge&logo=socket.io&logoColor=white" />
</p>

# ⚡ FluxCLI — Dynamic ETL Pipeline & Real-Time Dashboard

> **A CLI-first ETL pipeline that evolved into a full-stack web platform** — now supporting **any CSV schema** with automatic column detection, real-time pipeline monitoring via WebSocket, interactive analytics dashboards, and bilingual i18n support (EN/ES).

---

## 🎯 Purpose

FluxCLI automates the processing of CSV data through a robust **Extract → Transform → Load → Notify** pipeline. Originally built as a Python CLI tool for sales data, it was migrated to a modern web platform and later generalized to accept **any CSV schema dynamically**. It provides:

- **Dynamic schema detection** — automatically identifies column types (`numeric`, `date`, `text`) from any CSV
- **Real-time visibility** into ETL execution via WebSocket-streamed logs
- **Interactive dashboards** with data analytics, quality metrics, and execution history
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
│  Quarantine                     │  WS  │  /data/schema   → Column types   │
│                                 │      │  /data/export   → CSV download   │
│  i18n (EN/ES) ─ Recharts        │      │  /data/reset    → Full cleanup   │
│  Datrix Logo                    │      │  /ws/{run_id}   → Live logs      │
└─────────────────────────────────┘      │                                  │
                                         │  Services:                       │
                                         │   ├─ pipeline_runner.py          │
                                         │   └─ log_handler.py (WS bridge)  │
                                         │                                  │
                                         │  Core ETL:                       │
                                         │   ├─ extractor.py                │
                                         │   ├─ transformer.py (dynamic)    │
                                         │   ├─ loader.py (JSON datasets)   │
                                         │   └─ notifier.py (Email/Slack)   │
                                         │                                  │
                                         │  Data Layer:                     │
                                         │   ├─ datasets (JSON rows)        │
                                         │   ├─ dataset_schema (col types)  │
                                         │   └─ pipeline_runs (history)     │
                                         └──────────────────────────────────┘
```

---

## 🔥 The Migration Challenge

This project wasn't just "add a frontend." It was a **full architectural transformation** from a synchronous CLI script to an async, event-driven web platform — and later, from a fixed-schema pipeline to a **fully dynamic ETL engine**. Here's what made it hard:

### 🧩 Synchronous → Asynchronous Execution

The original pipeline blocks the process for 30+ seconds during execution. In a web context, that means HTTP timeouts and frozen UIs. **Solution:** Rewrote the orchestration layer using `asyncio.to_thread()`, returning a `run_id` immediately and streaming progress via WebSocket.

### 📡 stdout → WebSocket Log Streaming

The CLI printed logs to the terminal. The web dashboard needed them in real time. **Solution:** Built a custom `logging.Handler` that intercepts log messages and broadcasts them to connected WebSocket clients — supporting multiple concurrent sessions per `run_id`.

### 📁 File Paths → HTTP Uploads

The CLI receives `--file path/to/file.csv`. Browsers don't work that way. **Solution:** Implemented `multipart/form-data` upload with an auto-detect mode that scans for today's file in the `data/` directory.

### 🗃️ Ephemeral → Persistent State

The CLI had no memory — each run was fire-and-forget. The dashboard needs execution history, metrics, and trends. **Solution:** Designed a `pipeline_runs` table in SQLite tracking `total_read`, `total_valid`, `total_rejected`, `db_inserts`, `db_updates`, `duration`, and `status`.

### 🔄 Fixed Schema → Dynamic Schema

The original pipeline was hardcoded for a 6-column sales CSV (`id`, `date`, `product`, `qty`, `price`, `store_id`). **Solution:** Rewrote the transformer with `ColumnSchema` and `TransformResult` dataclasses that auto-detect column types (`numeric`, `date`, `text`). The loader now stores data as JSON rows in a generic `datasets` table with a companion `dataset_schema` table — enabling any CSV to be processed without code changes.

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
| **Dynamic Schema** | Automatically detects column types (`numeric`, `date`, `text`) from any CSV — no hardcoded schemas |
| **ETL Pipeline** | Extract → Transform → Load with data validation, deduplication, and upsert strategies |
| **Real-Time Logs** | WebSocket-powered live log streaming during pipeline execution |
| **Dashboard** | KPI cards, execution timeline, and quick-action controls |
| **Analytics** | Data trends, category breakdown, and comparisons via Recharts |
| **Data Explorer** | Browse, search, and paginate loaded records with dynamic columns |
| **CSV Export** | Export processed data as CSV directly from the Data Explorer |
| **Quarantine** | Review invalid/rejected rows with reason codes |
| **History** | Full execution log with duration, status, and row-level metrics |
| **Database Reset** | One-click cleanup of all data, run history, and quarantine files |
| **i18n** | Bilingual support (English / Español) with persistent language selection |
| **Smart Toggle** | Auto-detect test data toggle disables automatically when a real CSV is uploaded |
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
# Auto-detect today's file
python etl.py --auto

# Dry run (no DB writes, no notifications)
python etl.py --auto --dry-run

# Process a specific file
python etl.py --file data/input/my_data.csv
```

---

## 📂 Project Structure

```
FluxCLI/
├── etl.py                    # Original CLI entry point
├── mock_data_gen.py          # Test data generator
├── Procfile                  # Deployment configuration
├── .python-version           # Python version pinning
├── backend/
│   ├── main.py               # FastAPI application
│   ├── database.py           # SQLite: datasets, dataset_schema, pipeline_runs
│   ├── models.py             # Pydantic schemas (ColumnSchemaResponse, PaginatedRecords, etc.)
│   ├── routes/               # API endpoints (pipeline, data, stats)
│   └── services/
│       ├── pipeline_runner.py # Async orchestration layer
│       └── log_handler.py    # WebSocket log bridge
├── frontend/
│   └── src/
│       ├── App.jsx           # Router + sidebar layout
│       ├── img/              # Datrix logo (datrix-logo-v3.svg)
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── Analytics.jsx
│       │   ├── DataExplorer.jsx
│       │   ├── History.jsx
│       │   └── Quarantine.jsx
│       ├── hooks/            # Custom React hooks (useWebSocket)
│       ├── i18n/
│       │   ├── LanguageContext.jsx  # React Context for i18n
│       │   ├── en.json             # English translations
│       │   └── es.json             # Spanish translations
│       └── services/         # API client layer (api.js)
├── src/                      # Core ETL modules
│   ├── extractor.py
│   ├── transformer.py        # Dynamic column detection (ColumnSchema, TransformResult)
│   ├── loader.py             # JSON-based dataset storage
│   └── notifier.py
├── config/                   # Environment configuration
├── data/                     # Input files + quarantine reports
├── logs/                     # Execution logs
└── tests/                    # Unit tests
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **ETL Core** | Python, Pandas, SQLite, dataclasses, python-dateutil |
| **Backend** | FastAPI, Uvicorn, WebSocket |
| **Frontend** | React 19, Vite 6, React Router 7 |
| **Charts** | Recharts |
| **Icons** | Lucide React |
| **Notifications** | SMTP (Email), Slack Webhooks |
| **Testing** | Pytest |

---

## 📝 License

This project is licensed under the MIT License.
