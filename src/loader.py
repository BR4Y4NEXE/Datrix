import sqlite3
import json
import logging
from config.settings import settings
import pandas as pd
from typing import Tuple, List

logger = logging.getLogger(__name__)


class DataLoader:
    def __init__(self, db_path: str = settings.db.db_path):
        self.db_path = db_path

    def init_db(self):
        """Creates tables if they don't exist (delegates to database.py)."""
        from backend.database import init_database
        init_database()

    def save_schema(self, run_id: str, schema: list):
        """Save column schema metadata for a pipeline run."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for i, col_schema in enumerate(schema):
                    conn.execute(
                        """INSERT INTO dataset_schema
                           (run_id, column_name, column_type, original_name, column_order)
                           VALUES (?, ?, ?, ?, ?)""",
                        (run_id, col_schema.name, col_schema.dtype,
                         col_schema.original_name, i)
                    )
                conn.commit()
            logger.info(f"Saved schema with {len(schema)} columns for run {run_id}")
        except Exception as e:
            logger.error(f"Error saving schema: {e}")
            raise

    def load_data(self, df: pd.DataFrame, run_id: str) -> Tuple[int, int]:
        """
        Loads data into the datasets table as JSON rows.
        Returns (inserted_count, updated_count).
        Since each run creates new rows, updated_count is always 0.
        """
        if df.empty:
            return 0, 0

        inserted = 0

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Convert DataFrame rows to JSON and insert
                rows_to_insert = []
                for idx, row in df.iterrows():
                    # Convert row to dict, handling NaN values
                    row_dict = {}
                    for col, val in row.items():
                        if pd.isna(val):
                            row_dict[col] = None
                        elif isinstance(val, float) and val == int(val):
                            row_dict[col] = int(val)
                        else:
                            row_dict[col] = val
                    rows_to_insert.append(
                        (run_id, idx, json.dumps(row_dict, default=str))
                    )

                cursor.executemany(
                    """INSERT INTO datasets (run_id, row_index, data)
                       VALUES (?, ?, ?)""",
                    rows_to_insert
                )

                conn.commit()
                inserted = len(rows_to_insert)

                return inserted, 0

        except Exception as e:
            logger.error(f"Error loading data to DB: {e}")
            raise
