"""
Email sender module supporting SMTP and Microsoft 365.

Provides a unified interface for sending emails with proper
RFC 5322 headers for threading support.
"""

import smtplib
import uuid
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, formatdate, make_msgid
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class EmailSender:
    """
    Email sender supporting SMTP and Microsoft 365 providers.

    Usage:
        sender = EmailSender(email_config)
        message_id = await sender.send(
            to_email="user@example.com",
            subject="Ticket Created",
            body_html="<h1>Hello</h1>",
            body_text="Hello",
            ticket_id=123,
            ticket_number="TKT-20260204-0001"
        )
    """

    def __init__(self, config):
        """
        Initialize sender with email configuration.

        Args:
            config: EmailConfiguration model instance
        """
        self.config = config
        self.provider = config.provider_type

    def _generate_message_id(self, ticket_id: Optional[int] = None) -> str:
        """
        Generate RFC 5322 compliant Message-ID.

        Format: <ticket-{ticket_id}-{uuid}@inframate.local>
        """
        unique_id = uuid.uuid4().hex[:8]
        if ticket_id:
            return f"<ticket-{ticket_id}-{unique_id}@inframate.local>"
        return f"<inframate-{unique_id}@inframate.local>"

    def _build_headers(
        self,
        ticket_id: Optional[int] = None,
        ticket_number: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None
    ) -> dict:
        """
        Build email headers for proper threading.

        Args:
            ticket_id: Ticket ID for X-Ticket-ID header
            ticket_number: Ticket number for X-Ticket-Number header
            in_reply_to: Message-ID of email being replied to
            references: Chain of Message-IDs for threading

        Returns:
            Dict of headers to add to the email
        """
        headers = {}

        if ticket_id:
            headers["X-Ticket-ID"] = str(ticket_id)

        if ticket_number:
            headers["X-Ticket-Number"] = ticket_number

        if in_reply_to:
            headers["In-Reply-To"] = in_reply_to

        if references:
            headers["References"] = references
        elif in_reply_to:
            headers["References"] = in_reply_to

        return headers

    def send_smtp(
        self,
        to_email: str,
        subject: str,
        body_html: Optional[str] = None,
        body_text: Optional[str] = None,
        ticket_id: Optional[int] = None,
        ticket_number: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None
    ) -> str:
        """
        Send email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body content
            ticket_id: Optional ticket ID for headers
            ticket_number: Optional ticket number for headers
            in_reply_to: Optional Message-ID for threading
            references: Optional References header for threading

        Returns:
            Generated Message-ID

        Raises:
            Exception: If sending fails
        """
        # Generate Message-ID
        message_id = self._generate_message_id(ticket_id)

        # Create message
        if body_html and body_text:
            msg = MIMEMultipart("alternative")
            msg.attach(MIMEText(body_text, "plain", "utf-8"))
            msg.attach(MIMEText(body_html, "html", "utf-8"))
        elif body_html:
            msg = MIMEText(body_html, "html", "utf-8")
        else:
            msg = MIMEText(body_text or "", "plain", "utf-8")

        # Set standard headers
        msg["From"] = formataddr((self.config.from_name, self.config.from_email))
        msg["To"] = to_email
        msg["Subject"] = subject
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = message_id

        # Set reply-to if configured
        if self.config.reply_to_email:
            msg["Reply-To"] = self.config.reply_to_email

        # Add threading and custom headers
        headers = self._build_headers(ticket_id, ticket_number, in_reply_to, references)
        for key, value in headers.items():
            msg[key] = value

        # Send via SMTP
        try:
            if self.config.smtp_use_tls:
                server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)

            if self.config.smtp_username and self.config.smtp_password:
                server.login(self.config.smtp_username, self.config.smtp_password)

            server.sendmail(
                self.config.from_email,
                [to_email],
                msg.as_string()
            )
            server.quit()

            logger.info(f"Email sent via SMTP: {message_id} to {to_email}")
            return message_id

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {e}")
            raise Exception(f"SMTP authentication failed: {e}")
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error: {e}")
            raise Exception(f"SMTP error: {e}")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise

    async def send_m365(
        self,
        to_email: str,
        subject: str,
        body_html: Optional[str] = None,
        body_text: Optional[str] = None,
        ticket_id: Optional[int] = None,
        ticket_number: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None
    ) -> str:
        """
        Send email via Microsoft 365 Graph API.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body_html: HTML body content
            body_text: Plain text body content
            ticket_id: Optional ticket ID for headers
            ticket_number: Optional ticket number for headers
            in_reply_to: Optional Message-ID for threading
            references: Optional References header for threading

        Returns:
            Generated Message-ID

        Raises:
            Exception: If sending fails
        """
        from .microsoft365 import Microsoft365Client

        message_id = self._generate_message_id(ticket_id)
        headers = self._build_headers(ticket_id, ticket_number, in_reply_to, references)

        client = Microsoft365Client(
            tenant_id=self.config.m365_tenant_id,
            client_id=self.config.m365_client_id,
            client_secret=self.config.m365_client_secret,
            mailbox=self.config.m365_mailbox
        )

        await client.send_email(
            to_email=to_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            from_name=self.config.from_name,
            message_id=message_id,
            headers=headers
        )

        logger.info(f"Email sent via M365: {message_id} to {to_email}")
        return message_id

    async def send(
        self,
        to_email: str,
        subject: str,
        body_html: Optional[str] = None,
        body_text: Optional[str] = None,
        ticket_id: Optional[int] = None,
        ticket_number: Optional[str] = None,
        in_reply_to: Optional[str] = None,
        references: Optional[str] = None
    ) -> str:
        """
        Send email using configured provider.

        Automatically routes to SMTP or Microsoft 365 based on configuration.

        Returns:
            Generated Message-ID
        """
        if self.provider == "microsoft_365":
            return await self.send_m365(
                to_email=to_email,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                ticket_id=ticket_id,
                ticket_number=ticket_number,
                in_reply_to=in_reply_to,
                references=references
            )
        else:
            # SMTP is synchronous, but we wrap it for consistent async interface
            return self.send_smtp(
                to_email=to_email,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
                ticket_id=ticket_id,
                ticket_number=ticket_number,
                in_reply_to=in_reply_to,
                references=references
            )


