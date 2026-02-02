"""
Granular Permission System for Inframate.

This module provides utilities for checking granular permissions stored in the
User.permissions JSONB field. It replaces role-based checks with more flexible
permission-based access control.

Permission Format:
    Permissions follow the pattern: "module:action"
    Examples:
        - tickets:view      - Can view all tickets
        - tickets:edit      - Can edit tickets
        - tickets:assign    - Can assign tickets to users
        - tickets:delete    - Can delete tickets
        - tickets:resolve   - Can resolve/close tickets
        - tickets:admin     - Full ticket administration

Role Hierarchy:
    - superadmin: Full access to everything (bypasses permission checks)
    - admin: Full access to most features (bypasses permission checks)
    - tech: Access based on permissions array
    - user: Limited access (own resources only)
"""

from typing import List, Optional, Union
from functools import wraps
from fastapi import HTTPException, Depends
from backend import models


# ==================== PERMISSION DEFINITIONS ====================

# Ticket permissions
TICKET_PERMISSIONS = {
    "tickets:view": "Can view all tickets (not just own)",
    "tickets:edit": "Can edit any ticket",
    "tickets:assign": "Can assign tickets to users",
    "tickets:delete": "Can delete tickets",
    "tickets:resolve": "Can resolve and close tickets",
    "tickets:admin": "Full ticket administration (includes all above)",
}

# All available permissions
ALL_PERMISSIONS = {
    **TICKET_PERMISSIONS,
    # Future: Add IPAM, Inventory, DCIM permissions here
    "ipam:view": "Can view IPAM data",
    "ipam:edit": "Can edit IPAM data",
    "inventory:view": "Can view inventory",
    "inventory:edit": "Can edit inventory",
    "dcim:view": "Can view DCIM data",
    "dcim:edit": "Can edit DCIM data",
    "contracts:view": "Can view contracts",
    "contracts:edit": "Can edit contracts",
    "software:view": "Can view software licenses",
    "software:edit": "Can edit software licenses",
    "knowledge:view": "Can view knowledge base",
    "knowledge:edit": "Can edit knowledge base articles",
}


# ==================== PERMISSION CHECKING FUNCTIONS ====================

def has_permission(user: models.User, permission: str) -> bool:
    """
    Check if a user has a specific permission.

    Args:
        user: The User model instance
        permission: Permission string (e.g., "tickets:edit")

    Returns:
        True if user has the permission, False otherwise

    Notes:
        - superadmin and admin roles bypass all permission checks
        - For tech users, checks the permissions JSONB array
        - Supports wildcard admin permissions (e.g., "tickets:admin" grants all tickets:* permissions)
    """
    if not user:
        return False

    # Superadmin and admin bypass all permission checks
    if user.role in ("superadmin", "admin"):
        return True

    # Regular users have no granular permissions
    if user.role == "user":
        return False

    # Tech users - check permissions array
    if user.role == "tech":
        permissions = user.permissions or []

        # Direct permission check
        if permission in permissions:
            return True

        # Check for admin permission in the same module
        # e.g., "tickets:admin" grants all "tickets:*" permissions
        module = permission.split(":")[0]
        admin_permission = f"{module}:admin"
        if admin_permission in permissions:
            return True

        # Legacy permission format support (e.g., "tickets_admin" -> "tickets:admin")
        legacy_permission = permission.replace(":", "_")
        if legacy_permission in permissions:
            return True

        legacy_admin = f"{module}_admin"
        if legacy_admin in permissions:
            return True

    return False


def has_any_permission(user: models.User, permissions: List[str]) -> bool:
    """
    Check if a user has any of the specified permissions.

    Args:
        user: The User model instance
        permissions: List of permission strings

    Returns:
        True if user has at least one of the permissions
    """
    return any(has_permission(user, perm) for perm in permissions)


