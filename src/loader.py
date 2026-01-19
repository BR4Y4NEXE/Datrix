import sqlite3
import logging
from config.settings import settings
import pandas as pd
from typing import Tuple

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, db_path: str = settings.db.db_path):
        self.db_path = db_path

    def init_db(self):
        """Creates the table if it doesn't exist."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS sales (
            id TEXT PRIMARY KEY,
            date TEXT,
            product TEXT,
            qty INTEGER,
            price REAL,
            store_id TEXT,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(create_table_sql)
            logger.info("Database initialized/verified.")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def load_data(self, df: pd.DataFrame) -> Tuple[int, int]:
        """
        Upserts data into SQLite.
        Returns (inserted_count, updated_count).
        Note: SQLite's UPSERT syntax: INSERT ... ON CONFLICT DO UPDATE
        """
        if df.empty:
            return 0, 0
            
        inserted = 0
        updated = 0
        
        upsert_sql = """
        INSERT INTO sales (id, date, product, qty, price, store_id, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            date=excluded.date,
            product=excluded.product,
            qty=excluded.qty,
            price=excluded.price,
            store_id=excluded.store_id,
            last_updated=CURRENT_TIMESTAMP
        """
        
        # We need to calculate inserted vs updated.
        # SQLite doesn't easily return counts for each. 
        # Standard approach: 
        # 1. Try INSERT OR IGNORE, count changes -> inserts
        # 2. UPDATE ... WHERE id IN (...) -> updates
        # OR just run UPSERT and Count 'total changes', but that is sum.
        # For this requirement, to get distinct counts, it's expensive.
        # "Load: 468 inserted, 10 updated"
        
        # Strategy:
        # Check existing IDs
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Identify existing IDs to count updates
                ids = tuple(df['id'].astype(str).tolist())
                # If only 1 item, it needs a trailing comma for tuple syntax e.g. ('1',)
                # Python tuple() handles that but SQL "IN (?)" needs placeholders.
                
                placeholders = ','.join(['?'] * len(ids))
                existing_query = f"SELECT id FROM sales WHERE id IN ({placeholders})"
                
                cursor.execute(existing_query, ids)
                existing_ids = set(row[0] for row in cursor.fetchall())
                
                # Count
                total_rows = len(df)
                updates_count = sum(1 for x in ids if x in existing_ids)
                inserts_count = total_rows - updates_count
                
                # Execute UPSERT in batch
                # Convert DF to list of tuples
                data = df.to_records(index=False).tolist()
                cursor.executemany(upsert_sql, data)
                
                conn.commit()
                
                return inserts_count, updates_count
                
        except Exception as e:
            logger.error(f"Error loading data to DB: {e}")
            raise