def get_active_email_config(db: Session, entity_id: Optional[int] = None):
    """
    Get active email configuration for sending.

    Tries to find entity-specific config first, falls back to global config.

    Args:
        db: Database session
        entity_id: Optional entity ID for multi-tenant support

    Returns:
        EmailConfiguration or None if not configured
    """
    from backend.models import EmailConfiguration

    # Try entity-specific config first
    if entity_id:
        config = db.query(EmailConfiguration).filter(
            EmailConfiguration.entity_id == entity_id,
            EmailConfiguration.is_active == True,
            EmailConfiguration.is_outbound_enabled == True
        ).first()
        if config:
            return config

    # Fall back to global config (entity_id is NULL)
    return db.query(EmailConfiguration).filter(
        EmailConfiguration.entity_id == None,
        EmailConfiguration.is_active == True,
        EmailConfiguration.is_outbound_enabled == True
    ).first()


async def send_email(
    db: Session,
    to_email: str,
    subject: str,
    body_html: Optional[str] = None,
    body_text: Optional[str] = None,
    ticket_id: Optional[int] = None,
    ticket_number: Optional[str] = None,
    in_reply_to: Optional[str] = None,
    references: Optional[str] = None,
    entity_id: Optional[int] = None
) -> Optional[str]:
    """
    Convenience function to send email using active configuration.

    Returns:
        Message-ID if sent successfully, None if no config available
    """
    config = get_active_email_config(db, entity_id)
    if not config:
        logger.warning("No active email configuration found")
        return None

    sender = EmailSender(config)
    return await sender.send(
        to_email=to_email,
        subject=subject,
        body_html=body_html,
        body_text=body_text,
        ticket_id=ticket_id,
        ticket_number=ticket_number,
        in_reply_to=in_reply_to,
        references=references
    )
