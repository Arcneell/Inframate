"""
Email parsing and thread detection module.

Detects whether an incoming email is a reply to an existing ticket
or a new ticket request.
"""

import re
import logging
from typing import Optional, Dict, Any, Tuple
from html import unescape

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Regex pattern for ticket number in subject line
# Matches: TKT-YYYYMMDD-XXXX (e.g., TKT-20260204-0001)
TICKET_NUMBER_PATTERN = re.compile(r"TKT-\d{8}-\d{4}")

# Pattern to extract ticket ID from custom header
TICKET_ID_PATTERN = re.compile(r"^\d+$")

# Common reply prefixes to strip from subject
REPLY_PREFIXES = re.compile(r"^(Re:|RE:|Fwd:|FWD:|Fw:|FW:|\[.*?\])\s*", re.IGNORECASE)

# Quote patterns to strip from reply body
QUOTE_PATTERNS = [
    # "On [date], [name] wrote:"
    re.compile(r"^On .+ wrote:.*$", re.MULTILINE | re.IGNORECASE),
    # "From: [email]" header block
    re.compile(r"^From:.*$", re.MULTILINE),
    # Gmail quote marker
    re.compile(r"^>.*$", re.MULTILINE),
    # Outlook separator
    re.compile(r"^_{10,}.*$", re.MULTILINE),
    # Common separator lines
    re.compile(r"^-{3,}.*Original Message.*-{3,}$", re.MULTILINE | re.IGNORECASE),
]


class EmailParser:
    """
    Parser for incoming emails with thread detection.

    Usage:
        parser = EmailParser(db)
        result = parser.parse_and_detect(email_data)
        # result = {"ticket_id": 123, "is_reply": True, "clean_content": "..."}
    """

    def __init__(self, db: Session):
        self.db = db

    def clean_subject(self, subject: str) -> str:
        """
        Remove reply prefixes from subject line.

        Args:
            subject: Raw email subject

        Returns:
            Cleaned subject without Re:/Fwd:/etc prefixes
        """
        if not subject:
            return ""

        cleaned = subject
        while True:
            new_cleaned = REPLY_PREFIXES.sub("", cleaned).strip()
            if new_cleaned == cleaned:
                break
            cleaned = new_cleaned

        return cleaned

    def extract_ticket_number_from_subject(self, subject: str) -> Optional[str]:
        """
        Extract ticket number from email subject.

        Args:
            subject: Email subject line

        Returns:
            Ticket number (e.g., "TKT-20260204-0001") or None
        """
        if not subject:
            return None

        match = TICKET_NUMBER_PATTERN.search(subject)
        if match:
            return match.group(0)

        return None

    def strip_quotes(self, body: str) -> str:
        """
        Strip quoted content from reply body.

        Removes the original message that's typically included in email replies.

        Args:
            body: Raw email body text

        Returns:
            Body with quotes removed
        """
        if not body:
            return ""

        result = body

        # Remove common quote patterns
        for pattern in QUOTE_PATTERNS:
            result = pattern.sub("", result)

        # Remove consecutive blank lines
        result = re.sub(r"\n{3,}", "\n\n", result)

        return result.strip()

    def html_to_text(self, html: str) -> str:
        """
        Convert HTML body to plain text.

        Args:
            html: HTML content

        Returns:
            Plain text content
        """
        if not html:
            return ""

        # Remove script and style tags
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)

        # Replace br and p tags with newlines
        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)

        # Remove all remaining HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Decode HTML entities
        text = unescape(text)

        # Clean up whitespace
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    def find_ticket_by_message_id(self, message_id: str) -> Optional[int]:
        """
        Find ticket by matching a sent email's Message-ID.

        Args:
            message_id: Message-ID header value

        Returns:
            Ticket ID or None
        """
        from backend.models import SentEmail

        sent_email = self.db.query(SentEmail).filter(
            SentEmail.message_id == message_id
        ).first()

        if sent_email and sent_email.ticket_id:
            return sent_email.ticket_id

        return None

    def find_ticket_by_number(self, ticket_number: str) -> Optional[int]:
        """
        Find ticket by ticket number.

        Args:
            ticket_number: Ticket number (e.g., "TKT-20260204-0001")

        Returns:
            Ticket ID or None
        """
        from backend.models import Ticket

        ticket = self.db.query(Ticket).filter(
            Ticket.ticket_number == ticket_number,
            Ticket.is_deleted == False
        ).first()

        if ticket:
            return ticket.id

        return None

    def find_ticket_by_email_message_id(self, message_id: str) -> Optional[int]:
        """
        Find ticket that was created from a specific email.

        Args:
            message_id: Original email Message-ID

        Returns:
            Ticket ID or None
        """
        from backend.models import Ticket

        ticket = self.db.query(Ticket).filter(
            Ticket.email_message_id == message_id
        ).first()

        if ticket:
            return ticket.id

        return None

    def find_user_by_email(self, email_address: str) -> Optional[int]:
        """
        Find user by email address.

        Args:
            email_address: User email address

        Returns:
            User ID or None
        """
        from backend.models import User

        user = self.db.query(User).filter(
            User.email == email_address,
            User.is_active == True
        ).first()

        if user:
            return user.id

        return None


