import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
import json
from config.settings import settings

logger = logging.getLogger(__name__)

class Notifier:
    def __init__(self):
        self.config = settings.notifier

    def send_report(self, summary: dict):
        if not self.config.enable_notifications:
            logger.info("Notifications disabled.")
            return

        message_body = self._format_message(summary)
        
        # Email
        if self.config.smtp_user and self.config.smtp_password:
            self._send_email("ETL Report", message_body)
        
        # Slack
        if self.config.slack_webhook_url:
            self._send_slack(summary)

    def _format_message(self, summary: dict) -> str:
        return f"""
        ETL Execution Report
        --------------------
        Status: {summary.get('status')}
        Time: {summary.get('duration', 'N/A')}s
        
        Files Processed: {summary.get('file_name')}
        Rows Read: {summary.get('total_read')}
        
        Valid: {summary.get('total_valid')}
        Rejected: {summary.get('total_rejected')}
        
        DB Inserts: {summary.get('db_inserts')}
        DB Updates: {summary.get('db_updates')}
        """

    def _send_email(self, subject: str, body: str):
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config.smtp_user
            msg['To'] = self.config.smtp_recipient if self.config.smtp_recipient else self.config.smtp_user
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            server.starttls()
            server.login(self.config.smtp_user, self.config.smtp_password)
            text = msg.as_string()
            recipient = self.config.smtp_recipient if self.config.smtp_recipient else self.config.smtp_user
            server.sendmail(self.config.smtp_user, recipient, text)
            server.quit()
            logger.info("Email sent successfully.")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    def _send_slack(self, summary: dict):
        # Using Slack Block Kit
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 ETL Job Report",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Status:*\n{summary.get('status')}"},
                    {"type": "mrkdwn", "text": f"*Duration:*\n{summary.get('duration')}s"}
                ]
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Read:*\n{summary.get('total_read')}"},
                    {"type": "mrkdwn", "text": f"*Valid:*\n{summary.get('total_valid')}"},
                    {"type": "mrkdwn", "text": f"*Rejected:*\n{summary.get('total_rejected')}"}
                ]
            },
            {
                "type": "divider"
            }
        ]
        
        payload = {"blocks": blocks}
        try:
            response = requests.post(
                self.config.slack_webhook_url, 
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )
            if response.status_code != 200:
                 logger.error(f"Slack API error: {response.status_code} {response.text}")
            else:
                logger.info("Slack notification sent.")
        except Exception as e:
            logger.error(f"Failed to send Slack: {e}")
