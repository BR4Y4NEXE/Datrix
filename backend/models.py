from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from enum import Enum


class RunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class PipelineRunCreate(BaseModel):
    dry_run: bool = False
    auto_detect: bool = False


class PipelineRunResponse(BaseModel):
    id: str
    status: str
    file_name: str
    dry_run: bool
    started_at: str
    finished_at: Optional[str] = None
    duration: Optional[float] = None
    total_read: Optional[int] = None
    total_valid: Optional[int] = None
    total_rejected: Optional[int] = None
    db_inserts: Optional[int] = None
    db_updates: Optional[int] = None
    error_message: Optional[str] = None


# Dynamic record response - works with any column structure
class PaginatedRecords(BaseModel):
    records: List[Dict[str, Any]]
    total: int
    page: int
    per_page: int
    total_pages: int


class ColumnSchemaResponse(BaseModel):
    column_name: str
    column_type: str
    original_name: str
    column_order: int


class DatasetSchemaResponse(BaseModel):
    run_id: str
    columns: List[ColumnSchemaResponse]


class QuarantineFile(BaseModel):
    filename: str
    row_count: int
    created_at: str


class QuarantineDetail(BaseModel):
    filename: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    total: int


class NotificationStatus(BaseModel):
    email_enabled: bool
    slack_enabled: bool
    smtp_configured: bool
    slack_configured: bool
