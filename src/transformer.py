import pandas as pd
import logging
import re
from dateutil import parser
from dataclasses import dataclass, field
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)


@dataclass
class ColumnSchema:
    name: str
    dtype: str  # 'numeric', 'date', 'text'
    original_name: str  # Original CSV column name


@dataclass
class TransformResult:
    valid_df: pd.DataFrame
    rejected_df: pd.DataFrame
    total_processed: int
    total_valid: int
    total_rejected: int
    schema: List[ColumnSchema] = field(default_factory=list)


def detect_column_type(series: pd.Series) -> str:
    """
    Detect the type of a column: 'numeric', 'date', or 'text'.
    Uses heuristic sampling to determine the most likely type.
    """
    # Drop nulls for analysis
    clean = series.dropna().astype(str).str.strip()
    if clean.empty:
        return 'text'

    sample = clean.head(100)

    # Check numeric: try to parse as numbers (strip $, commas, etc.)
    numeric_count = 0
    for val in sample:
        cleaned = re.sub(r'[^\d.\-]', '', val.replace(',', ''))
        if cleaned:
            try:
                float(cleaned)
                numeric_count += 1
            except ValueError:
                pass

    if numeric_count / len(sample) > 0.7:
        return 'numeric'

    # Check date: try to parse as dates
    date_count = 0
    for val in sample:
        try:
            if len(val) >= 6:  # Minimum reasonable date string
                parser.parse(val)
                date_count += 1
        except (ValueError, TypeError, OverflowError):
            pass

    if date_count / len(sample) > 0.7:
        return 'date'

    return 'text'


def clean_numeric_value(val) -> Optional[float]:
    """Clean a value that should be numeric."""
    if isinstance(val, (int, float)):
        return float(val) if not pd.isna(val) else None
    if not isinstance(val, str) or not val.strip():
        return None
    cleaned = re.sub(r'[^\d.\-]', '', val.replace(',', ''))
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def clean_date_value(val) -> Optional[str]:
    """Clean a value that should be a date."""
    if pd.isna(val) or str(val).strip() == '':
        return None
    try:
        dt = parser.parse(str(val))
        return dt.strftime('%Y-%m-%d')
    except (ValueError, TypeError, OverflowError):
        return None


def clean_text_value(val) -> str:
    """Clean a text value."""
    if pd.isna(val):
        return ''
    return str(val).strip()


def _has_content(val) -> bool:
    """True if the original cell carried a real value (not empty/null)."""
    return not pd.isna(val) and str(val).strip() != ''


def transform(df: pd.DataFrame, strict: Optional[bool] = None) -> TransformResult:
    """
    Dynamically transforms any CSV DataFrame:
    1. Detects column types (numeric, date, text)
    2. Cleans values based on detected types
    3. Quarantines rows that are empty/mostly-empty, and — in strict mode —
       rows where a typed cell had content but failed to parse.

    strict: if None, read from settings.transform.strict. In strict mode a single
    unparseable date/numeric cell sends the whole row to quarantine. In lax mode
    parse failures become NULL and the row passes (legacy behavior).
    """
    from config.settings import settings
    cfg = settings.transform
    if strict is None:
        strict = cfg.strict

    total = len(df)

    # Strip whitespace from column names
    df.columns = df.columns.str.strip()

    # Detect schema
    schema = []
    for col in df.columns:
        col_type = detect_column_type(df[col])
        schema.append(ColumnSchema(
            name=col.lower().replace(' ', '_'),
            dtype=col_type,
            original_name=col,
        ))
        logger.info(f"Column '{col}' detected as: {col_type}")

    # Work on a copy
    processing_df = df.copy()

    # Clean each column based on its detected type, recording hard parse failures:
    # a cell that had content but cleaned to None is corrupt (not just empty).
    parse_failures = {}  # row idx -> list of reason strings
    for col_schema in schema:
        col = col_schema.original_name
        if col_schema.dtype in ('numeric', 'date'):
            clean_fn = clean_numeric_value if col_schema.dtype == 'numeric' else clean_date_value
            cleaned = processing_df[col].apply(clean_fn)
            label = "Numérico inválido" if col_schema.dtype == 'numeric' else "Fecha inválida"
            for idx in processing_df.index:
                if pd.isna(cleaned.at[idx]) and _has_content(processing_df.at[idx, col]):
                    parse_failures.setdefault(idx, []).append(f"{label} en '{col}'")
            processing_df[col] = cleaned
        else:
            processing_df[col] = processing_df[col].apply(clean_text_value)

    # Validation: reject rows where ALL fields are empty/null
    def row_is_empty(row):
        for val in row:
            if val is not None and val != '' and not (isinstance(val, float) and pd.isna(val)):
                return False
        return True

    numeric_cols = [s.original_name for s in schema if s.dtype == 'numeric']

    reject_reasons = []
    for idx, row in processing_df.iterrows():
        reasons = []
        if row_is_empty(row):
            reasons.append("All fields empty")

        # Count how many fields have null/empty values
        null_count = sum(
            1 for val in row
            if val is None or val == '' or (isinstance(val, float) and pd.isna(val))
        )
        total_cols = len(row)
        if null_count > 0 and null_count >= total_cols * 0.7 and not row_is_empty(row):
            reasons.append(f"Mostly empty ({null_count}/{total_cols} fields null)")

        # Hard parse failures (strict mode only).
        if strict and idx in parse_failures:
            reasons.extend(parse_failures[idx])

        # Optional domain rules (off by default).
        if cfg.reject_empty_required and null_count > 0 and not row_is_empty(row):
            reasons.append(f"Campo requerido vacío ({null_count} null)")
        if cfg.reject_nonpositive_numeric:
            for c in numeric_cols:
                v = row[c]
                if v is not None and not (isinstance(v, float) and pd.isna(v)) and v <= 0:
                    reasons.append(f"Numérico no positivo en '{c}'")

        reject_reasons.append('; '.join(reasons))

    processing_df['reject_reason'] = reject_reasons

    # Split valid vs rejected
    valid_mask = processing_df['reject_reason'] == ''

    valid_df = processing_df.loc[valid_mask].drop(columns=['reject_reason']).copy()
    # Quarantine keeps the ORIGINAL values (e.g. "2025/13/45", "two") so the
    # reason is auditable — not the cleaned NaN it became.
    rejected_df = df.loc[~valid_mask].copy()
    rejected_df['reject_reason'] = processing_df.loc[~valid_mask, 'reject_reason']

    # Normalize column names in valid_df to lowercase with underscores
    rename_map = {s.original_name: s.name for s in schema}
    valid_df = valid_df.rename(columns=rename_map)

    logger.info(
        f"Transform complete: {len(valid_df)} valid, {len(rejected_df)} rejected "
        f"out of {total} total rows"
    )

    return TransformResult(
        valid_df=valid_df,
        rejected_df=rejected_df,
        total_processed=total,
        total_valid=len(valid_df),
        total_rejected=len(rejected_df),
        schema=schema,
    )
