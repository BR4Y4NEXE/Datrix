<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React_19-61DAFB?style=for-the-badge&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/Tested_with-Pytest-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" />
</p>

# ⚡ Datrix — Dynamic ETL Pipeline & Real-Time Dashboard

> **Companies that move data around in CSV files have no idea what happened to it — how many rows were loaded, how many silently failed, or why. Datrix automates that pipeline and makes every row auditable in real time.**

<p align="center">
  <a href="URL"><b>🔗 LIVE DEMO</b></a>
  &nbsp;•&nbsp;
  <a href="https://github.com/BR4Y4NEXE/Datrix"><b>💻 Repository</b></a>
</p>

<!-- Replace URL above with your live Vercel deployment link -->

---

## ✨ Key Features

- **Dynamic schema detection** — auto-infers column types (`numeric`, `date`, `text`) from any CSV, zero config.
- **Real-time monitoring** — live pipeline progress and logs streamed over WebSockets.
- **Interactive dashboard** — data quality metrics, run history, and visual analytics.
- **Data governance** — a quarantine system isolates invalid rows for auditing instead of dropping them silently.
- **Automated notifications** — email and Slack reports the moment a run finishes.
- **Bilingual UI** — English / Spanish (i18n).

---

## 🎯 Purpose

Datrix is a full-stack platform built to tame the chaos of data processing. What started as a CLI tool for sales pipelines evolved into a **fully dynamic** ETL (Extract, Transform, Load) engine that adapts to any CSV schema.

Rather than hard-coding columns, Datrix inspects incoming data, infers its structure, transforms and validates it, and persists a complete audit trail of every row — loaded, validated, or rejected — all while streaming progress live to a dashboard.

---

## 📸 Screenshots

<!-- Drop the real images into docs/ and they will render automatically. -->

![Dashboard](docs/dashboard.png)
<!-- TODO: add the main dashboard screenshot at docs/dashboard.png -->

![Data Explorer](docs/data-explorer.png)
<!-- TODO: add the Data Explorer screenshot at docs/data-explorer.png -->

![Quarantine](docs/quarantine.png)
<!-- TODO: add the Quarantine view screenshot at docs/quarantine.png -->

---

## 🏗️ Architecture & Deployment

The project is modular by design, for scalability and easy deployment:

- **Frontend:** React 19 + Vite 6 (deployed on **Vercel**).
- **Backend:** FastAPI + SQLite (deployed on **Render**).
- **Communication:** REST API for data, WebSockets for live logs.

```
┌─────────────────────────────────┐      ┌──────────────────────────────────┐
│     React 19 (Vercel)           │      │        FastAPI (Render)           │
│                                 │      │                                  │
│  Dashboard ─ Analytics          │ HTTP │  /pipeline/run  → PipelineRunner │
│  DataExplorer ─ History   ◄─────┼──────┼► /data/*        → SQLite queries │
│  Quarantine                     │  WS  │  /data/schema   → Column types   │
│  i18n (EN/ES)                   │      │  /ws/{run_id}   → Live logs      │
└─────────────────────────────────┘      └──────────────────────────────────┘
```

---

## 🔥 The Engineering Challenge

This project was a complete architectural transformation. Each step was a deliberate trade-off, not just a feature:

1. **Synchronous → Event-Driven.** The original pipeline blocked on every run, so only one job could execute and there was no visibility into progress. **Decision:** rebuild around `asyncio` + WebSockets. **Why:** it unlocks concurrent runs *and* live monitoring from the same change, instead of bolting on a polling layer that would have added latency and load for no real-time guarantee.

2. **Fixed Schema → Dynamic Engine.** The system handled exactly 6 hard-coded columns, which meant a new file format meant new code. **Decision:** introduce a metadata abstraction layer that detects and transforms any CSV structure at runtime. **Why:** moving schema knowledge from code into data turns "ship a release" into "drop in a file," which is the whole value proposition of the tool.

3. **Ephemeral → Persistent & Auditable.** Results vanished once a run ended, so failures couldn't be investigated. **Decision:** add a SQLite persistence layer recording every row as processed, validated, or rejected. **Why:** auditability is the product — a quarantine you can't query is just a silent `DROP`. SQLite keeps that history zero-ops to deploy, matching the project's single-file, low-friction footprint.

---

## 🧪 Quality & Testing

The reliability of the transformation engine is backed by a **Pytest** suite.

- **Critical coverage:** `transformer.py` is tested for:
  - Cleaning and normalizing numeric, date, and text values.
  - Auto-detecting column type based on content.
  - Validating dynamic schemas across different file types (Sales CSV, Amazon-style CSV, etc.).
  - Controlled rejection of invalid or incomplete rows.

Run the tests:
```bash
pytest tests/test_transformer.py
```

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/BR4Y4NEXE/Datrix.git
cd Datrix
```

### 2. Configuration (environment variables)
Copy `.env.example` to `.env` and set your SMTP and Slack credentials.

### 3. Backend (Render)
```bash
pip install -r requirements.txt
pip install -r requirements-api.txt
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 4. Frontend (Vercel)
```bash
cd frontend
npm install
npm run dev
```

---

## 📂 Project Structure

```
Datrix/
├── backend/               # FastAPI application & business logic
├── frontend/              # React application (dashboard & UI)
├── src/                   # Core ETL modules (Extractor, Transformer, Loader)
├── tests/                 # Pytest suite
├── data/                  # Input samples & quarantine reports
└── etl.py                 # CLI entry point (legacy support)
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Core ETL** | Python, Pandas, SQLite, Dataclasses |
| **Backend** | FastAPI, Uvicorn, WebSocket |
| **Frontend** | React 19, Vite 6, Recharts, Lucide |
| **Testing** | Pytest |
| **Deployment** | Vercel (frontend), Render (backend) |

---

## 📝 License

This project is licensed under the MIT License.
