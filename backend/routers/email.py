"""
Email Integration Router - Email configuration management and testing.
Superadmin only access for email settings.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr
import logging

from backend.core.database import get_db
from backend.core.security import get_current_superadmin_user
from backend import models

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email", tags=["email"])


# ==================== PYDANTIC SCHEMAS ====================

class EmailConfigurationCreate(BaseModel):
    """Schema for creating an email configuration."""
    name: str
    entity_id: Optional[int] = None
    provider_type: str  # smtp_imap, microsoft_365
    is_active: bool = True
    is_inbound_enabled: bool = False
    is_outbound_enabled: bool = True

    # SMTP settings
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True

    # IMAP settings
    imap_host: Optional[str] = None
    imap_port: int = 993
    imap_username: Optional[str] = None
    imap_password: Optional[str] = None
    imap_use_ssl: bool = True
    imap_folder: str = "INBOX"

    # Microsoft 365 settings
    m365_tenant_id: Optional[str] = None
    m365_client_id: Optional[str] = None
    m365_client_secret: Optional[str] = None
    m365_user_email: Optional[str] = None
    m365_mailbox: Optional[str] = None
    m365_folder_id: Optional[str] = None

    # Common settings
    from_email: Optional[str] = None
    from_name: str = "Inframate"
    reply_to_email: Optional[str] = None


class EmailConfigurationUpdate(BaseModel):
    """Schema for updating an email configuration."""
    name: Optional[str] = None
    provider_type: Optional[str] = None
    is_active: Optional[bool] = None
    is_inbound_enabled: Optional[bool] = None
    is_outbound_enabled: Optional[bool] = None

    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: Optional[bool] = None

    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    imap_username: Optional[str] = None
    imap_password: Optional[str] = None
    imap_use_ssl: Optional[bool] = None
    imap_folder: Optional[str] = None

    m365_tenant_id: Optional[str] = None
    m365_client_id: Optional[str] = None
    m365_client_secret: Optional[str] = None
    m365_user_email: Optional[str] = None
    m365_mailbox: Optional[str] = None
    m365_folder_id: Optional[str] = None

    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to_email: Optional[str] = None


class EmailConfigurationResponse(BaseModel):
    """Response schema for email configuration."""
    id: int
    name: str
    entity_id: Optional[int] = None
    provider_type: str
    is_active: bool
    is_inbound_enabled: bool
    is_outbound_enabled: bool

    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_use_tls: Optional[bool] = None

    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    imap_use_ssl: Optional[bool] = None
    imap_folder: Optional[str] = None

    m365_tenant_id: Optional[str] = None
    m365_client_id: Optional[str] = None
    m365_user_email: Optional[str] = None
    m365_mailbox: Optional[str] = None
    m365_folder_id: Optional[str] = None

    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to_email: Optional[str] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SentEmailResponse(BaseModel):
    """Response schema for sent email."""
    id: int
    ticket_id: Optional[int] = None
    message_id: str
    recipient_email: str
    subject: str
    email_type: str
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InboundEmailResponse(BaseModel):
    """Response schema for inbound email."""
    id: int
    message_id: str
    from_email: str
    from_name: Optional[str] = None
    to_email: str
    subject: str
    processing_status: str
    processing_result: Optional[dict] = None
    error_message: Optional[str] = None
    received_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestEmailRequest(BaseModel):
    """Request schema for sending test email."""
    to_email: EmailStr


# ==================== CONFIGURATION ENDPOINTS ====================

@router.get("/configurations", response_model=List[EmailConfigurationResponse])
def list_email_configurations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superadmin_user)
):
    """List all email configurations."""
    configs = db.query(models.EmailConfiguration).order_by(
        models.EmailConfiguration.name
    ).all()

    # Mask sensitive fields in response
    result = []
    for config in configs:
        response = EmailConfigurationResponse(
            id=config.id,
            name=config.name,
            entity_id=config.entity_id,
            provider_type=config.provider_type,
            is_active=config.is_active,
            is_inbound_enabled=config.is_inbound_enabled,
            is_outbound_enabled=config.is_outbound_enabled,
            smtp_host=config.smtp_host,
            smtp_port=config.smtp_port,
            smtp_username=config.smtp_username,
            smtp_use_tls=config.smtp_use_tls,
            imap_host=config.imap_host,
            imap_port=config.imap_port,
            imap_use_ssl=config.imap_use_ssl,
            imap_folder=config.imap_folder,
            m365_tenant_id=config.m365_tenant_id,
            m365_client_id=config.m365_client_id,
            m365_user_email=config.m365_user_email,
            m365_mailbox=config.m365_mailbox,
            m365_folder_id=config.m365_folder_id,
            from_email=config.from_email,
            from_name=config.from_name,
            reply_to_email=config.reply_to_email,
            created_at=config.created_at,
            updated_at=config.updated_at
        )
        result.append(response)

    return result


@router.get("/configurations/{config_id}", response_model=EmailConfigurationResponse)
def get_email_configuration(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superadmin_user)
):
    """Get a specific email configuration."""
    config = db.query(models.EmailConfiguration).filter(
        models.EmailConfiguration.id == config_id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Email configuration not found")

    return EmailConfigurationResponse(
        id=config.id,
        name=config.name,
        entity_id=config.entity_id,
        provider_type=config.provider_type,
        is_active=config.is_active,
        is_inbound_enabled=config.is_inbound_enabled,
        is_outbound_enabled=config.is_outbound_enabled,
        smtp_host=config.smtp_host,
        smtp_port=config.smtp_port,
        smtp_username=config.smtp_username,
        smtp_use_tls=config.smtp_use_tls,
        imap_host=config.imap_host,
        imap_port=config.imap_port,
        imap_use_ssl=config.imap_use_ssl,
        imap_folder=config.imap_folder,
        m365_tenant_id=config.m365_tenant_id,
        m365_client_id=config.m365_client_id,
        m365_user_email=config.m365_user_email,
        m365_mailbox=config.m365_mailbox,
        m365_folder_id=config.m365_folder_id,
        from_email=config.from_email,
        from_name=config.from_name,
        reply_to_email=config.reply_to_email,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.post("/configurations", response_model=EmailConfigurationResponse)
def create_email_configuration(
    config_data: EmailConfigurationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superadmin_user)
):
    """Create a new email configuration."""
    # Validate provider type
    if config_data.provider_type not in ["smtp_imap", "microsoft_365"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid provider_type. Must be 'smtp_imap' or 'microsoft_365'"
        )

    # Validate required fields based on provider
    if config_data.provider_type == "smtp_imap":
        if config_data.is_outbound_enabled and not config_data.smtp_host:
            raise HTTPException(status_code=400, detail="SMTP host is required for outbound email")
        if config_data.is_inbound_enabled and not config_data.imap_host:
            raise HTTPException(status_code=400, detail="IMAP host is required for inbound email")
    elif config_data.provider_type == "microsoft_365":
        if not all([config_data.m365_tenant_id, config_data.m365_client_id, config_data.m365_client_secret, config_data.m365_mailbox]):
            raise HTTPException(
                status_code=400,
                detail="Microsoft 365 requires tenant_id, client_id, client_secret, and mailbox"
            )

    config = models.EmailConfiguration(
        name=config_data.name,
        entity_id=config_data.entity_id,
        provider_type=config_data.provider_type,
        is_active=config_data.is_active,
        is_inbound_enabled=config_data.is_inbound_enabled,
        is_outbound_enabled=config_data.is_outbound_enabled,
        smtp_host=config_data.smtp_host,
        smtp_port=config_data.smtp_port,
        smtp_username=config_data.smtp_username,
        smtp_password=config_data.smtp_password,
        smtp_use_tls=config_data.smtp_use_tls,
        imap_host=config_data.imap_host,
        imap_port=config_data.imap_port,
        imap_username=config_data.imap_username,
        imap_password=config_data.imap_password,
        imap_use_ssl=config_data.imap_use_ssl,
        imap_folder=config_data.imap_folder,
        m365_tenant_id=config_data.m365_tenant_id,
        m365_client_id=config_data.m365_client_id,
        m365_client_secret=config_data.m365_client_secret,
        m365_user_email=config_data.m365_user_email,
        m365_mailbox=config_data.m365_mailbox,
        m365_folder_id=config_data.m365_folder_id,
        from_email=config_data.from_email,
        from_name=config_data.from_name,
        reply_to_email=config_data.reply_to_email
    )

    db.add(config)
    db.commit()
    db.refresh(config)

    logger.info(f"Email configuration '{config.name}' created by {current_user.username}")

    return EmailConfigurationResponse(
        id=config.id,
        name=config.name,
        entity_id=config.entity_id,
        provider_type=config.provider_type,
        is_active=config.is_active,
        is_inbound_enabled=config.is_inbound_enabled,
        is_outbound_enabled=config.is_outbound_enabled,
        smtp_host=config.smtp_host,
        smtp_port=config.smtp_port,
        smtp_username=config.smtp_username,
        smtp_use_tls=config.smtp_use_tls,
        imap_host=config.imap_host,
        imap_port=config.imap_port,
        imap_use_ssl=config.imap_use_ssl,
        imap_folder=config.imap_folder,
        m365_tenant_id=config.m365_tenant_id,
        m365_client_id=config.m365_client_id,
        m365_user_email=config.m365_user_email,
        m365_mailbox=config.m365_mailbox,
        m365_folder_id=config.m365_folder_id,
        from_email=config.from_email,
        from_name=config.from_name,
        reply_to_email=config.reply_to_email,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.put("/configurations/{config_id}", response_model=EmailConfigurationResponse)
def update_email_configuration(
    config_id: int,
    config_data: EmailConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superadmin_user)
):
    """Update an email configuration."""
    config = db.query(models.EmailConfiguration).filter(
        models.EmailConfiguration.id == config_id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Email configuration not found")

    # Update fields if provided
    update_data = config_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    config.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(config)

    logger.info(f"Email configuration '{config.name}' updated by {current_user.username}")

    return EmailConfigurationResponse(
        id=config.id,
        name=config.name,
        entity_id=config.entity_id,
        provider_type=config.provider_type,
        is_active=config.is_active,
        is_inbound_enabled=config.is_inbound_enabled,
        is_outbound_enabled=config.is_outbound_enabled,
        smtp_host=config.smtp_host,
        smtp_port=config.smtp_port,
        smtp_username=config.smtp_username,
        smtp_use_tls=config.smtp_use_tls,
        imap_host=config.imap_host,
        imap_port=config.imap_port,
        imap_use_ssl=config.imap_use_ssl,
        imap_folder=config.imap_folder,
        m365_tenant_id=config.m365_tenant_id,
        m365_client_id=config.m365_client_id,
        m365_mailbox=config.m365_mailbox,
        from_email=config.from_email,
        from_name=config.from_name,
        reply_to_email=config.reply_to_email,
        created_at=config.created_at,
        updated_at=config.updated_at
    )


@router.delete("/configurations/{config_id}")
def delete_email_configuration(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superadmin_user)
):
    """Delete an email configuration."""
    config = db.query(models.EmailConfiguration).filter(
        models.EmailConfiguration.id == config_id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Email configuration not found")

    name = config.name
    db.delete(config)
    db.commit()

    logger.info(f"Email configuration '{name}' deleted by {current_user.username}")
    return {"message": f"Email configuration '{name}' deleted"}


# ==================== TEST CREDENTIALS WITHOUT SAVING ====================

class TestM365CredentialsRequest(BaseModel):
    """Schema for testing M365 credentials without saving."""
    tenant_id: str
    client_id: str
    client_secret: str
    mailbox: str


class TestSmtpCredentialsRequest(BaseModel):
    """Schema for testing SMTP credentials without saving."""
    smtp_host: str
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True


@router.post("/test-m365-credentials")
async def test_m365_credentials(
    request: TestM365CredentialsRequest,
    current_user: models.User = Depends(get_current_superadmin_user)
):
    """Test Microsoft 365 credentials without creating a configuration."""
    if not all([request.tenant_id, request.client_id, request.client_secret, request.mailbox]):
        raise HTTPException(
            status_code=400,
            detail="All M365 fields are required: tenant_id, client_id, client_secret, mailbox"
        )

    try:
        from backend.core.email.microsoft365 import Microsoft365Client

        client = Microsoft365Client(
            tenant_id=request.tenant_id,
            client_id=request.client_id,
            client_secret=request.client_secret,
            mailbox=request.mailbox
        )

        # Test connection by fetching mailbox info
        result = await client.test_connection()

        logger.info(f"M365 credentials test successful for mailbox '{request.mailbox}' by {current_user.username}")
        return {
            "message": "Microsoft 365 connection successful",
            "mailbox": result.get("mail", request.mailbox),
            "display_name": result.get("displayName", "")
        }

    except Exception as e:
        logger.error(f"M365 credentials test failed: {e}")
        error_msg = str(e)
        # Provide more user-friendly error messages
        if "AADSTS700016" in error_msg:
            detail = "Application not found in tenant. Check your Client ID and Tenant ID."
        elif "AADSTS7000215" in error_msg:
            detail = "Invalid client secret. Please verify the secret is correct and not expired."
        elif "AADSTS90002" in error_msg:
            detail = "Tenant not found. Check your Tenant ID."
        elif "AADSTS50034" in error_msg:
            detail = "User account does not exist. Check the mailbox address."
        elif "403" in error_msg or "Forbidden" in error_msg:
            detail = "Access denied. Ensure the application has Mail.Read and Mail.Send permissions."
        elif "404" in error_msg or "MailboxNotFound" in error_msg:
            detail = f"Mailbox '{request.mailbox}' not found. Check the email address."
        else:
            detail = f"Microsoft 365 connection failed: {error_msg}"
        raise HTTPException(status_code=400, detail=detail)


@router.post("/test-smtp-credentials")
async def test_smtp_credentials(
    request: TestSmtpCredentialsRequest,
    current_user: models.User = Depends(get_current_superadmin_user)
):
    """Test SMTP credentials without creating a configuration."""
    import smtplib

    if not request.smtp_host:
        raise HTTPException(status_code=400, detail="SMTP host is required")

    try:
        # Test connection
        if request.smtp_use_tls:
            server = smtplib.SMTP(request.smtp_host, request.smtp_port, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP(request.smtp_host, request.smtp_port, timeout=10)

        if request.smtp_username and request.smtp_password:
            server.login(request.smtp_username, request.smtp_password)

        server.quit()

        logger.info(f"SMTP credentials test successful for '{request.smtp_host}' by {current_user.username}")
        return {"message": "SMTP connection successful"}

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP auth test failed: {e}")
        raise HTTPException(status_code=400, detail="SMTP authentication failed. Check username and password.")
    except smtplib.SMTPConnectError as e:
        logger.error(f"SMTP connect test failed: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to connect to SMTP server at {request.smtp_host}:{request.smtp_port}")
    except OSError as e:
        logger.error(f"SMTP test network error: {e}")
        if "getaddrinfo failed" in str(e) or "Name or service not known" in str(e):
            raise HTTPException(status_code=400, detail=f"Cannot resolve hostname '{request.smtp_host}'. Check the server address.")
        elif "Connection refused" in str(e):
            raise HTTPException(status_code=400, detail=f"Connection refused at {request.smtp_host}:{request.smtp_port}. Check host and port.")
        elif "timed out" in str(e).lower():
            raise HTTPException(status_code=400, detail=f"Connection timed out. Server at {request.smtp_host}:{request.smtp_port} is not responding.")
        raise HTTPException(status_code=400, detail=f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"SMTP test failed: {e}")
        raise HTTPException(status_code=400, detail=f"SMTP test failed: {str(e)}")


# ==================== TEST EXISTING CONFIG ENDPOINTS ====================

@router.post("/configurations/{config_id}/test-smtp")
async def test_smtp_connection(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superadmin_user)
):
    """Test SMTP connection for a configuration."""
    import smtplib
    from email.mime.text import MIMEText

    config = db.query(models.EmailConfiguration).filter(
        models.EmailConfiguration.id == config_id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Email configuration not found")

    if config.provider_type != "smtp_imap":
        raise HTTPException(status_code=400, detail="This configuration is not SMTP/IMAP")

    if not config.smtp_host:
        raise HTTPException(status_code=400, detail="SMTP host not configured")

    try:
        # Test connection
        if config.smtp_use_tls:
            server = smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=10)

        if config.smtp_username and config.smtp_password:
            server.login(config.smtp_username, config.smtp_password)

        server.quit()

        logger.info(f"SMTP test successful for config '{config.name}' by {current_user.username}")
        return {"message": "SMTP connection successful"}

    except smtplib.SMTPAuthenticationError:
        raise HTTPException(status_code=400, detail="SMTP authentication failed")
    except smtplib.SMTPConnectError:
        raise HTTPException(status_code=400, detail="Failed to connect to SMTP server")
    except Exception as e:
        logger.error(f"SMTP test failed: {e}")
        raise HTTPException(status_code=400, detail=f"SMTP test failed: {str(e)}")


@router.post("/configurations/{config_id}/test-imap")
async def test_imap_connection(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superadmin_user)
):
    """Test IMAP connection for a configuration."""
    import imaplib

    config = db.query(models.EmailConfiguration).filter(
        models.EmailConfiguration.id == config_id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Email configuration not found")

    if config.provider_type != "smtp_imap":
        raise HTTPException(status_code=400, detail="This configuration is not SMTP/IMAP")

    if not config.imap_host:
        raise HTTPException(status_code=400, detail="IMAP host not configured")

    try:
        # Test connection
        if config.imap_use_ssl:
            imap = imaplib.IMAP4_SSL(config.imap_host, config.imap_port)
        else:
            imap = imaplib.IMAP4(config.imap_host, config.imap_port)

        username = config.imap_username or config.smtp_username
        password = config.imap_password or config.smtp_password

        if username and password:
            imap.login(username, password)

        # Test folder selection
        folder = config.imap_folder or "INBOX"
        status, data = imap.select(folder, readonly=True)

        if status != "OK":
            raise Exception(f"Failed to select folder '{folder}'")

        # Get message count
        msg_count = int(data[0])

        imap.close()
        imap.logout()

        logger.info(f"IMAP test successful for config '{config.name}' by {current_user.username}")
        return {"message": f"IMAP connection successful. {msg_count} messages in {folder}"}

    except imaplib.IMAP4.error as e:
        raise HTTPException(status_code=400, detail=f"IMAP error: {str(e)}")
    except Exception as e:
        logger.error(f"IMAP test failed: {e}")
        raise HTTPException(status_code=400, detail=f"IMAP test failed: {str(e)}")


@router.post("/configurations/{config_id}/test-m365")
async def test_m365_connection(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superadmin_user)
):
    """Test Microsoft 365 connection for a configuration."""
    config = db.query(models.EmailConfiguration).filter(
        models.EmailConfiguration.id == config_id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Email configuration not found")

    if config.provider_type != "microsoft_365":
        raise HTTPException(status_code=400, detail="This configuration is not Microsoft 365")

    if not all([config.m365_tenant_id, config.m365_client_id, config.m365_client_secret, config.m365_mailbox]):
        raise HTTPException(status_code=400, detail="Microsoft 365 configuration incomplete")

    try:
        from backend.core.email.microsoft365 import Microsoft365Client

        client = Microsoft365Client(
            tenant_id=config.m365_tenant_id,
            client_id=config.m365_client_id,
            client_secret=config.m365_client_secret,
            mailbox=config.m365_mailbox
        )

        # Test connection by fetching mailbox info
        result = await client.test_connection()

        logger.info(f"M365 test successful for config '{config.name}' by {current_user.username}")
        return {
            "message": f"Microsoft 365 connection successful",
            "mailbox": result.get("mail", config.m365_mailbox),
            "display_name": result.get("displayName", "")
        }

    except Exception as e:
        logger.error(f"M365 test failed: {e}")
        raise HTTPException(status_code=400, detail=f"Microsoft 365 test failed: {str(e)}")


@router.post("/send-test")
async def send_test_email(
    request: TestEmailRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superadmin_user)
):
    """Send a test email using the active configuration."""
    from backend.core.email.sender import get_active_email_config, EmailSender
    from backend.core.email.templates import render_email_template

    config = get_active_email_config(db)
    if not config:
        raise HTTPException(status_code=400, detail="No active email configuration found")

    try:
        # Render test email
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #0ea5e9; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #fff; padding: 20px; border: 1px solid #e5e7eb; }}
        .footer {{ background: #f8fafc; padding: 15px; text-align: center; font-size: 12px; color: #64748b; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Inframate</h1>
        </div>
        <div class="content">
            <h2>Test Email</h2>
            <p>This is a test email from Inframate.</p>
            <p>If you received this email, your email configuration is working correctly.</p>
            <p><strong>Configuration:</strong> {config.name}</p>
            <p><strong>Provider:</strong> {config.provider_type}</p>
            <p><strong>Sent by:</strong> {current_user.username}</p>
        </div>
        <div class="footer">
            <p>This is an automated test email from Inframate.</p>
        </div>
    </div>
</body>
</html>
"""
        text_content = f"""
Inframate - Test Email

This is a test email from Inframate.
If you received this email, your email configuration is working correctly.

Configuration: {config.name}
Provider: {config.provider_type}
Sent by: {current_user.username}

--
This is an automated test email from Inframate.
"""

        sender = EmailSender(config)
        message_id = await sender.send(
            to_email=request.to_email,
            subject="Inframate - Test Email",
            body_html=html_content,
            body_text=text_content
        )

        logger.info(f"Test email sent to {request.to_email} by {current_user.username}")
        return {
            "message": f"Test email sent to {request.to_email}",
            "message_id": message_id
        }

    except Exception as e:
        logger.error(f"Failed to send test email: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to send test email: {str(e)}")


