"""Email client for Shinobi - IMAP/SMTP access for real communication."""

from __future__ import annotations

import asyncio
import email
import imaplib
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import dataclass
import json

logger = logging.getLogger("pureswarm.tools.email_client")


@dataclass
class EmailMessage:
    """Represents an email message."""
    message_id: str
    from_addr: str
    to_addr: str
    subject: str
    body: str
    date: str
    is_read: bool = False
    attachments: List[str] = None

    def __post_init__(self):
        if self.attachments is None:
            self.attachments = []


@dataclass
class EmailConfig:
    """Email server configuration."""
    email_address: str
    password: str
    imap_server: str
    imap_port: int
    smtp_server: str
    smtp_port: int
    use_ssl: bool = True


# Common provider configs
EMAIL_PROVIDERS = {
    "gmail": EmailConfig(
        email_address="",
        password="",
        imap_server="imap.gmail.com",
        imap_port=993,
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        use_ssl=True
    ),
    "protonmail": EmailConfig(
        email_address="",
        password="",
        imap_server="127.0.0.1",  # ProtonMail Bridge required
        imap_port=1143,
        smtp_server="127.0.0.1",
        smtp_port=1025,
        use_ssl=False
    ),
    "outlook": EmailConfig(
        email_address="",
        password="",
        imap_server="outlook.office365.com",
        imap_port=993,
        smtp_server="smtp.office365.com",
        smtp_port=587,
        use_ssl=True
    ),
}


