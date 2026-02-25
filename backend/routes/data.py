import os
import sys
import json
import math
import logging
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pandas as pd
from config.settings import settings
from backend.database import get_connection
from backend.models import (
    PaginatedRecords, DatasetSchemaResponse, ColumnSchemaResponse,
    QuarantineFile, QuarantineDetail,
    NotificationStatus
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Data"])


def _get_latest_run_id() -> Optional[str]:
    """Get the run_id of the latest successful pipeline run."""
    with get_connection() as conn:
        row = conn.execute(
            """SELECT id FROM pipeline_runs
               WHERE status = 'SUCCESS'
               ORDER BY started_at DESC LIMIT 1"""
        ).fetchone()
    return row["id"] if row else None


def _get_schema_for_run(run_id: str) -> List[Dict]:
    """Get column schema for a specific run."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT column_name, column_type, original_name, column_order
               FROM dataset_schema WHERE run_id = ?
               ORDER BY column_order""",
            (run_id,)
        ).fetchall()
    return [dict(r) for r in rows]


@router.get("/data/schema", response_model=DatasetSchemaResponse)
async def get_schema(run_id: Optional[str] = None):
    """Get the column schema for a dataset. Defaults to latest run."""
    if not run_id:
        run_id = _get_latest_run_id()
    if not run_id:
        raise HTTPException(status_code=404, detail="No successful pipeline runs found")

    schema = _get_schema_for_run(run_id)
    if not schema:
        raise HTTPException(status_code=404, detail="No schema found for this run")

    return DatasetSchemaResponse(
        run_id=run_id,
        columns=[
            ColumnSchemaResponse(
                column_name=s["column_name"],
                column_type=s["column_type"],
                original_name=s["original_name"],
                column_order=s["column_order"],
            )
            for s in schema
        ],
    )