def has_all_permissions(user: models.User, permissions: List[str]) -> bool:
    """
    Check if a user has all of the specified permissions.

    Args:
        user: The User model instance
        permissions: List of permission strings

    Returns:
        True if user has all of the permissions
    """
    return all(has_permission(user, perm) for perm in permissions)


def can_access_tickets(user: models.User) -> bool:
    """
    Check if user can access the tickets module (view all tickets).

    Regular users can only see their own tickets.
    Tech/admin/superadmin can see all tickets if they have tickets:view or tickets:admin.
    """
    if user.role in ("superadmin", "admin"):
        return True

    if user.role == "tech":
        return has_any_permission(user, ["tickets:view", "tickets:admin"])

    return False


def can_manage_ticket(user: models.User, action: str = "edit") -> bool:
    """
    Check if user can perform a specific action on tickets.

    Args:
        user: The User model instance
        action: The action to check (edit, assign, delete, resolve)

    Returns:
        True if user can perform the action
    """
    permission = f"tickets:{action}"
    return has_permission(user, permission)


def can_edit_ticket(user: models.User) -> bool:
    """Check if user can edit tickets."""
    return has_any_permission(user, ["tickets:edit", "tickets:admin"])


def can_assign_ticket(user: models.User) -> bool:
    """Check if user can assign tickets to users."""
    return has_any_permission(user, ["tickets:assign", "tickets:admin"])


def can_delete_ticket(user: models.User) -> bool:
    """Check if user can delete tickets."""
    return has_any_permission(user, ["tickets:delete", "tickets:admin"])


def can_resolve_ticket(user: models.User) -> bool:
    """Check if user can resolve/close tickets."""
    return has_any_permission(user, ["tickets:resolve", "tickets:admin"])


# ==================== PERMISSION REQUIREMENT DECORATORS ====================

def require_permission(permission: str):
    """
    Decorator factory to require a specific permission for an endpoint.

    Usage:
        @router.get("/admin-action")
        @require_permission("tickets:admin")
        def admin_action(current_user: models.User = Depends(get_current_user)):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Find current_user in kwargs
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")

            if not has_permission(current_user, permission):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: requires '{permission}'"
                )

            return func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(permissions: List[str]):
    """
    Decorator factory to require any of the specified permissions.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")

            if not has_any_permission(current_user, permissions):
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: requires one of {permissions}"
                )

            return func(*args, **kwargs)
        return wrapper
    return decorator


# ==================== HELPER FOR CHECKING TICKET OWNERSHIP ====================

def can_access_ticket(user: models.User, ticket: models.Ticket) -> bool:
    """
    Check if a user can access a specific ticket.

    Args:
        user: The User model instance
        ticket: The Ticket model instance

    Returns:
        True if user can access the ticket

    Rules:
        - superadmin/admin: can access all tickets
        - tech with tickets:view: can access all tickets in their entity
        - user: can only access tickets they created
    """
    # Admins can access everything
    if user.role in ("superadmin", "admin"):
        return True

    # Tech users with view permission can access entity tickets
    if user.role == "tech" and can_access_tickets(user):
        # Entity-scoped access
        if user.entity_id and ticket.entity_id:
            return ticket.entity_id == user.entity_id
        return True

    # Regular users can only access their own tickets
    return ticket.requester_id == user.id


def can_modify_ticket(user: models.User, ticket: models.Ticket, action: str = "edit") -> bool:
    """
    Check if a user can modify a specific ticket.

    Args:
        user: The User model instance
        ticket: The Ticket model instance
        action: The action to perform (edit, assign, delete, resolve)

    Returns:
        True if user can modify the ticket
    """
    # First check if user can access the ticket
    if not can_access_ticket(user, ticket):
        return False

    # Then check if user has the required permission
    if user.role in ("superadmin", "admin"):
        return True

    if user.role == "tech":
        return can_manage_ticket(user, action)

    # Regular users can only edit their own tickets with limited fields
    if user.role == "user" and action == "edit":
        return ticket.requester_id == user.id

    return False