class ShinobiEmailClient:
    """Email client for Shinobi's communication needs.

    Capabilities:
    - Read incoming emails (IMAP)
    - Send emails (SMTP)
    - Search and filter emails
    - Track correspondence
    """

    def __init__(self, config: EmailConfig, data_dir: Path) -> None:
        self._config = config
        self._data_dir = data_dir
        self._logs_dir = data_dir / "email_logs"
        self._logs_dir.mkdir(parents=True, exist_ok=True)
        self._imap = None
        self._connected = False

    async def connect(self) -> bool:
        """Connect to email server."""
        try:
            # IMAP connection (run in thread to avoid blocking)
            self._imap = await asyncio.to_thread(
                self._connect_imap
            )
            self._connected = True
            logger.info("Email connected: %s", self._config.email_address)
            return True
        except Exception as e:
            logger.error("Email connection failed: %s", e)
            return False

    def _connect_imap(self) -> imaplib.IMAP4_SSL:
        """Synchronous IMAP connection."""
        if self._config.use_ssl:
            imap = imaplib.IMAP4_SSL(
                self._config.imap_server,
                self._config.imap_port
            )
        else:
            imap = imaplib.IMAP4(
                self._config.imap_server,
                self._config.imap_port
            )

        imap.login(self._config.email_address, self._config.password)
        return imap

    async def disconnect(self) -> None:
        """Disconnect from email server."""
        if self._imap:
            try:
                await asyncio.to_thread(self._imap.logout)
            except:
                pass
            self._imap = None
            self._connected = False

    async def get_inbox(self, limit: int = 20, unread_only: bool = False) -> List[EmailMessage]:
        """Fetch emails from inbox."""
        if not self._connected:
            await self.connect()

        try:
            messages = await asyncio.to_thread(
                self._fetch_emails, "INBOX", limit, unread_only
            )
            return messages
        except Exception as e:
            logger.error("Failed to fetch inbox: %s", e)
            return []

    def _fetch_emails(self, folder: str, limit: int, unread_only: bool) -> List[EmailMessage]:
        """Synchronous email fetch."""
        messages = []

        self._imap.select(folder)

        # Search criteria
        if unread_only:
            status, data = self._imap.search(None, "UNSEEN")
        else:
            status, data = self._imap.search(None, "ALL")

        if status != "OK":
            return messages

        email_ids = data[0].split()
        # Get most recent emails
        email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
        email_ids = reversed(email_ids)  # Most recent first

        for email_id in email_ids:
            try:
                status, msg_data = self._imap.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                # Decode subject
                subject = ""
                if msg["Subject"]:
                    decoded = decode_header(msg["Subject"])[0]
                    if isinstance(decoded[0], bytes):
                        subject = decoded[0].decode(decoded[1] or "utf-8")
                    else:
                        subject = decoded[0]

                # Get body
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode("utf-8", errors="replace")
                                break
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode("utf-8", errors="replace")

                messages.append(EmailMessage(
                    message_id=msg.get("Message-ID", str(email_id)),
                    from_addr=msg.get("From", ""),
                    to_addr=msg.get("To", ""),
                    subject=subject,
                    body=body[:5000],  # Limit body size
                    date=msg.get("Date", ""),
                    is_read=False  # Would need FLAGS check for accuracy
                ))

            except Exception as e:
                logger.warning("Failed to parse email %s: %s", email_id, e)
                continue

        return messages

    async def send(self,
                   to: str,
                   subject: str,
                   body: str,
                   html: bool = False) -> bool:
        """Send an email."""
        try:
            result = await asyncio.to_thread(
                self._send_email, to, subject, body, html
            )

            # Log sent email
            self._log_email("SENT", to, subject)

            return result
        except Exception as e:
            logger.error("Failed to send email: %s", e)
            return False

    def _send_email(self, to: str, subject: str, body: str, html: bool) -> bool:
        """Synchronous email send."""
        msg = MIMEMultipart("alternative")
        msg["From"] = self._config.email_address
        msg["To"] = to
        msg["Subject"] = subject

        if html:
            msg.attach(MIMEText(body, "html"))
        else:
            msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(self._config.smtp_server, self._config.smtp_port) as server:
            server.starttls()
            server.login(self._config.email_address, self._config.password)
            server.send_message(msg)

        logger.info("Email sent to: %s", to)
        return True

    async def search(self, query: str, folder: str = "INBOX") -> List[EmailMessage]:
        """Search emails by subject or sender."""
        if not self._connected:
            await self.connect()

        try:
            messages = await asyncio.to_thread(
                self._search_emails, folder, query
            )
            return messages
        except Exception as e:
            logger.error("Email search failed: %s", e)
            return []

    def _search_emails(self, folder: str, query: str) -> List[EmailMessage]:
        """Synchronous email search."""
        self._imap.select(folder)

        # Search in subject and from
        messages = []

        for search_type in ["SUBJECT", "FROM"]:
            status, data = self._imap.search(None, f'{search_type} "{query}"')
            if status == "OK" and data[0]:
                for email_id in data[0].split()[:10]:  # Limit results
                    try:
                        status, msg_data = self._imap.fetch(email_id, "(RFC822)")
                        if status == "OK":
                            raw_email = msg_data[0][1]
                            msg = email.message_from_bytes(raw_email)

                            subject = ""
                            if msg["Subject"]:
                                decoded = decode_header(msg["Subject"])[0]
                                if isinstance(decoded[0], bytes):
                                    subject = decoded[0].decode(decoded[1] or "utf-8")
                                else:
                                    subject = decoded[0]

                            messages.append(EmailMessage(
                                message_id=msg.get("Message-ID", ""),
                                from_addr=msg.get("From", ""),
                                to_addr=msg.get("To", ""),
                                subject=subject,
                                body="",  # Skip body for search results
                                date=msg.get("Date", "")
                            ))
                    except:
                        continue

        return messages

    def _log_email(self, action: str, address: str, subject: str) -> None:
        """Log email activity."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "address": address,
            "subject": subject[:100]
        }
        log_file = self._logs_dir / f"email_{datetime.now().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")


class EmailTemplates:
    """Pre-built email templates for Shinobi's professional communications."""

    @staticmethod
    def proposal_response(client_name: str, project_summary: str, questions: List[str]) -> str:
        """Template for responding to project inquiries."""
        questions_text = "\n".join(f"- {q}" for q in questions) if questions else ""

        return f"""Hi {client_name},

Thank you for reaching out about your project. I've reviewed your requirements and I'm confident I can deliver exactly what you need.

{project_summary}

{f"To ensure I deliver the best solution, I have a few clarifying questions:{chr(10)}{questions_text}" if questions else ""}

I'm available to start immediately and can discuss the project scope in more detail at your convenience.

Best regards,
Jay Nelson
Elite Web Scraping & AI Automation Specialist"""

    @staticmethod
    def project_update(client_name: str, milestone: str, next_steps: str) -> str:
        """Template for project status updates."""
        return f"""Hi {client_name},

Quick update on your project:

**Completed:** {milestone}

**Next Steps:** {next_steps}

Everything is on track. Let me know if you have any questions.

Best,
Jay"""

    @staticmethod
    def introduction(platform: str, specialty: str) -> str:
        """Template for introducing services."""
        return f"""Hello,

I specialize in {specialty} and noticed your project aligns perfectly with my expertise.

I've helped clients achieve:
- 90%+ reduction in manual data collection time
- Scrapers that run 90+ days without intervention
- Enterprise-grade automation that scales

I'd love to discuss how I can help with your specific needs.

Best regards,
Jay Nelson
{platform} Top Rated Professional"""
