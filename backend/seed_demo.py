"""Seed one fixed demo run (run_id='demo') so the dashboard is always populated.

Idempotent: skips if the 'demo' run already exists. Generates a small realistic
sales CSV once and runs it through the real transformer + loader so pipeline_runs,
datasets and dataset_schema look exactly like a genuine run.
"""
import os
import sys
import csv
import random
import datetime
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src import extractor, transformer, loader
from backend.database import get_connection

logger = logging.getLogger(__name__)

DEMO_RUN_ID = "demo"
DEMO_CSV = os.path.join(PROJECT_ROOT, "data", "demo_sales.csv")

_PRODUCTS = [
    ("Laptop Pro 15", "Electronics", 1299.00),
    ("Wireless Mouse", "Accessories", 24.99),
    ("Mechanical Keyboard", "Accessories", 89.50),
    ("4K Monitor", "Electronics", 349.00),
    ("USB-C Hub", "Accessories", 39.95),
    ("Noise-Cancel Headset", "Audio", 199.00),
    ("Webcam HD", "Electronics", 79.00),
    ("Standing Desk", "Furniture", 459.00),
    ("Ergo Chair", "Furniture", 289.00),
    ("Desk Lamp", "Furniture", 34.50),
]
_REGIONS = ["North", "South", "East", "West", "Central"]


def _generate_csv(path: str, rows: int = 60):
    """Write a deterministic, clean sales CSV (~60 rows)."""
    random.seed(42)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    start = datetime.date(2025, 1, 1)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Date", "Product", "Category", "Region", "Quantity", "Unit Price", "Revenue"])
        for i in range(rows):
            product, category, price = random.choice(_PRODUCTS)
            qty = random.randint(1, 12)
            day = start + datetime.timedelta(days=i)
            w.writerow([
                day.isoformat(), product, category, random.choice(_REGIONS),
                qty, f"{price:.2f}", f"{price * qty:.2f}",
            ])


def seed_demo():
    """Idempotently create the 'demo' pipeline run."""
    with get_connection() as conn:
        exists = conn.execute(
            "SELECT 1 FROM pipeline_runs WHERE id = ?", (DEMO_RUN_ID,)
        ).fetchone()
    if exists:
        return

    if not os.path.exists(DEMO_CSV):
        _generate_csv(DEMO_CSV)

    df = extractor.extract_csv(DEMO_CSV)
    result = transformer.transform(df, strict=False)

    data_loader = loader.DataLoader()
    data_loader.init_db()
    data_loader.save_schema(DEMO_RUN_ID, result.schema)
    inserts, updates = data_loader.load_data(result.valid_df, DEMO_RUN_ID)

    now = datetime.datetime.now().isoformat()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO pipeline_runs
               (id, status, file_name, dry_run, started_at, finished_at, duration,
                total_read, total_valid, total_rejected, db_inserts, db_updates)
               VALUES (?, 'SUCCESS', 'demo_sales.csv', 0, ?, ?, 0.0, ?, ?, ?, ?, ?)""",
            (DEMO_RUN_ID, now, now, len(df), result.total_valid,
             result.total_rejected, inserts, updates),
        )
        conn.commit()
    logger.info(f"Seeded demo run with {inserts} rows")
