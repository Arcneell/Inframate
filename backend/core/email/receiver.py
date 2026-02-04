"""
Email receiver module supporting IMAP and Microsoft 365.

Polls configured mailboxes for new emails and stores them
for processing into tickets or comments.
"""

import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class EmailReceiver:
    """
    Email receiver supporting IMAP and Microsoft 365 providers.

    Usage:
        receiver = EmailReceiver(email_config)
        emails = await receiver.fetch_new_emails()
    """

    def __init__(self, config):
        """
        Initialize receiver with email configuration.

        Args:
            config: EmailConfiguration model instance
        """
        self.config = config
        self.provider = config.provider_type

    def _decode_header_value(self, value: str) -> str:
        """Decode email header value (handles encoded headers)."""
        if not value:
            return ""

        decoded_parts = decode_header(value)
        result = []
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                try:
                    result.append(part.decode(charset or "utf-8", errors="replace"))
                except (LookupError, TypeError):
                    result.append(part.decode("utf-8", errors="replace"))
            else:
                result.append(part)
        return "".join(result)

    def _extract_body(self, msg) -> tuple:
        """
        Extract text and HTML body from email message.

        Returns:
            Tuple of (body_text, body_html)
        """
        body_text = None
        body_html = None

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Skip attachments
                if "attachment" in content_disposition:
                    continue

                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        decoded = payload.decode(charset, errors="replace")

                        if content_type == "text/plain" and not body_text:
                            body_text = decoded
                        elif content_type == "text/html" and not body_html:
                            body_html = decoded
                except Exception as e:
                    logger.warning(f"Failed to decode email part: {e}")
        else:
            content_type = msg.get_content_type()
            try:
                payload = msg.get_payload(decode=True)
                if payload:
                    charset = msg.get_content_charset() or "utf-8"
                    decoded = payload.decode(charset, errors="replace")

                    if content_type == "text/plain":
                        body_text = decoded
                    elif content_type == "text/html":
                        body_html = decoded
            except Exception as e:
                logger.warning(f"Failed to decode email body: {e}")

        return body_text, body_html

    def _extract_headers(self, msg) -> Dict[str, str]:
        """Extract relevant headers from email message."""
        headers = {}
        for key in ["Message-ID", "In-Reply-To", "References", "X-Ticket-ID", "X-Ticket-Number"]:
            value = msg.get(key)
            if value:
                headers[key] = self._decode_header_value(value)
        return headers

    def fetch_imap(self, mark_as_read: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch new emails via IMAP.

        Args:
            mark_as_read: Whether to mark fetched emails as read

        Returns:
            List of email dictionaries with parsed content
        """
        emails = []

        try:
            # Connect to IMAP server
            if self.config.imap_use_ssl:
                imap = imaplib.IMAP4_SSL(self.config.imap_host, self.config.imap_port)
            else:
                imap = imaplib.IMAP4(self.config.imap_host, self.config.imap_port)

            # Login
            imap.login(
                self.config.imap_username or self.config.smtp_username,
                self.config.imap_password or self.config.smtp_password
            )

            # Select folder
            folder = self.config.imap_folder or "INBOX"
            imap.select(folder)

            # Search for unread emails
            status, messages = imap.search(None, "UNSEEN")
            if status != "OK":
                logger.warning(f"IMAP search failed: {status}")
                return emails

            message_ids = messages[0].split()
            logger.info(f"Found {len(message_ids)} unread emails in {folder}")

            for msg_id in message_ids:
                try:
                    # Fetch email
                    status, msg_data = imap.fetch(msg_id, "(RFC822)")
                    if status != "OK":
                        continue

                    # Parse email
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    # Extract sender
                    from_header = msg.get("From", "")
                    from_name, from_email_addr = parseaddr(from_header)
                    from_name = self._decode_header_value(from_name)

                    # Extract recipient
                    to_header = msg.get("To", "")
                    _, to_email_addr = parseaddr(to_header)

                    # Extract subject
                    subject = self._decode_header_value(msg.get("Subject", ""))

                    # Extract body
                    body_text, body_html = self._extract_body(msg)

                    # Extract headers
                    headers = self._extract_headers(msg)

                    email_data = {
                        "message_id": headers.get("Message-ID", f"<imap-{msg_id.decode()}@unknown>"),
                        "in_reply_to": headers.get("In-Reply-To"),
                        "references": headers.get("References"),
                        "from_email": from_email_addr,
                        "from_name": from_name,
                        "to_email": to_email_addr,
                        "subject": subject,
                        "body_text": body_text,
                        "body_html": body_html,
                        "raw_headers": headers,
                        "received_at": datetime.now(timezone.utc)
                    }

                    emails.append(email_data)

                    # Mark as read if requested
                    if mark_as_read:
                        imap.store(msg_id, "+FLAGS", "\\Seen")

                except Exception as e:
                    logger.error(f"Failed to process email {msg_id}: {e}")

            imap.close()
            imap.logout()

        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP error: {e}")
            raise Exception(f"IMAP error: {e}")
        except Exception as e:
            logger.error(f"Failed to fetch IMAP emails: {e}")
            raise

        return emails

    async def fetch_m365(self, mark_as_read: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch new emails via Microsoft 365 Graph API.

        Args:
            mark_as_read: Whether to mark fetched emails as read

        Returns:
            List of email dictionaries with parsed content
        """
        from .microsoft365 import Microsoft365Client

        client = Microsoft365Client(
            tenant_id=self.config.m365_tenant_id,
            client_id=self.config.m365_client_id,
            client_secret=self.config.m365_client_secret,
            mailbox=self.config.m365_mailbox
        )

        # Fetch unread messages
        messages = await client.list_messages(filter_unread=True)
        emails = []

        for msg in messages:
            try:
                # Get full message with body
                full_msg = await client.get_message(msg["id"])

                email_data = {
                    "message_id": full_msg.get("internetMessageId", f"<m365-{msg['id']}@outlook.com>"),
                    "in_reply_to": full_msg.get("inReplyTo"),
                    "references": full_msg.get("conversationId"),  # M365 uses conversation threading
                    "from_email": full_msg.get("from", {}).get("emailAddress", {}).get("address", ""),
                    "from_name": full_msg.get("from", {}).get("emailAddress", {}).get("name", ""),
                    "to_email": self.config.m365_mailbox,
                    "subject": full_msg.get("subject", ""),
                    "body_text": full_msg.get("body", {}).get("content", "") if full_msg.get("body", {}).get("contentType") == "text" else None,
                    "body_html": full_msg.get("body", {}).get("content", "") if full_msg.get("body", {}).get("contentType") == "html" else None,
                    "raw_headers": {
                        "Message-ID": full_msg.get("internetMessageId"),
                        "ConversationId": full_msg.get("conversationId")
                    },
                    "received_at": datetime.now(timezone.utc)
                }

                emails.append(email_data)

                # Mark as read
                if mark_as_read:
                    await client.mark_as_read(msg["id"])

            except Exception as e:
                logger.error(f"Failed to process M365 message {msg.get('id')}: {e}")

        return emails

    async def fetch_new_emails(self, mark_as_read: bool = True) -> List[Dict[str, Any]]:
        """
        Fetch new emails using configured provider.

        Returns:
            List of email dictionaries
        """
        if self.provider == "microsoft_365":
            return await self.fetch_m365(mark_as_read=mark_as_read)
        else:
            # IMAP is synchronous
            return self.fetch_imap(mark_as_read=mark_as_read)


def get_active_inbound_configs(db: Session) -> List:
    """
    Get all active email configurations with inbound enabled.

    Returns:
        List of EmailConfiguration instances
    """
    from backend.models import EmailConfiguration

    return db.query(EmailConfiguration).filter(
        EmailConfiguration.is_active == True,
        EmailConfiguration.is_inbound_enabled == True
    ).all()
