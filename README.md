<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/React_19-61DAFB?style=for-the-badge&logo=react&logoColor=black" />
  <img src="https://img.shields.io/badge/Vite_6-646CFF?style=for-the-badge&logo=vite&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" />
  <img src="https://img.shields.io/badge/WebSocket-010101?style=for-the-badge&logo=socket.io&logoColor=white" />
</p>

# ⚡ Datrix — Dynamic ETL Pipeline & Real-Time Dashboard

> **Las empresas que trabajan con archivos CSV no tienen visibilidad de qué pasó con sus datos ni cuántos registros fallaron. Datrix automatiza ese proceso y lo hace auditable en tiempo real.**

---

## 🎯 Propósito

Datrix es una plataforma Full-Stack diseñada para solucionar el caos en el procesamiento de datos. Lo que comenzó como una herramienta CLI para pipelines de ventas evolucionó en un motor de ETL (Extract, Transform, Load) **totalmente dinámico** que se adapta a cualquier esquema de CSV.

- **Detección dinámica de esquemas:** Identifica automáticamente tipos de datos (`numeric`, `date`, `text`) sin configuración previa.
- **Monitoreo en tiempo real:** Visualización del progreso mediante WebSockets (Live Logs).
- **Dashboard Interactivo:** Métricas de calidad, historial de ejecuciones y analítica visual.
- **Gobernanza de Datos:** Sistema de cuarentena que aísla registros inválidos para su auditoría.
- **Notificaciones Automatizadas:** Reportes automáticos vía Email y Slack al finalizar el proceso.

---

## 📸 Screenshots (Próximamente)

> [!NOTE]
> Aquí se incluirán imágenes del Dashboard, Data Explorer y el sistema de Quarantine.

---

## 🏗️ Arquitectura y Despliegue

El proyecto está diseñado de forma modular para garantizar escalabilidad y facilidad de despliegue:

- **Frontend:** React 19 + Vite 6 (Desplegado en **Vercel**).
- **Backend:** FastAPI + SQLite (Desplegado en **Render**).
- **Comunicación:** REST API para datos y WebSockets para logs en vivo.

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

## 🔥 El Desafío de Ingeniería

Este proyecto representa una transformación arquitectónica completa:

1. **De Síncrono a Event-Driven:** El pipeline original bloqueaba la ejecución. Se rediseñó usando `asyncio` y WebSockets para permitir múltiples ejecuciones concurrentes y monitoreo en vivo.
2. **De Esquema Fijo a Motor Dinámico:** El sistema pasó de procesar 6 columnas fijas a detectar y transformar cualquier estructura CSV mediante una capa de abstracción de metadatos.
3. **Persistencia y Auditoría:** Se implementó una capa de persistencia en SQLite para llevar un registro histórico de cada fila procesada, validada o rechazada.

---

## 🧪 Calidad y Testing

La fiabilidad del motor de transformación está garantizada mediante una suite de pruebas con **Pytest**.

- **Cobertura Crítica:** El `transformer.py` cuenta con tests exhaustivos que verifican:
  - Limpieza y normalización de valores numéricos, fechas y texto.
  - Detección automática del tipo de columna basado en el contenido.
  - Validación de esquemas dinámicos con diferentes tipos de archivos (Sales CSV, Amazon-style CSV, etc.).
  - Rechazo controlado de filas inválidas o incompletas.

Para ejecutar los tests:
```bash
pytest tests/test_transformer.py
```

---

## 🚀 Quick Start

### 1. Clonar el Repositorio
```bash
git clone https://github.com/BR4Y4NEXE/Datrix.git
cd Datrix
```

### 2. Configuración (Variables de Entorno)
Copia el archivo `.env.example` a `.env` y configura tus credenciales de SMTP y Slack.

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

## 📂 Estructura del Proyecto

```
Datrix/
├── backend/               # FastAPI Application & Business Logic
├── frontend/              # React Application (Dashboard & UI)
├── src/                   # Core ETL Modules (Extractor, Transformer, Loader)
├── tests/                 # Pytest Suite
├── data/                  # Input samples & Quarantine reports
└── etl.py                 # CLI Entry point (Legacy support)
```

---

## 🛠️ Tech Stack

| Capa | Tecnología |
|-------|-----------|
| **Core ETL** | Python, Pandas, SQLite, Dataclasses |
| **Backend** | FastAPI, Uvicorn, WebSocket |
| **Frontend** | React 19, Vite 6, Recharts, Lucide |
| **Testing** | Pytest |
| **Despliegue** | Vercel (Frontend), Render (Backend) |

---

## 📝 Licencia

Este proyecto está bajo la licencia MIT.
