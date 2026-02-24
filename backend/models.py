from pydantic import BaseModel
from typing import Optional, List
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


class SalesRecordResponse(BaseModel):
    id: str
    date: str
    product: str
    qty: int
    price: float
    store_id: str
    last_updated: str


class PaginatedRecords(BaseModel):
    records: List[SalesRecordResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class QuarantineFile(BaseModel):
    filename: str
    row_count: int
    created_at: str


class QuarantineRow(BaseModel):
    ID: str
    Date: str
    Product: str
    Qty: str
    Price: str
    Store_ID: str
    reject_reason: str


class QuarantineDetail(BaseModel):
    filename: str
    rows: List[QuarantineRow]
    total: int


class NotificationStatus(BaseModel):
    email_enabled: bool
    slack_enabled: bool
    smtp_configured: bool
    slack_configured: bool