@router.get("/data/records", response_model=PaginatedRecords)
async def get_records(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    run_id: Optional[str] = None,
):
    """Query dataset records with pagination and search."""
    if not run_id:
        run_id = _get_latest_run_id()
    if not run_id:
        return PaginatedRecords(
            records=[], total=0, page=1, per_page=per_page, total_pages=1
        )

    with get_connection() as conn:
        # Count total
        if search:
            count_row = conn.execute(
                "SELECT COUNT(*) as cnt FROM datasets WHERE run_id = ? AND data LIKE ?",
                (run_id, f"%{search}%")
            ).fetchone()
        else:
            count_row = conn.execute(
                "SELECT COUNT(*) as cnt FROM datasets WHERE run_id = ?",
                (run_id,)
            ).fetchone()

        total = count_row["cnt"]

        # Fetch page
        offset = (page - 1) * per_page
        if search:
            rows = conn.execute(
                """SELECT data FROM datasets
                   WHERE run_id = ? AND data LIKE ?
                   ORDER BY row_index
                   LIMIT ? OFFSET ?""",
                (run_id, f"%{search}%", per_page, offset)
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT data FROM datasets
                   WHERE run_id = ?
                   ORDER BY row_index
                   LIMIT ? OFFSET ?""",
                (run_id, per_page, offset)
            ).fetchall()

    records = [json.loads(r["data"]) for r in rows]

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

            import datetime
            created = os.path.getmtime(fpath)
            created_at = datetime.datetime.fromtimestamp(created).isoformat()

            files.append(QuarantineFile(
                filename=fname,
                row_count=row_count,
                created_at=created_at,
            ))

    return files


@router.get("/quarantine/{filename}", response_model=QuarantineDetail)
async def get_quarantine_file(filename: str):
    """Get the contents of a specific quarantine file (dynamic columns)."""
    q_dir = settings.app.quarantine_dir
    fpath = os.path.join(q_dir, filename)

    if not os.path.exists(fpath):
        raise HTTPException(status_code=404, detail="Quarantine file not found")

    try:
        df = pd.read_csv(fpath)
        df = df.fillna("")
        columns = list(df.columns)
        rows = [
            {col: str(val) for col, val in row.items()}
            for _, row in df.iterrows()
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")

    return QuarantineDetail(
        filename=filename,
        columns=columns,
        rows=rows,
        total=len(rows),
    )


@router.get("/data/analytics")
async def get_analytics(run_id: Optional[str] = None):
    """
    Dynamic analytics: auto-detects numeric and categorical columns
    from the dataset schema and generates aggregations.
    """
    if not run_id:
        run_id = _get_latest_run_id()
    if not run_id:
        return {
            "charts": [],
            "summary": {"total_records": 0, "columns": 0},
            "quality": [],
            "schema": [],
        }

    schema = _get_schema_for_run(run_id)
    numeric_cols = [s for s in schema if s["column_type"] == "numeric"]
    text_cols = [s for s in schema if s["column_type"] == "text"]
    date_cols = [s for s in schema if s["column_type"] == "date"]

    with get_connection() as conn:
        # Fetch all data for this run
        rows = conn.execute(
            "SELECT data FROM datasets WHERE run_id = ?", (run_id,)
        ).fetchall()

        total_records = len(rows)
        if total_records == 0:
            return {
                "charts": [],
                "summary": {"total_records": 0, "columns": len(schema)},
                "quality": [],
                "schema": schema,
            }

        # Parse all records
        records = [json.loads(r["data"]) for r in rows]
        df = pd.DataFrame(records)

        # Build summary
        summary = {"total_records": total_records, "columns": len(schema)}

        # Add numeric summaries
        numeric_summaries = []
        for nc in numeric_cols:
            col = nc["column_name"]
            if col in df.columns:
                series = pd.to_numeric(df[col], errors='coerce')
                numeric_summaries.append({
                    "column": col,
                    "original_name": nc["original_name"],
                    "sum": round(float(series.sum()), 2) if not series.empty else 0,
                    "avg": round(float(series.mean()), 2) if not series.empty else 0,
                    "min": round(float(series.min()), 2) if not series.empty else 0,
                    "max": round(float(series.max()), 2) if not series.empty else 0,
                })
        summary["numeric_columns"] = numeric_summaries

        # Add text column unique counts
        text_summaries = []
        for tc in text_cols:
            col = tc["column_name"]
            if col in df.columns:
                text_summaries.append({
                    "column": col,
                    "original_name": tc["original_name"],
                    "unique_values": int(df[col].nunique()),
                })
        summary["text_columns"] = text_summaries

        # Generate charts
        charts = []

        # Chart 1: For each categorical (text) column × first numeric column → bar chart
        if text_cols and numeric_cols:
            first_numeric = numeric_cols[0]["column_name"]
            for tc in text_cols[:3]:  # max 3 categorical charts
                cat_col = tc["column_name"]
                if cat_col in df.columns and first_numeric in df.columns:
                    df[first_numeric] = pd.to_numeric(df[first_numeric], errors='coerce')
                    grouped = df.groupby(cat_col)[first_numeric].agg(['sum', 'count']).reset_index()
                    grouped = grouped.sort_values('sum', ascending=False).head(10)
                    charts.append({
                        "type": "bar",
                        "title": f"{tc['original_name']} by {numeric_cols[0]['original_name']}",
                        "category_key": cat_col,
                        "value_key": "value",
                        "data": [
                            {
                                cat_col: str(row[cat_col]),
                                "value": round(float(row['sum']), 2),
                                "count": int(row['count'])
                            }
                            for _, row in grouped.iterrows()
                        ],
                    })

        # Chart 2: Date trend line chart (if date and numeric columns exist)
        if date_cols and numeric_cols:
            date_col = date_cols[0]["column_name"]
            first_numeric = numeric_cols[0]["column_name"]
            if date_col in df.columns and first_numeric in df.columns:
                df[first_numeric] = pd.to_numeric(df[first_numeric], errors='coerce')
                trend = df.groupby(date_col)[first_numeric].agg(['sum', 'count']).reset_index()
                trend = trend.sort_values(date_col)
                # If too many data points, sample
                if len(trend) > 60:
                    trend = trend.iloc[::len(trend)//60]
                charts.append({
                    "type": "line",
                    "title": f"{numeric_cols[0]['original_name']} over {date_cols[0]['original_name']}",
                    "x_key": date_col,
                    "y_key": "value",
                    "data": [
                        {
                            date_col: str(row[date_col]),
                            "value": round(float(row['sum']), 2),
                            "count": int(row['count'])
                        }
                        for _, row in trend.iterrows()
                    ],
                })

        # Chart 3: Distribution of first numeric column (histogram-like top values)
        if len(numeric_cols) > 1:
            for nc in numeric_cols[1:3]:  # next 2 numeric columns
                col = nc["column_name"]
                if col in df.columns:
                    series = pd.to_numeric(df[col], errors='coerce').dropna()
                    if not series.empty:
                        # Create bins
                        try:
                            binned = pd.cut(series, bins=min(10, len(series.unique())), duplicates='drop')
                            dist = binned.value_counts().sort_index()
                            charts.append({
                                "type": "bar",
                                "title": f"{nc['original_name']} Distribution",
                                "category_key": "range",
                                "value_key": "count",
                                "data": [
                                    {"range": str(interval), "count": int(count)}
                                    for interval, count in dist.items()
                                ],
                            })
                        except Exception:
                            pass

        # Data quality from pipeline_runs
        quality = conn.execute("""
            SELECT id, file_name, status, total_read, total_valid, total_rejected,
                   db_inserts, db_updates, started_at
            FROM pipeline_runs ORDER BY started_at DESC LIMIT 20
        """).fetchall()

    return {
        "charts": charts,
        "summary": summary,
        "schema": schema,
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
async def export_csv(run_id: Optional[str] = None):
    """Export dataset as a downloadable CSV (dynamic columns)."""
    from fastapi.responses import StreamingResponse
    import io, csv

    if not run_id:
        run_id = _get_latest_run_id()
    if not run_id:
        raise HTTPException(status_code=404, detail="No data to export")

    with get_connection() as conn:
        rows = conn.execute(
            "SELECT data FROM datasets WHERE run_id = ? ORDER BY row_index",
            (run_id,)
        ).fetchall()

    if not rows:
        raise HTTPException(status_code=404, detail="No data found for this run")

    records = [json.loads(r["data"]) for r in rows]

    # Get all column names from schema
    schema = _get_schema_for_run(run_id)
    columns = [s["column_name"] for s in schema] if schema else list(records[0].keys())

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
    writer.writeheader()
    for rec in records:
        writer.writerow(rec)
    output.seek(0)

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=datrix_export.csv"},
    )


@router.delete("/data/reset")
async def reset_database():
    """
    Clear all datasets, schemas, pipeline runs, and quarantine files.
    Allows uploading a completely new CSV for analysis.
    """
    try:
        with get_connection() as conn:
            conn.execute("DELETE FROM datasets")
            conn.execute("DELETE FROM dataset_schema")
            conn.execute("DELETE FROM pipeline_runs")
            conn.execute("DELETE FROM sales")  # legacy table
            conn.commit()

        # Also clear quarantine files
        q_dir = settings.app.quarantine_dir
        if os.path.exists(q_dir):
            import shutil
            for fname in os.listdir(q_dir):
                fpath = os.path.join(q_dir, fname)
                if fname.endswith(".csv"):
                    os.remove(fpath)

        logger.info("Database and quarantine files reset successfully")
        return {"status": "ok", "message": "All data cleared. Ready for a new CSV upload."}

    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {e}")

