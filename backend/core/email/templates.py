"""
Email template rendering module using Jinja2.

Provides functions to render HTML and plain text email templates
for various ticket notification types.
"""

import os
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates" / "email"

# Initialize Jinja2 environment
_env: Optional[Environment] = None


def get_template_env() -> Environment:
    """
    Get or create Jinja2 environment for email templates.

    Returns:
        Configured Jinja2 Environment
    """
    global _env

    if _env is None:
        # Ensure template directory exists
        TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

        _env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
            trim_blocks=True,
            lstrip_blocks=True
        )

        # Add custom filters
        _env.filters["format_datetime"] = format_datetime
        _env.filters["truncate_text"] = truncate_text

    return _env


def format_datetime(value, format: str = "%Y-%m-%d %H:%M") -> str:
    """Format datetime for email display."""
    if value is None:
        return ""
    try:
        return value.strftime(format)
    except Exception:
        return str(value)


def truncate_text(text: str, length: int = 200) -> str:
    """Truncate text to specified length."""
    if not text:
        return ""
    if len(text) <= length:
        return text
    return text[:length].rsplit(" ", 1)[0] + "..."


def render_email_template(
    template_name: str,
    context: Dict[str, Any],
    site_name: str = "Inframate",
    site_url: str = "http://localhost:3000"
) -> Tuple[str, str]:
    """
    Render email template with context.

    Args:
        template_name: Name of template (e.g., "ticket_created")
        context: Template context variables
        site_name: Application name for branding
        site_url: Base URL for links

    Returns:
        Tuple of (html_content, text_content)
    """
    env = get_template_env()

    # Add global context
    full_context = {
        "site_name": site_name,
        "site_url": site_url,
        **context
    }

    # Render HTML template
    html_content = ""
    try:
        html_template = env.get_template(f"{template_name}.html")
        html_content = html_template.render(**full_context)
    except Exception as e:
        logger.warning(f"Failed to render HTML template {template_name}: {e}")
        # Fall back to inline template if file doesn't exist
        html_content = render_fallback_html(template_name, full_context)

    # Generate plain text version
    text_content = generate_plain_text(template_name, full_context)

    return html_content, text_content


def render_fallback_html(template_name: str, context: Dict[str, Any]) -> str:
    """
    Render fallback HTML when template file doesn't exist.

    Args:
        template_name: Template name
        context: Template context

    Returns:
        Simple HTML email content
    """
    ticket = context.get("ticket", {})
    ticket_number = getattr(ticket, "ticket_number", "N/A") if hasattr(ticket, "ticket_number") else ticket.get("ticket_number", "N/A")
    title = getattr(ticket, "title", "") if hasattr(ticket, "title") else ticket.get("title", "")
    site_name = context.get("site_name", "Inframate")
    site_url = context.get("site_url", "")

    # Build generic message based on template name
    messages = {
        "ticket_created": f"A new ticket has been created: {ticket_number}",
        "ticket_assigned": f"Ticket {ticket_number} has been assigned to you",
        "comment_added": f"A new comment has been added to ticket {ticket_number}",
        "ticket_resolved": f"Ticket {ticket_number} has been resolved",
        "sla_warning": f"SLA warning: Ticket {ticket_number} is approaching its deadline",
        "sla_breach": f"SLA breach: Ticket {ticket_number} has exceeded its deadline"
    }

    message = messages.get(template_name, f"Notification for ticket {ticket_number}")

    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #0ea5e9; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #ffffff; padding: 20px; border: 1px solid #e5e7eb; }}
        .footer {{ background: #f8fafc; padding: 15px; font-size: 12px; color: #64748b; text-align: center; border-radius: 0 0 8px 8px; }}
        .ticket-info {{ background: #f1f5f9; padding: 15px; border-left: 4px solid #0ea5e9; margin: 15px 0; }}
        .button {{ display: inline-block; background: #0ea5e9; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 style="margin: 0; font-size: 24px;">{site_name}</h1>
        </div>
        <div class="content">
            <p>{message}</p>
            <div class="ticket-info">
                <strong>Ticket:</strong> {ticket_number}<br>
                <strong>Title:</strong> {title}
            </div>
            <a href="{site_url}/tickets?id={getattr(ticket, 'id', '') if hasattr(ticket, 'id') else ticket.get('id', '')}" class="button">View Ticket</a>
        </div>
        <div class="footer">
            <p>This email was sent by {site_name}.</p>
            <p>To reply to this ticket, simply reply to this email.</p>
        </div>
    </div>
</body>
</html>
"""


def generate_plain_text(template_name: str, context: Dict[str, Any]) -> str:
    """
    Generate plain text version of email.

    Args:
        template_name: Template name
        context: Template context

    Returns:
        Plain text email content
    """
    ticket = context.get("ticket", {})
    ticket_number = getattr(ticket, "ticket_number", "N/A") if hasattr(ticket, "ticket_number") else ticket.get("ticket_number", "N/A")
    title = getattr(ticket, "title", "") if hasattr(ticket, "title") else ticket.get("title", "")
    site_name = context.get("site_name", "Inframate")
    site_url = context.get("site_url", "")
    comment = context.get("comment")

    messages = {
        "ticket_created": f"A new ticket has been created.",
        "ticket_assigned": f"A ticket has been assigned to you.",
        "comment_added": f"A new comment has been added to your ticket.",
        "ticket_resolved": f"Your ticket has been resolved.",
        "sla_warning": f"SLA warning: This ticket is approaching its deadline.",
        "sla_breach": f"SLA breach: This ticket has exceeded its deadline."
    }

    message = messages.get(template_name, "Ticket notification")

    text = f"""
{site_name}
{'=' * len(site_name)}

{message}

Ticket: {ticket_number}
Title: {title}
"""

    if comment:
        comment_content = getattr(comment, "content", "") if hasattr(comment, "content") else comment.get("content", "")
        text += f"""
Comment:
{'-' * 40}
{comment_content}
{'-' * 40}
"""

    ticket_id = getattr(ticket, 'id', '') if hasattr(ticket, 'id') else ticket.get('id', '')
    text += f"""
View ticket: {site_url}/tickets?id={ticket_id}

--
This email was sent by {site_name}.
To reply to this ticket, simply reply to this email.
"""

    return text.strip()


def get_email_subject(
    template_name: str,
    ticket_number: str,
    title: str = ""
) -> str:
    """
    Generate email subject line for notification type.

    Args:
        template_name: Template name
        ticket_number: Ticket number
        title: Ticket title (optional)

    Returns:
        Formatted email subject
    """
    subjects = {
        "ticket_created": f"[{ticket_number}] New Ticket: {title}",
        "ticket_assigned": f"[{ticket_number}] Ticket Assigned: {title}",
        "comment_added": f"Re: [{ticket_number}] {title}",
        "ticket_resolved": f"[{ticket_number}] Ticket Resolved: {title}",
        "sla_warning": f"[{ticket_number}] SLA Warning: {title}",
        "sla_breach": f"[{ticket_number}] SLA Breach Alert: {title}"
    }

    subject = subjects.get(template_name, f"[{ticket_number}] {title}")

    # Truncate if too long (max 78 chars recommended for email subjects)
    if len(subject) > 78:
        subject = subject[:75] + "..."

    return subject
