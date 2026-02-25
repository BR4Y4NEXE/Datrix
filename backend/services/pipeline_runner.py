import os
import sys
import time
import uuid
import datetime
import logging
import asyncio

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src import extractor, transformer, loader, notifier
from config.settings import settings
from backend.database import get_connection
from backend.services.log_handler import WebSocketLogHandler

logger = logging.getLogger(__name__)


def create_run_record(run_id: str, file_name: str, dry_run: bool):
    """Insert a new pipeline_runs record with RUNNING status."""
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO pipeline_runs
               (id, status, file_name, dry_run, started_at)
               VALUES (?, 'RUNNING', ?, ?, ?)""",
            (run_id, file_name, int(dry_run),
             datetime.datetime.now().isoformat())
        )
        conn.commit()


def update_run_record(run_id: str, **kwargs):
    """Update a pipeline_runs record with final metrics."""
    sets = ", ".join(f"{k}=?" for k in kwargs.keys())
    vals = list(kwargs.values()) + [run_id]
    with get_connection() as conn:
        conn.execute(
            f"UPDATE pipeline_runs SET {sets} WHERE id=?", vals
        )
        conn.commit()


def run_pipeline(run_id: str, file_path: str, dry_run: bool = False,
                 loop: asyncio.AbstractEventLoop = None):
    """
    Execute the full ETL pipeline (Extract → Transform → Load → Notify).
    This runs synchronously in a thread and uses WebSocketLogHandler
    to stream logs to connected clients.
    """
    # Setup per-run logging handler
    ws_handler = WebSocketLogHandler(run_id, loop=loop)
    ws_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )

    # Attach handler to root logger to capture all ETL module logs
    root_logger = logging.getLogger()
    root_logger.addHandler(ws_handler)

    file_name = os.path.basename(file_path)
    create_run_record(run_id, file_name, dry_run)

    start_time = time.time()
    logger.info(f"[Run {run_id}] Starting ETL for {file_path}")

    try:
        # 1. Extract
        df = extractor.extract_csv(file_path)
        total_read = len(df)
        logger.info(f"[Run {run_id}] Extract: {total_read} rows read")

        # 2. Transform (dynamic - auto-detects schema)
        result = transformer.transform(df)
        logger.info(
            f"[Run {run_id}] Transform: {result.total_valid} valid, "
            f"{result.total_rejected} rejected"
        )

        # Log detected schema
        for col in result.schema:
            logger.info(f"[Run {run_id}] Schema: {col.original_name} → {col.name} ({col.dtype})")

        # 3. Handle Quarantine
        if not result.rejected_df.empty:
            os.makedirs(settings.app.quarantine_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            q_filename = f"errors_{timestamp}.csv"
            q_path = os.path.join(settings.app.quarantine_dir, q_filename)
            result.rejected_df.to_csv(q_path, index=False)
            logger.info(
                f"[Run {run_id}] Quarantined {len(result.rejected_df)} rows to {q_path}"
            )

        # 4. Load (if not dry-run)
        inserts, updates = 0, 0
        if not dry_run:
            data_loader = loader.DataLoader()
            data_loader.init_db()
            # Save schema metadata
            data_loader.save_schema(run_id, result.schema)
            # Load data with run_id
            inserts, updates = data_loader.load_data(result.valid_df, run_id)
            logger.info(f"[Run {run_id}] Load: {inserts} inserted, {updates} updated")
        else:
            logger.info(f"[Run {run_id}] Dry run: Skipping DB load")

        duration = round(time.time() - start_time, 2)
        logger.info(f"[Run {run_id}] ETL COMPLETED SUCCESSFULLY in {duration}s")

        # Update run record
        update_run_record(
            run_id,
            status="SUCCESS",
            finished_at=datetime.datetime.now().isoformat(),
            duration=duration,
            total_read=total_read,
            total_valid=result.total_valid,
            total_rejected=result.total_rejected,
            db_inserts=inserts,
            db_updates=updates,
        )

        # 5. Notify (if not dry-run)
        summary = {
            "status": "SUCCESS",
            "duration": duration,
            "file_name": file_name,
            "total_read": total_read,
            "total_valid": result.total_valid,
            "total_rejected": result.total_rejected,
            "db_inserts": inserts,
            "db_updates": updates,
        }
        if not dry_run:
            try:
                notif = notifier.Notifier()
                notif.send_report(summary)
            except Exception as e:
                logger.warning(f"[Run {run_id}] Notification failed: {e}")

    except Exception as e:
        duration = round(time.time() - start_time, 2)
        logger.error(f"[Run {run_id}] ETL Failed: {e}", exc_info=True)
        update_run_record(
            run_id,
            status="FAILED",
            finished_at=datetime.datetime.now().isoformat(),
            duration=duration,
            error_message=str(e),
        )
    finally:
        # Clean up the handler
        root_logger.removeHandler(ws_handler)
