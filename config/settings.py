import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

@dataclass
class DatabaseConfig:
    db_path: str = os.getenv("DB_PATH", "sales_data.sqlite")

@dataclass
class NotifierConfig:
    enable_notifications: bool = os.getenv("ENABLE_NOTIFICATIONS", "false").lower() == "true"
    smtp_server: str = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    slack_webhook_url: str = os.getenv("SLACK_WEBHOOK_URL", "")
    smtp_recipient: str = os.getenv("SMTP_RECIPIENT", "")

@dataclass
class AppConfig:
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    input_dir: str = os.path.join(os.getcwd(), "data", "input")
    quarantine_dir: str = os.path.join(os.getcwd(), "data", "quarantine")
    log_file: str = os.path.join(os.getcwd(), "logs", "etl.log")

@dataclass
class Settings:
    db: DatabaseConfig = field(default_factory=DatabaseConfig)
    notifier: NotifierConfig = field(default_factory=NotifierConfig)
    app: AppConfig = field(default_factory=AppConfig)

settings = Settings()
