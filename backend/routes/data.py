import os
import sys
import math
import logging
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
from config.settings import settings
from backend.database import get_connection
from backend.models import (
    SalesRecordResponse, PaginatedRecords,
    QuarantineFile, QuarantineDetail, QuarantineRow,
    NotificationStatus
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Data"])


@router.get("/data/records", response_model=PaginatedRecords)
async def get_records(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    product: Optional[str] = None,
    store_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
):
    """Query sales records with pagination and filters."""
    conditions = []
    params = []

    if product:
        conditions.append("product LIKE ?")
        params.append(f"%{product}%")
    if store_id:
        conditions.append("store_id = ?")
        params.append(store_id)
    if date_from:
        conditions.append("date >= ?")
        params.append(date_from)
    if date_to:
        conditions.append("date <= ?")
        params.append(date_to)
    if search:
        conditions.append("(product LIKE ? OR id LIKE ? OR store_id LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    with get_connection() as conn:
        # Count total
        count_row = conn.execute(
            f"SELECT COUNT(*) as cnt FROM sales WHERE {where_clause}", params
        ).fetchone()
        total = count_row["cnt"]

        # Fetch page
        offset = (page - 1) * per_page
        rows = conn.execute(
            f"""SELECT id, date, product, qty, price, store_id, last_updated
                FROM sales WHERE {where_clause}
                ORDER BY last_updated DESC
                LIMIT ? OFFSET ?""",
            params + [per_page, offset]
        ).fetchall()

    records = [
        SalesRecordResponse(
            id=r["id"], date=r["date"], product=r["product"],
            qty=r["qty"], price=r["price"], store_id=r["store_id"],
            last_updated=r["last_updated"]
        )
        for r in rows
    ]

    return PaginatedRecords(
        records=records,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=max(1, math.ceil(total / per_page)),
    )


@router.get("/quarantine", response_model=List[QuarantineFile])
async def list_quarantine_files():
    """List all quarantine error report CSV files."""
    q_dir = settings.app.quarantine_dir
    if not os.path.exists(q_dir):
        return []

    files = []
    for fname in sorted(os.listdir(q_dir), reverse=True):
        if fname.endswith(".csv"):
            fpath = os.path.join(q_dir, fname)
            try:
                df = pd.read_csv(fpath)
                row_count = len(df)
            except Exception:
                row_count = 0

            stat = os.stat(fpath)
            created = os.path.getmtime(fpath)
            import datetime
            created_at = datetime.datetime.fromtimestamp(created).isoformat()

            files.append(QuarantineFile(
                filename=fname,
                row_count=row_count,
                created_at=created_at,
            ))

    return files


@router.get("/quarantine/{filename}", response_model=QuarantineDetail)
async def get_quarantine_file(filename: str):
    """Get the contents of a specific quarantine file."""
    q_dir = settings.app.quarantine_dir
    fpath = os.path.join(q_dir, filename)

    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Quarantine file not found")

    try:
        df = pd.read_csv(fpath)
        df = df.fillna("")
        rows = [
            QuarantineRow(**{col: str(val) for col, val in row.items()})
            for _, row in df.iterrows()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")

    return QuarantineDetail(
        filename=filename,
        rows=rows,
        total=len(rows),
    )


@router.get("/data/analytics")
async def get_analytics():
    """Aggregate sales data for charts: by product, by store, over time, and data quality."""
    with get_connection() as conn:
        # Sales by product (top 10 by revenue)
        by_product = conn.execute("""
            SELECT product, SUM(qty) as total_qty, SUM(qty * price) as revenue, COUNT(*) as count
            FROM sales GROUP BY product ORDER BY revenue DESC LIMIT 10
        """).fetchall()

        # Sales by store
        by_store = conn.execute("""
            SELECT store_id, SUM(qty) as total_qty, SUM(qty * price) as revenue, COUNT(*) as count
            FROM sales GROUP BY store_id ORDER BY revenue DESC LIMIT 10
        """).fetchall()

        # Sales trend over time (by date)
        over_time = conn.execute("""
            SELECT date, SUM(qty) as total_qty, SUM(qty * price) as revenue, COUNT(*) as count
            FROM sales GROUP BY date ORDER BY date
        """).fetchall()

        # Overall stats
        summary_row = conn.execute("""
            SELECT COUNT(*) as total_records,
                   COALESCE(SUM(qty), 0) as total_qty,
                   COALESCE(SUM(qty * price), 0) as total_revenue,
                   COUNT(DISTINCT product) as unique_products,
                   COUNT(DISTINCT store_id) as unique_stores
            FROM sales
        """).fetchone()

        # Data quality from pipeline_runs
        quality = conn.execute("""
            SELECT id, file_name, status, total_read, total_valid, total_rejected,
                   db_inserts, db_updates, started_at
            FROM pipeline_runs ORDER BY started_at DESC LIMIT 20
        """).fetchall()

    return {
        "by_product": [
            {"product": r["product"], "qty": r["total_qty"],
             "revenue": round(r["revenue"], 2), "count": r["count"]}
            for r in by_product
        ],
        "by_store": [
            {"store_id": r["store_id"], "qty": r["total_qty"],
             "revenue": round(r["revenue"], 2), "count": r["count"]}
            for r in by_store
        ],
        "over_time": [
            {"date": r["date"], "qty": r["total_qty"],
             "revenue": round(r["revenue"], 2), "count": r["count"]}
            for r in over_time
        ],
        "summary": {
            "total_records": summary_row["total_records"],
            "total_qty": summary_row["total_qty"],
            "total_revenue": round(summary_row["total_revenue"], 2),
            "unique_products": summary_row["unique_products"],
            "unique_stores": summary_row["unique_stores"],
        },
        "quality": [
            {"id": r["id"], "file_name": r["file_name"], "status": r["status"],
             "total_read": r["total_read"], "total_valid": r["total_valid"],
             "total_rejected": r["total_rejected"],
             "db_inserts": r["db_inserts"], "db_updates": r["db_updates"],
             "started_at": r["started_at"]}
            for r in quality
        ],
    }


@router.get("/data/export")
async def export_csv():
    """Export all sales data as a downloadable CSV."""
    from fastapi.responses import StreamingResponse
    import io, csv

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, date, product, qty, price, store_id, last_updated FROM sales ORDER BY date"
        ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "date", "product", "qty", "price", "store_id", "last_updated"])
    for r in rows:
        writer.writerow([r["id"], r["date"], r["product"], r["qty"], r["price"],
                         r["store_id"], r["last_updated"]])
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=fluxcli_sales_export.csv"},
    )