# ==================== EMAIL LOG ENDPOINTS ====================

@router.get("/sent", response_model=List[SentEmailResponse])
def list_sent_emails(
    ticket_id: Optional[int] = None,
    status: Optional[str] = None,
    email_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superadmin_user)
):
    """List sent emails with optional filters."""
    query = db.query(models.SentEmail)

    if ticket_id:
        query = query.filter(models.SentEmail.ticket_id == ticket_id)
    if status:
        query = query.filter(models.SentEmail.status == status)
    if email_type:
        query = query.filter(models.SentEmail.email_type == email_type)

    emails = query.order_by(
        models.SentEmail.created_at.desc()
    ).offset(offset).limit(limit).all()

    return emails


@router.get("/sent/{email_id}", response_model=SentEmailResponse)
def get_sent_email(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superadmin_user)
):
    """Get a specific sent email."""
    email = db.query(models.SentEmail).filter(
        models.SentEmail.id == email_id
    ).first()

    if not email:
        raise HTTPException(status_code=404, detail="Sent email not found")

    return email


@router.get("/inbound", response_model=List[InboundEmailResponse])
def list_inbound_emails(
    processing_status: Optional[str] = None,
    from_email: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superadmin_user)
):
    """List inbound emails with optional filters."""
    query = db.query(models.InboundEmail)

    if processing_status:
        query = query.filter(models.InboundEmail.processing_status == processing_status)
    if from_email:
        query = query.filter(models.InboundEmail.from_email.ilike(f"%{from_email}%"))

    emails = query.order_by(
        models.InboundEmail.received_at.desc()
    ).offset(offset).limit(limit).all()

    return emails


