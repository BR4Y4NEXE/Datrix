import pytest
import pandas as pd
from src.transformer import clean_price, clean_date, clean_quantity, transform

def test_clean_price():
    assert clean_price("$1,200.00") == 1200.0
    assert clean_price("USD 500") == 500.0
    assert clean_price("500") == 500.0
    assert clean_price("-10") is None
    assert clean_price("Free") is None

def test_clean_date():
    assert clean_date("2025-01-01") == "2025-01-01"
    assert clean_date("01/01/2025") == "2025-01-01"
    assert clean_date("Jan 1, 2025") == "2025-01-01"
    assert clean_date("Invalid") is None

def test_clean_quantity():
    assert clean_quantity("5") == 5
    assert clean_quantity(5) == 5
    assert clean_quantity(-1) == 0
    assert clean_quantity("two") == 0

def test_transform_logic():
    data = {
        "ID": ["1", "2", "3", ""],
        "Date": ["2025-01-01", "Invalid", "2025-01-03", "2025-01-04"],
        "Product": ["A", "B", "C", "D"],
        "Qty": [1, 1, -5, 1],         
        "Price": ["100", "100", "100", "100"],
        "Store_ID": ["101", "101", "101", "101"]
    }
    df = pd.DataFrame(data)
    
    result = transform(df)
    
    # Row 1: Valid
    # Row 2: Invalid Date
    # Row 3: Invalid Qty
    # Row 4: Missing ID
    
    assert result.total_processed == 4
    assert result.total_valid == 1
    assert result.total_rejected == 3
    
    valid_ids = result.valid_df['id'].tolist()
    assert "1" in valid_ids
    
    rejected_reasons = result.rejected_df['reject_reason'].tolist()
    assert "Invalid Date" in str(rejected_reasons[0]) or "Invalid Date" in str(rejected_reasons[1])