def detect_ticket_from_email(
    db: Session,
    email_data: Dict[str, Any]
) -> Tuple[Optional[int], bool, str]:
    """
    Detect which ticket (if any) an email belongs to.

    Detection order:
    1. X-Ticket-ID header (if present)
    2. In-Reply-To header -> match SentEmail.message_id
    3. References header -> match any SentEmail.message_id
    4. Subject line -> extract TKT-YYYYMMDD-XXXX pattern
    5. In-Reply-To -> match Ticket.email_message_id (original email that created ticket)

    Args:
        db: Database session
        email_data: Parsed email dictionary

    Returns:
        Tuple of (ticket_id, is_reply, clean_content)
        - ticket_id: Found ticket ID or None
        - is_reply: True if this is a reply to existing ticket
        - clean_content: Cleaned email body for ticket/comment content
    """
    parser = EmailParser(db)

    ticket_id = None
    is_reply = False

    # Get email data
    subject = email_data.get("subject", "")
    in_reply_to = email_data.get("in_reply_to")
    references = email_data.get("references")
    raw_headers = email_data.get("raw_headers", {})
    body_text = email_data.get("body_text", "")
    body_html = email_data.get("body_html", "")

    # 1. Check X-Ticket-ID header
    x_ticket_id = raw_headers.get("X-Ticket-ID")
    if x_ticket_id and TICKET_ID_PATTERN.match(x_ticket_id):
        try:
            candidate_id = int(x_ticket_id)
            # Verify ticket exists
            from backend.models import Ticket
            exists = db.query(Ticket).filter(
                Ticket.id == candidate_id,
                Ticket.is_deleted == False
            ).first()
            if exists:
                ticket_id = candidate_id
                is_reply = True
                logger.info(f"Found ticket via X-Ticket-ID header: {ticket_id}")
        except ValueError:
            pass

    # 2. Check In-Reply-To header
    if not ticket_id and in_reply_to:
        found_id = parser.find_ticket_by_message_id(in_reply_to)
        if found_id:
            ticket_id = found_id
            is_reply = True
            logger.info(f"Found ticket via In-Reply-To header: {ticket_id}")

    # 3. Check References header
    if not ticket_id and references:
        # References can contain multiple Message-IDs separated by spaces
        ref_ids = references.split()
        for ref_id in ref_ids:
            found_id = parser.find_ticket_by_message_id(ref_id.strip())
            if found_id:
                ticket_id = found_id
                is_reply = True
                logger.info(f"Found ticket via References header: {ticket_id}")
                break

    # 4. Check subject line for ticket number
    if not ticket_id:
        ticket_number = parser.extract_ticket_number_from_subject(subject)
        if ticket_number:
            found_id = parser.find_ticket_by_number(ticket_number)
            if found_id:
                ticket_id = found_id
                is_reply = True
                logger.info(f"Found ticket via subject ticket number: {ticket_id}")

    # 5. Check if In-Reply-To matches original email that created a ticket
    if not ticket_id and in_reply_to:
        found_id = parser.find_ticket_by_email_message_id(in_reply_to)
        if found_id:
            ticket_id = found_id
            is_reply = True
            logger.info(f"Found ticket via original email Message-ID: {ticket_id}")

    # Prepare clean content
    if body_text:
        clean_content = body_text
    elif body_html:
        clean_content = parser.html_to_text(body_html)
    else:
        clean_content = ""

    # Strip quotes if this is a reply
    if is_reply:
        clean_content = parser.strip_quotes(clean_content)

    return ticket_id, is_reply, clean_content
