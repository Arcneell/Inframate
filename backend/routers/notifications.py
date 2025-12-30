"""
Notification Router for in-app notifications.
Provides real-time notification management for users.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime, timezone
import logging

from backend.core.database import get_db
from backend.core.security import get_current_user
from backend import models, schemas

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=List[schemas.Notification])
def list_notifications(
    unread_only: bool = False,
    notification_type: Optional[str] = None,
    skip: int = 0,
    limit: int = Query(default=50, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get notifications for current user."""
    query = db.query(models.Notification).filter(
        models.Notification.user_id == current_user.id
    )

    if unread_only:
        query = query.filter(models.Notification.is_read == False)

    if notification_type:
        query = query.filter(models.Notification.notification_type == notification_type)

    # Exclude expired notifications
    now = datetime.now(timezone.utc)
    query = query.filter(
        (models.Notification.expires_at == None) |
        (models.Notification.expires_at > now)
    )

    notifications = query.order_by(
        models.Notification.created_at.desc()
    ).offset(skip).limit(limit).all()

    return notifications


@router.get("/count", response_model=schemas.NotificationCount)
def get_notification_count(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get notification counts (total and unread)."""
    now = datetime.now(timezone.utc)

    # Base query excluding expired
    base_query = db.query(models.Notification).filter(
        and_(
            models.Notification.user_id == current_user.id,
            (models.Notification.expires_at == None) |
            (models.Notification.expires_at > now)
        )
    )

    total = base_query.count()
    unread = base_query.filter(models.Notification.is_read == False).count()

    return schemas.NotificationCount(total=total, unread=unread)


@router.get("/{notification_id}", response_model=schemas.Notification)
def get_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Get a specific notification."""
    notification = db.query(models.Notification).filter(
        and_(
            models.Notification.id == notification_id,
            models.Notification.user_id == current_user.id
        )
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    return notification


@router.put("/{notification_id}/read")
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mark a notification as read."""
    notification = db.query(models.Notification).filter(
        and_(
            models.Notification.id == notification_id,
            models.Notification.user_id == current_user.id
        )
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Notification marked as read"}


@router.put("/read-all")
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Mark all notifications as read."""
    now = datetime.now(timezone.utc)

    db.query(models.Notification).filter(
        and_(
            models.Notification.user_id == current_user.id,
            models.Notification.is_read == False
        )
    ).update({
        "is_read": True,
        "read_at": now
    })

    db.commit()
    return {"message": "All notifications marked as read"}


@router.delete("/{notification_id}")
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a notification."""
    notification = db.query(models.Notification).filter(
        and_(
            models.Notification.id == notification_id,
            models.Notification.user_id == current_user.id
        )
    ).first()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    db.delete(notification)
    db.commit()

    return {"message": "Notification deleted"}


@router.delete("/")
def delete_all_read(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete all read notifications."""
    db.query(models.Notification).filter(
        and_(
            models.Notification.user_id == current_user.id,
            models.Notification.is_read == True
        )
    ).delete()

    db.commit()
    return {"message": "Read notifications deleted"}


# ==================== ADMIN ENDPOINTS ====================

@router.post("/", response_model=schemas.Notification)
def create_notification(
    notification_data: schemas.NotificationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Create a notification (admin or system use)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    # Verify target user exists
    target_user = db.query(models.User).filter(
        models.User.id == notification_data.user_id
    ).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Target user not found")

    notification = models.Notification(
        user_id=notification_data.user_id,
        title=notification_data.title,
        message=notification_data.message,
        notification_type=notification_data.notification_type,
        link_type=notification_data.link_type,
        link_id=notification_data.link_id,
        expires_at=notification_data.expires_at
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    logger.info(f"Notification created for user {target_user.username}")
    return notification


@router.post("/broadcast")
def broadcast_notification(
    title: str,
    message: str,
    notification_type: str = "info",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Send notification to all active users (admin only)."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    users = db.query(models.User).filter(models.User.is_active == True).all()

    for user in users:
        notification = models.Notification(
            user_id=user.id,
            title=title,
            message=message,
            notification_type=notification_type
        )
        db.add(notification)

    db.commit()

    logger.info(f"Broadcast notification sent to {len(users)} users by {current_user.username}")
    return {"message": f"Notification sent to {len(users)} users"}
