import sqlite3
import os
import sys
import logging

# Add project root to path so we can import src/ and config/
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config.settings import settings

logger = logging.getLogger(__name__)

DB_PATH = settings.db.db_path


def get_connection() -> sqlite3.Connection:
    """Get a SQLite connection with row_factory for dict-like access."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize both the sales table and pipeline_runs table."""
    with get_connection() as conn:
        # Sales table (same as existing loader.py)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales (
                id TEXT PRIMARY KEY,
                date TEXT,
                product TEXT,
                qty INTEGER,
                price REAL,
                store_id TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Pipeline runs history table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_runs (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'PENDING',
                file_name TEXT NOT NULL,
                dry_run INTEGER NOT NULL DEFAULT 0,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                duration REAL,
                total_read INTEGER,
                total_valid INTEGER,
                total_rejected INTEGER,
                db_inserts INTEGER,
                db_updates INTEGER,
                error_message TEXT
            );
        """)

        conn.commit()
        logger.info("Database tables initialized.")
