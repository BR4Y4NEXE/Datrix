import os
import sys
import uuid
import asyncio
import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional, List

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.settings import settings
from backend.database import get_connection
from backend.models import PipelineRunResponse
from backend.services.pipeline_runner import run_pipeline

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

# Thread pool for running ETL in background
executor = ThreadPoolExecutor(max_workers=2)


@router.post("/run", response_model=dict)
async def launch_pipeline(
    file: Optional[UploadFile] = File(None),
    dry_run: bool = Form(False),
    auto_detect: bool = Form(False),
):
    """
    Launch the ETL pipeline with an uploaded CSV file or auto-detect mode.
    Returns a run_id that can be used to track progress via WebSocket.
    """
    run_id = str(uuid.uuid4())

    if auto_detect:
        # Auto-detect today's file
        today = datetime.date.today().strftime("%Y%m%d")
        expected_filename = f"sales_{today}.csv"
        file_path = os.path.join(settings.app.input_dir, expected_filename)
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=404,
                detail=f"Auto-detection failed: {expected_filename} not found in {settings.app.input_dir}"
            )
    elif file:
        # Save uploaded file to input directory
        os.makedirs(settings.app.input_dir, exist_ok=True)
        file_path = os.path.join(settings.app.input_dir, file.filename)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"Saved uploaded file to {file_path}")
    else:
        raise HTTPException(
            status_code=400,
            detail="Either upload a CSV file or set auto_detect=true"
        )

    # Get the current event loop for WebSocket broadcasting
    loop = asyncio.get_event_loop()

    # Run pipeline in a thread to avoid blocking the event loop
    executor.submit(run_pipeline, run_id, file_path, dry_run, loop)

    return {
        "run_id": run_id,
        "status": "RUNNING",
        "message": f"Pipeline started. Connect to /ws/logs/{run_id} for live logs."
    }


@router.get("/runs", response_model=List[PipelineRunResponse])
async def get_runs(limit: int = 50, offset: int = 0):
    """Get pipeline execution history, most recent first."""
    with get_connection() as conn:
        cursor = conn.execute(
            """SELECT id, status, file_name, dry_run, started_at, finished_at,
                      duration, total_read, total_valid, total_rejected,
                      db_inserts, db_updates, error_message
               FROM pipeline_runs
               ORDER BY started_at DESC
               LIMIT ? OFFSET ?""",
            (limit, offset)
        )
        rows = cursor.fetchall()

    return [
        PipelineRunResponse(
            id=row["id"],
            status=row["status"],
            file_name=row["file_name"],
            dry_run=bool(row["dry_run"]),
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            duration=row["duration"],
            total_read=row["total_read"],
            total_valid=row["total_valid"],
            total_rejected=row["total_rejected"],
            db_inserts=row["db_inserts"],
            db_updates=row["db_updates"],
            error_message=row["error_message"],
        )
        for row in rows
    ]


@router.get("/runs/{run_id}", response_model=PipelineRunResponse)
async def get_run(run_id: str):
    """Get a specific pipeline run detail."""
    with get_connection() as conn:
        cursor = conn.execute(
            """SELECT id, status, file_name, dry_run, started_at, finished_at,
                      duration, total_read, total_valid, total_rejected,
                      db_inserts, db_updates, error_message
               FROM pipeline_runs WHERE id = ?""",
            (run_id,)
        )
        row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Run not found")

    return PipelineRunResponse(
        id=row["id"],
        status=row["status"],
        file_name=row["file_name"],
        dry_run=bool(row["dry_run"]),
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        duration=row["duration"],
        total_read=row["total_read"],
        total_valid=row["total_valid"],
        total_rejected=row["total_rejected"],
        db_inserts=row["db_inserts"],
        db_updates=row["db_updates"],
        error_message=row["error_message"],
    )
