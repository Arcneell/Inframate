"""
Email integration module for Inframate.

This module provides:
- Email sending via SMTP or Microsoft 365 Graph API
- Email receiving via IMAP or Microsoft 365 Graph API
- Email parsing and thread detection
- Jinja2 template rendering for professional email notifications
"""

from .sender import EmailSender, send_email
from .receiver import EmailReceiver
from .parser import EmailParser, detect_ticket_from_email
from .templates import render_email_template

__all__ = [
    "EmailSender",
    "send_email",
    "EmailReceiver",
    "EmailParser",
    "detect_ticket_from_email",
    "render_email_template",
]
