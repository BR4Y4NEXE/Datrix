import os
import sys
import logging

# Ensure project root is on path so config/ and src/ are importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_database
from backend.routes import pipeline, data, ws

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FluxCLI API",
    description="REST API for the FluxCLI Sales ETL Pipeline",
    version="1.0.0",
)

# CORS — allow frontend origins (comma-separated in env for production)
default_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
env_origins = os.getenv("ALLOWED_ORIGINS", "")
extra_origins = [o.strip() for o in env_origins.split(",") if o.strip()]
allowed_origins = default_origins + extra_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(pipeline.router)
app.include_router(data.router)
app.include_router(ws.router)


@app.on_event("startup")
async def startup():
    """Initialize the database on app startup."""
    # Ensure data directories exist
    os.makedirs(os.path.join(PROJECT_ROOT, "data", "input"), exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT, "data", "quarantine"), exist_ok=True)
    os.makedirs(os.path.join(PROJECT_ROOT, "logs"), exist_ok=True)
    init_database()
    logger.info("FluxCLI API started successfully")


@app.get("/", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "FluxCLI API"}
