import pandas as pd
import logging
from dateutil import parser
import re
from dataclasses import dataclass
from typing import Tuple, Optional

logger = logging.getLogger(__name__)

@dataclass
class TransformResult:
    valid_df: pd.DataFrame
    rejected_df: pd.DataFrame
    total_processed: int
    total_valid: int
    total_rejected: int

def clean_price(price_str: str) -> Optional[float]:
    """
    Extracts numeric price from string.
    Examples: "$1,200.00" -> 1200.0, "USD 500" -> 500.0
    Returns None if parsing fails or result <= 0.
    """
    if isinstance(price_str, (int, float)):
        return float(price_str) if price_str > 0 else None
    
    if not isinstance(price_str, str):
        return None

    # Remove currency symbols and text (keep digits and dots/commas)
    # Using regex to find the first number group
    # Handling 1,200.00 -> 1200.00
    cleaned = re.sub(r'[^\d.,]', '', price_str)
    
    if not cleaned:
        return None

    try:
        # Simple heuristic: if '.' and ',' are both present, 
        # assume ',' is thousands separator if it comes before '.'
        # or if ',' is thousands sep if it appears multiple times.
        # Ideally, we remove ',' unless it's a decimal comma (European), 
        # but user context implies US/Standard format "$1,200.00".
        
        # Standardize: remove ','
        standardized = cleaned.replace(',', '')
        val = float(standardized)
        return val if val > 0 else None
    except ValueError:
        return None

def clean_date(date_str: str) -> Optional[str]:
    """
    Parses date string to YYYY-MM-DD.
    Returns None if invalid.
    """
    if pd.isna(date_str) or date_str == "":
        return None
        
    try:
        dt = parser.parse(str(date_str))
        return dt.strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        return None

def clean_quantity(qty) -> int:
    """
    Parses quantity. Returns 0 if invalid (which will be rejected later).
    """
    try:
        q = int(qty)
        return q if q > 0 else 0
    except (ValueError, TypeError):
        return 0

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names to the expected schema: ID, Date, Product, Qty, Price, Store_ID.
    Uses case-insensitive matching and common aliases.
    """
    # Strip whitespace from column names
    df.columns = df.columns.str.strip()
    
    # Define mapping: expected_name -> list of common aliases (all lowercase for matching)
    column_aliases = {
        'ID': ['id', 'item_id', 'transaction_id', 'order_id', 'sale_id', 'record_id', 'no', 'num', 'number', '#'],
        'Date': ['date', 'fecha', 'sale_date', 'order_date', 'transaction_date', 'dt', 'created_at'],
        'Product': ['product', 'producto', 'product_name', 'product_category', 'product_id', 'item', 'item_name', 'description', 'desc', 'nombre', 'category'],
        'Qty': ['qty', 'quantity', 'cantidad', 'units', 'count', 'amount', 'qty_sold', 'quantity_sold', 'units_sold'],
        'Price': ['price', 'precio', 'unit_price', 'cost', 'valor', 'value', 'price_usd', 'total_revenue', 'sale_price'],
        'Store_ID': ['store_id', 'storeid', 'store', 'tienda', 'branch', 'branch_id', 'location', 'location_id', 'sucursal', 'customer_region', 'region', 'channel'],
    }
    
    rename_map = {}
    lower_cols = {col.lower(): col for col in df.columns}
    
    for expected_name, aliases in column_aliases.items():
        # Skip if column already exists with exact name
        if expected_name in df.columns:
            continue
        # Try to find a match from aliases
        for alias in aliases:
            if alias in lower_cols:
                rename_map[lower_cols[alias]] = expected_name
                break
    
    if rename_map:
        logger.info(f"Column mapping applied: {rename_map}")
        df = df.rename(columns=rename_map)
    
    return df


def transform(df: pd.DataFrame) -> TransformResult:
    """
    Applies cleaning rules and separates valid vs invalid rows.
    """
    total = len(df)
    
    # Normalize column names to handle different CSV formats
    df = normalize_columns(df)
    
    # Validate required columns exist
    required = ['ID', 'Date', 'Product', 'Qty', 'Price', 'Store_ID']
    missing = [col for col in required if col not in df.columns]
    if missing:
        available = list(df.columns)
        raise KeyError(
            f"Missing required columns after normalization: {missing}. "
            f"Available columns: {available}. "
            f"Please ensure your CSV has columns matching: {required}"
        )
    
    # Work on a copy to avoid SettingWithCopy warnings on input df
    processing_df = df.copy()
    
    # Initialize reject reason column
    processing_df['reject_reason'] = ""
    
    # 1. Clean ID
    # Rule: ID not empty
    processing_df['clean_id'] = processing_df['ID'].astype(str).str.strip()
    
    # 2. Clean Date
    processing_df['clean_date'] = processing_df['Date'].apply(clean_date)
    
    # 3. Clean Price
    processing_df['clean_price'] = processing_df['Price'].apply(clean_price)
    
    # 4. Clean Qty
    processing_df['clean_qty'] = processing_df['Qty'].apply(clean_quantity)
    
    # 5. Clean Store_ID (ensure it's valid, loosely)
    processing_df['clean_store_id'] = processing_df['Store_ID'].fillna('').astype(str)

    # Validation Logic
    def validate_row(row):
        reasons = []
        if not row['clean_id'] or str(row['clean_id']).lower() == 'nan':
            reasons.append("Missing ID")
        if row['clean_date'] is None:
            reasons.append("Invalid Date")
        if row['clean_price'] is None:
            reasons.append("Invalid Price (<=0 or parse error)")
        if row['clean_qty'] <= 0:
            reasons.append("Invalid Quantity (<=0)")
        
        return "; ".join(reasons)

    processing_df['reject_reason'] = processing_df.apply(validate_row, axis=1)
    
    # Split
    valid_mask = processing_df['reject_reason'] == ""
    
    # Finalize Valid DF
    # Select only clean columns and rename them back to standard names if needed,
    # or keep them as map to DB columns.
    # Let's map to DB schema: id, date, product, qty, price, store_id
    
    valid_df = processing_df.loc[valid_mask].copy()
    valid_df = valid_df[['clean_id', 'clean_date', 'Product', 'clean_qty', 'clean_price', 'clean_store_id']]
    valid_df.columns = ['id', 'date', 'product', 'qty', 'price', 'store_id']
    
    # Finalize Rejected DF
    # Keep original data + reason
    rejected_df = processing_df.loc[~valid_mask].copy()
    # Keep original columns for debugging + reason
    rejected_df = rejected_df[['ID', 'Date', 'Product', 'Qty', 'Price', 'Store_ID', 'reject_reason']]
    
    return TransformResult(
        valid_df=valid_df,
        rejected_df=rejected_df,
        total_processed=total,
        total_valid=len(valid_df),
        total_rejected=len(rejected_df)
    )