@router.get("/inbound/{email_id}", response_model=InboundEmailResponse)
def get_inbound_email(
    email_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superadmin_user)
):
    """Get a specific inbound email."""
    email = db.query(models.InboundEmail).filter(
        models.InboundEmail.id == email_id
    ).first()

    if not email:
        raise HTTPException(status_code=404, detail="Inbound email not found")

    return email


# ==================== MANUAL TRIGGER ENDPOINTS ====================

@router.post("/poll-inbox")
async def trigger_inbox_poll(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superadmin_user)
):
    """Manually trigger inbox polling for all active inbound configurations."""
    from backend.core.email.receiver import get_active_inbound_configs

    configs = get_active_inbound_configs(db)

    if not configs:
        raise HTTPException(status_code=400, detail="No active inbound email configurations found")

    # Trigger Celery task
    try:
        from worker.tasks import poll_email_inbox_task
        poll_email_inbox_task.delay()
        logger.info(f"Inbox poll triggered by {current_user.username}")
        return {"message": f"Inbox polling triggered for {len(configs)} configuration(s)"}
    except Exception as e:
        logger.error(f"Failed to trigger inbox poll: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger inbox poll: {str(e)}")


# ==================== MICROSOFT 365 HELPER ENDPOINTS ====================

@router.get("/configurations/{config_id}/m365-mailboxes")
async def get_m365_mailboxes(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superadmin_user)
):
    """Fetch available mailboxes from Microsoft 365 for this configuration."""
    config = db.query(models.EmailConfiguration).filter(
        models.EmailConfiguration.id == config_id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Email configuration not found")

    if config.provider_type != "microsoft_365":
        raise HTTPException(status_code=400, detail="This configuration is not Microsoft 365")

    if not all([config.m365_tenant_id, config.m365_client_id, config.m365_client_secret]):
        raise HTTPException(status_code=400, detail="Microsoft 365 credentials not configured")

    try:
        from backend.core.email.microsoft365 import Microsoft365Client

        client = Microsoft365Client(
            tenant_id=config.m365_tenant_id,
            client_id=config.m365_client_id,
            client_secret=config.m365_client_secret,
            mailbox=config.m365_user_email or config.m365_mailbox  # Use user email if set
        )

        # Fetch available mailboxes (shared mailboxes the user/app has access to)
        mailboxes = await client.list_mailboxes()

        logger.info(f"Fetched {len(mailboxes)} mailboxes for config '{config.name}' by {current_user.username}")
        return {"mailboxes": mailboxes}

    except Exception as e:
        logger.error(f"Failed to fetch M365 mailboxes: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch mailboxes: {str(e)}")


@router.get("/configurations/{config_id}/m365-folders")
async def get_m365_folders(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superadmin_user)
):
    """Fetch mail folders from Microsoft 365 for the configured mailbox."""
    config = db.query(models.EmailConfiguration).filter(
        models.EmailConfiguration.id == config_id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Email configuration not found")

    if config.provider_type != "microsoft_365":
        raise HTTPException(status_code=400, detail="This configuration is not Microsoft 365")

    if not all([config.m365_tenant_id, config.m365_client_id, config.m365_client_secret]):
        raise HTTPException(status_code=400, detail="Microsoft 365 credentials not configured")

    if not config.m365_mailbox:
        raise HTTPException(status_code=400, detail="No mailbox selected")

    try:
        from backend.core.email.microsoft365 import Microsoft365Client

        client = Microsoft365Client(
            tenant_id=config.m365_tenant_id,
            client_id=config.m365_client_id,
            client_secret=config.m365_client_secret,
            mailbox=config.m365_mailbox
        )

        # Fetch available folders in the mailbox
        folders = await client.list_folders()

        logger.info(f"Fetched {len(folders)} folders for mailbox '{config.m365_mailbox}' by {current_user.username}")
        return {"folders": folders}

    except Exception as e:
        logger.error(f"Failed to fetch M365 folders: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch folders: {str(e)}")


@router.get("/configurations/{config_id}/imap-folders")
async def get_imap_folders(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_superadmin_user)
):
    """Fetch mail folders from IMAP server for the configured account."""
    import imaplib

    config = db.query(models.EmailConfiguration).filter(
        models.EmailConfiguration.id == config_id
    ).first()

    if not config:
        raise HTTPException(status_code=404, detail="Email configuration not found")

    if config.provider_type != "smtp_imap":
        raise HTTPException(status_code=400, detail="This configuration is not SMTP/IMAP")

    if not config.imap_host:
        raise HTTPException(status_code=400, detail="IMAP host not configured")

    try:
        # Connect to IMAP server
        if config.imap_use_ssl:
            imap = imaplib.IMAP4_SSL(config.imap_host, config.imap_port)
        else:
            imap = imaplib.IMAP4(config.imap_host, config.imap_port)

        username = config.imap_username or config.smtp_username
        password = config.imap_password or config.smtp_password

        if username and password:
            imap.login(username, password)

        # List all folders
        status, folder_data = imap.list()

        folders = []
        if status == "OK":
            for item in folder_data:
                if item:
                    # Parse IMAP folder response: (flags) "delimiter" "folder_name"
                    decoded = item.decode() if isinstance(item, bytes) else item
                    # Extract folder name from response like: (\HasNoChildren) "/" "INBOX"
                    parts = decoded.rsplit('"', 2)
                    if len(parts) >= 2:
                        folder_name = parts[-2]
                        # Skip system folders that start with [Gmail] or similar
                        if not folder_name.startswith('['):
                            folders.append({
                                "id": folder_name,
                                "displayName": folder_name
                            })

        imap.logout()

        logger.info(f"Fetched {len(folders)} IMAP folders for config '{config.name}' by {current_user.username}")
        return {"folders": folders}

    except imaplib.IMAP4.error as e:
        logger.error(f"IMAP error fetching folders: {e}")
        raise HTTPException(status_code=400, detail=f"IMAP error: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to fetch IMAP folders: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to fetch folders: {str(e)}")
