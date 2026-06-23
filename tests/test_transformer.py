import pytest
import pandas as pd
from src.transformer import (
    clean_numeric_value, clean_date_value, clean_text_value,
    detect_column_type, transform
)


def test_clean_numeric_value():
    assert clean_numeric_value("$1,200.00") == 1200.0
    assert clean_numeric_value("USD 500") == 500.0
    assert clean_numeric_value("500") == 500.0
    assert clean_numeric_value(42) == 42.0
    assert clean_numeric_value(3.14) == 3.14
    assert clean_numeric_value("") is None
    assert clean_numeric_value(None) is None
    assert clean_numeric_value("Free") is None


def test_clean_date_value():
    assert clean_date_value("2025-01-01") == "2025-01-01"
    assert clean_date_value("01/01/2025") == "2025-01-01"
    assert clean_date_value("Jan 1, 2025") == "2025-01-01"
    assert clean_date_value("Invalid") is None
    assert clean_date_value("") is None
    assert clean_date_value(None) is None


def test_clean_text_value():
    assert clean_text_value("  hello  ") == "hello"
    assert clean_text_value(None) == ""
    assert clean_text_value(123) == "123"


def test_detect_column_type_numeric():
    series = pd.Series(["100", "200.5", "$300", "400", "500"])
    assert detect_column_type(series) == "numeric"


def test_detect_column_type_date():
    series = pd.Series(["2025-01-01", "2025-02-15", "Jan 3, 2025", "2025-04-10"])
    assert detect_column_type(series) == "date"


def test_detect_column_type_text():
    series = pd.Series(["Apple", "Banana", "Cherry", "Date"])
    assert detect_column_type(series) == "text"


def test_detect_column_type_empty():
    series = pd.Series([None, None, None])
    assert detect_column_type(series) == "text"


def test_transform_dynamic_sales_csv():
    """Test with a typical sales CSV (like the original schema)."""
    data = {
        "ID": ["1", "2", "3", ""],
        "Date": ["2025-01-01", "Invalid", "2025-01-03", "2025-01-04"],
        "Product": ["A", "B", "C", "D"],
        "Qty": [1, 1, 5, 1],
        "Price": ["100", "100", "100", "100"],
        "Store_ID": ["101", "101", "101", "101"]
    }
    df = pd.DataFrame(data)
    result = transform(df)

    assert result.total_processed == 4
    # Strict mode (default): the "Invalid" date row is quarantined; the empty-ID
    # row is just NULL (empty original, not a parse failure) and still passes.
    assert result.total_valid == 3
    assert result.total_rejected == 1
    assert "Fecha inválida" in result.rejected_df["reject_reason"].iloc[0]
    assert len(result.schema) == 6

    # Check schema detected correct types
    schema_types = {s.name: s.dtype for s in result.schema}
    assert schema_types["qty"] == "numeric"
    assert schema_types["price"] == "numeric"
    assert schema_types["product"] == "text"
    assert schema_types["store_id"] == "numeric"  # "101" etc. detected as numeric


def test_transform_amazon_csv():
    """Test with an Amazon-style CSV — completely different columns."""
    data = {
        "order_id": ["A001", "A002", "A003"],
        "order_date": ["2025-01-15", "2025-02-20", "2025-03-10"],
        "product_category": ["Electronics", "Books", "Home"],
        "quantity_sold": [2, 5, 1],
        "price": [29.99, 14.50, 89.00],
        "discount_percent": [10, 0, 15],
        "customer_region": ["North", "South", "East"],
        "rating": [4.5, 3.8, 4.2],
    }
    df = pd.DataFrame(data)
    result = transform(df)

    assert result.total_processed == 3
    assert result.total_valid == 3
    assert result.total_rejected == 0
    assert len(result.schema) == 8

    schema_types = {s.name: s.dtype for s in result.schema}
    assert schema_types["price"] == "numeric"
    assert schema_types["quantity_sold"] == "numeric"
    assert schema_types["rating"] == "numeric"
    assert schema_types["product_category"] == "text"
    assert schema_types["customer_region"] == "text"
    assert schema_types["order_date"] == "date"


# Enough clean rows that type detection holds (>0.7), plus one corrupt cell.
_GOOD_DATES = [f"2025-01-0{i}" for i in range(1, 10)]  # 9 valid dates
_GOOD_QTYS = [str(i) for i in range(1, 10)]            # 9 valid numerics


def test_strict_quarantines_invalid_date():
    """A date column with an unparseable value sends that row to quarantine."""
    data = {
        "Date": _GOOD_DATES + ["2025/13/45"],
        "Qty": _GOOD_QTYS + ["10"],
    }
    result = transform(pd.DataFrame(data), strict=True)
    assert result.total_rejected == 1
    assert result.total_valid == 9
    assert "Fecha inválida" in result.rejected_df["reject_reason"].iloc[0]


def test_strict_quarantines_invalid_numeric():
    """A numeric column with garbage text sends that row to quarantine."""
    data = {
        "Date": _GOOD_DATES + ["2025-01-10"],
        "Qty": _GOOD_QTYS + ["two"],
    }
    result = transform(pd.DataFrame(data), strict=True)
    assert result.total_rejected == 1
    assert "Numérico inválido" in result.rejected_df["reject_reason"].iloc[0]


def test_strict_keeps_empty_cells_valid():
    """An empty (not unparseable) typed cell is NULL, not a parse failure."""
    data = {
        "Date": _GOOD_DATES + [""],
        "Qty": _GOOD_QTYS + ["10"],
    }
    result = transform(pd.DataFrame(data), strict=True)
    assert result.total_rejected == 0
    assert result.total_valid == 10


def test_lax_mode_passes_dirty_rows():
    """strict=False restores the legacy behavior: parse failures become NULL."""
    data = {
        "Date": _GOOD_DATES + ["2025/13/45"],
        "Qty": _GOOD_QTYS + ["10"],  # only Date is corrupt, so the row isn't fully empty
    }
    result = transform(pd.DataFrame(data), strict=False)
    assert result.total_rejected == 0
    assert result.total_valid == 10


def test_transform_empty_rows_rejected():
    """Rows where all fields are empty should be rejected."""
    data = {
        "Name": ["Alice", "", None],
        "Score": [95, None, None],
    }
    df = pd.DataFrame(data)
    result = transform(df)

    assert result.total_processed == 3
    assert result.total_valid >= 1  # At least Alice
    assert result.total_rejected >= 1  # At least the fully empty row
