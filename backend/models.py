from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, Date, Numeric, UniqueConstraint, Index, event, text
from sqlalchemy.dialects.postgresql import INET, JSON, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator
from datetime import datetime, timezone
from backend.core.database import Base


def utc_now():
    """Get current UTC time with timezone awareness."""
    return datetime.now(timezone.utc)


# ==================== ENCRYPTED STRING TYPE DECORATOR ====================

class EncryptedString(TypeDecorator):
    """
    SQLAlchemy TypeDecorator for automatic Fernet encryption/decryption.

    Encrypts values before storing in DB, decrypts when reading.
    Fernet tokens start with 'gAAAA' prefix for detection.

    Usage:
        totp_secret = Column(EncryptedString, nullable=True)
        remote_password = Column(EncryptedString, nullable=True)
    """
    impl = String
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Encrypt value before storing in database."""
        if not value:
            return value
        # Already encrypted - skip
        if isinstance(value, str) and value.startswith('gAAAA'):
            return value
        # Import here to avoid circular imports
        from backend.core.security import encrypt_value
        return encrypt_value(value)

    def process_result_value(self, value, dialect):
        """Decrypt value when reading from database."""
        if not value:
            return value
        # Only decrypt if it looks encrypted
        if isinstance(value, str) and value.startswith('gAAAA'):
            from backend.core.security import decrypt_value
            import logging
            try:
                return decrypt_value(value)
            except Exception as e:
                # Log decryption failure for security audit
                logger = logging.getLogger(__name__)
                logger.error(
                    f"Failed to decrypt sensitive field: {type(e).__name__} - {e}. "
                    "This may indicate the ENCRYPTION_KEY has changed. "
                    "Use rotate_encryption_key_task to migrate encrypted data to a new key."
                )
                # Return a fallback value instead of raising an exception
                # This prevents blocking entire list displays when one record has encryption issues
                # The error is logged above for security audit purposes
                return "[ERREUR DECHIFFREMENT]"
        return value


# ==================== MULTI-ENTITY MODEL ====================

class Entity(Base):
    """
    Entity for multi-tenant isolation.
    All major objects belong to an entity for logical separation.
    """
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    users = relationship("User", back_populates="entity")
    subnets = relationship("Subnet", back_populates="entity")
    equipment = relationship("Equipment", back_populates="entity")
    locations = relationship("Location", back_populates="entity")
    racks = relationship("Rack", back_populates="entity")
    contracts = relationship("Contract", back_populates="entity")
    software = relationship("Software", back_populates="entity")

class User(Base):
    """
    User model with hierarchical role system:
    - user: Access to helpdesk only (create/view own tickets)
    - tech: Granular permissions (ipam, inventory, dcim, contracts, software, topology, knowledge)
    - admin: All tech permissions + user management (no system settings)
    - superadmin: Full access including system settings and scripts
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, nullable=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")  # user, tech, admin, superadmin
    avatar = Column(String, nullable=True)  # Profile picture filename
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    # MFA/TOTP fields
    mfa_enabled = Column(Boolean, default=False)
    totp_secret = Column(EncryptedString, nullable=True)  # Encrypted TOTP secret (auto-encrypted via TypeDecorator)

    # Granular permissions for tech and admin roles (JSON array of permission strings)
    # Available: ipam, inventory, dcim, contracts, software, topology, knowledge, network_ports, attachments
    permissions = Column(JSONB, default=[])  # JSONB for GIN index support

    entity = relationship("Entity", back_populates="users")
    refresh_tokens = relationship("UserToken", back_populates="user", cascade="all, delete-orphan")

    # GIN index for JSON permissions column (fast permission-based queries)
    __table_args__ = (
        Index('ix_users_permissions_gin', permissions, postgresql_using='gin'),
    )


class UserToken(Base):
    """
    Stores refresh tokens for secure token renewal.
    Each refresh token is tied to a user and has an expiration.
    """
    __tablename__ = "user_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String, unique=True, nullable=False, index=True)  # SHA256 hash of the token
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    revoked = Column(Boolean, default=False)
    device_info = Column(String, nullable=True)  # User agent or device identifier
    ip_address = Column(String, nullable=True)  # IP address of the client

    user = relationship("User", back_populates="refresh_tokens")


class Subnet(Base):
    __tablename__ = "subnets"

    id = Column(Integer, primary_key=True, index=True)
    cidr = Column(INET, unique=True, nullable=False)
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True)

    entity = relationship("Entity", back_populates="subnets")
    ips = relationship("IPAddress", back_populates="subnet", cascade="all, delete-orphan")

class IPAddress(Base):
    __tablename__ = "ip_addresses"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(INET, unique=True, nullable=False)
    status = Column(String, default="available", index=True)  # Index for IPAM filtering
    hostname = Column(String, nullable=True, index=True)  # Index for hostname search
    mac_address = Column(String, nullable=True)
    last_scanned_at = Column(DateTime, nullable=True)
    subnet_id = Column(Integer, ForeignKey("subnets.id"), index=True)  # Index for subnet filtering
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="SET NULL"), nullable=True, index=True)

    subnet = relationship("Subnet", back_populates="ips")
    equipment = relationship("Equipment", back_populates="ip_addresses")

class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    filename = Column(String, nullable=False)
    script_type = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    executions = relationship("ScriptExecution", back_populates="script")

class ScriptExecution(Base):
    __tablename__ = "script_executions"

    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id", ondelete="SET NULL"), nullable=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="SET NULL"), nullable=True)
    task_id = Column(String, nullable=True)
    status = Column(String, default="pending")
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    started_at = Column(DateTime, default=utc_now)
    completed_at = Column(DateTime, nullable=True)

    script = relationship("Script", back_populates="executions")
    equipment = relationship("Equipment")


# ==================== INVENTORY MODELS ====================

class Manufacturer(Base):
    """Hardware manufacturers (Dell, HP, Cisco, etc.)"""
    __tablename__ = "manufacturers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    website = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    models = relationship("EquipmentModel", back_populates="manufacturer")


class EquipmentType(Base):
    """Equipment categories (Server, Switch, Router, PC, etc.)"""
    __tablename__ = "equipment_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    icon = Column(String, default="pi-box")  # PrimeIcons class
    supports_remote_execution = Column(Boolean, default=False)  # Enable SSH/WinRM fields
    hierarchy_level = Column(Integer, default=3)  # 0=top (router), 1=firewall, 2=switch, 3=server, 4=storage

    models = relationship("EquipmentModel", back_populates="equipment_type")


class EquipmentModel(Base):
    """Product models/SKUs (PowerEdge R740, Catalyst 9300, etc.)"""
    __tablename__ = "equipment_models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    manufacturer_id = Column(Integer, ForeignKey("manufacturers.id"), nullable=False)
    equipment_type_id = Column(Integer, ForeignKey("equipment_types.id"), nullable=False)
    specs = Column(JSONB, nullable=True)  # {"cpu": "...", "ram": "...", etc.} - JSONB for GIN index

    manufacturer = relationship("Manufacturer", back_populates="models")
    equipment_type = relationship("EquipmentType", back_populates="models")
    equipment = relationship("Equipment", back_populates="model")

    # GIN index for JSON specs column (fast hardware spec searches)
    __table_args__ = (
        Index('ix_equipment_models_specs_gin', specs, postgresql_using='gin'),
    )


class Location(Base):
    """Physical locations (Site > Building > Room)"""
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    site = Column(String, nullable=False)
    building = Column(String, nullable=True)
    room = Column(String, nullable=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True)

    entity = relationship("Entity", back_populates="locations")
    equipment = relationship("Equipment", back_populates="location")
    racks = relationship("Rack", back_populates="location")


class Supplier(Base):
    """Equipment suppliers/vendors"""
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    contact_email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

    equipment = relationship("Equipment", back_populates="supplier")
    contracts = relationship("Contract", back_populates="supplier")


class Equipment(Base):
    """Main equipment/asset inventory with financial and DCIM fields"""
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    serial_number = Column(String, unique=True, nullable=True, index=True)
    asset_tag = Column(String, unique=True, nullable=True, index=True)
    status = Column(String, default="in_service", index=True)  # in_service, in_stock, retired, maintenance
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Financial & Lifecycle fields
    purchase_date = Column(DateTime, nullable=True)
    purchase_price = Column(Numeric(12, 2), nullable=True)
    warranty_months = Column(Integer, nullable=True)  # Duration in months
    warranty_expiry = Column(DateTime, nullable=True)
    end_of_support = Column(DateTime, nullable=True)

    # DCIM - Rack placement fields
    rack_id = Column(Integer, ForeignKey("racks.id"), nullable=True)
    position_u = Column(Integer, nullable=True)  # Starting U position (1-42)
    height_u = Column(Integer, default=1)  # Height in U (1, 2, 4, etc.)

    # Power tracking
    power_consumption_watts = Column(Integer, nullable=True)
    pdu_id = Column(Integer, ForeignKey("pdus.id"), nullable=True)
    pdu_port = Column(String, nullable=True)
    redundant_pdu_id = Column(Integer, ForeignKey("pdus.id"), nullable=True)
    redundant_pdu_port = Column(String, nullable=True)

    # Foreign keys
    model_id = Column(Integer, ForeignKey("equipment_models.id"), nullable=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True)

    # Remote execution fields (optional, used when equipment type supports it)
    remote_ip = Column(String, nullable=True)
    os_type = Column(String, nullable=True)  # linux, windows
    connection_type = Column(String, nullable=True)  # ssh, winrm
    remote_username = Column(String, nullable=True)
    remote_password = Column(EncryptedString, nullable=True)
    remote_port = Column(Integer, nullable=True)

    # Relationships
    model = relationship("EquipmentModel", back_populates="equipment")
    location = relationship("Location", back_populates="equipment")
    supplier = relationship("Supplier", back_populates="equipment")
    entity = relationship("Entity", back_populates="equipment")
    ip_addresses = relationship("IPAddress", back_populates="equipment")
    rack = relationship("Rack", back_populates="equipment", foreign_keys=[rack_id])
    pdu = relationship("PDU", back_populates="equipment", foreign_keys=[pdu_id])
    redundant_pdu = relationship("PDU", foreign_keys=[redundant_pdu_id])
    network_ports = relationship("NetworkPort", back_populates="equipment", cascade="all, delete-orphan")
    software_installations = relationship("SoftwareInstallation", back_populates="equipment", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="equipment", cascade="all, delete-orphan")
    contracts = relationship("ContractEquipment", back_populates="equipment")


# ==================== DCIM MODELS ====================

class Rack(Base):
    """
    Server rack for DCIM placement.
    Standard racks have 42U capacity.
    """
    __tablename__ = "racks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True)
    height_u = Column(Integer, default=42)  # Total U capacity
    width_mm = Column(Integer, default=600)  # Standard 600mm or 800mm
    depth_mm = Column(Integer, default=1000)
    max_power_kw = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    location = relationship("Location", back_populates="racks")
    entity = relationship("Entity", back_populates="racks")
    equipment = relationship("Equipment", back_populates="rack", foreign_keys="Equipment.rack_id")
    pdus = relationship("PDU", back_populates="rack")


class PDU(Base):
    """
    Power Distribution Unit for rack power management.
    """
    __tablename__ = "pdus"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    rack_id = Column(Integer, ForeignKey("racks.id"), nullable=True)
    pdu_type = Column(String, default="basic")  # basic, metered, switched, smart
    total_ports = Column(Integer, default=8)
    max_amps = Column(Float, nullable=True)
    voltage = Column(Integer, default=230)  # 230V or 120V
    phase = Column(String, default="single")  # single, three
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    rack = relationship("Rack", back_populates="pdus")
    equipment = relationship("Equipment", back_populates="pdu", foreign_keys="Equipment.pdu_id")


# ==================== CONTRACT MODELS ====================

class Contract(Base):
    """
    Service contracts (maintenance, insurance, leasing).
    """
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    contract_type = Column(String, nullable=False, index=True)  # maintenance, insurance, leasing, support
    contract_number = Column(String, unique=True, nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False, index=True)  # Indexed for expiration alerts
    annual_cost = Column(Numeric(12, 2), nullable=True)
    renewal_type = Column(String, default="manual")  # auto, manual, none
    renewal_notice_days = Column(Integer, default=30)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    supplier = relationship("Supplier", back_populates="contracts")
    entity = relationship("Entity", back_populates="contracts")
    equipment_links = relationship("ContractEquipment", back_populates="contract", cascade="all, delete-orphan")


class ContractEquipment(Base):
    """
    Many-to-many relationship between contracts and equipment.
    """
    __tablename__ = "contract_equipment"

    id = Column(Integer, primary_key=True, index=True)
    contract_id = Column(Integer, ForeignKey("contracts.id"), nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    notes = Column(Text, nullable=True)

    contract = relationship("Contract", back_populates="equipment_links")
    equipment = relationship("Equipment", back_populates="contracts")

    __table_args__ = (
        UniqueConstraint('contract_id', 'equipment_id', name='uq_contract_equipment'),
    )


# ==================== SOFTWARE & LICENSE MODELS ====================

class Software(Base):
    """
    Software catalog for license management.
    """
    __tablename__ = "software"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    publisher = Column(String, nullable=True)
    version = Column(String, nullable=True)
    category = Column(String, nullable=True)  # os, database, middleware, application, utility
    entity_id = Column(Integer, ForeignKey("entities.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    entity = relationship("Entity", back_populates="software")
    licenses = relationship("SoftwareLicense", back_populates="software", cascade="all, delete-orphan")
    installations = relationship("SoftwareInstallation", back_populates="software", cascade="all, delete-orphan")


class SoftwareLicense(Base):
    """
    Software license with quota management.
    """
    __tablename__ = "software_licenses"

    id = Column(Integer, primary_key=True, index=True)
    software_id = Column(Integer, ForeignKey("software.id"), nullable=False)
    license_key = Column(String, nullable=True)  # Encrypted
    license_type = Column(String, default="perpetual")  # perpetual, subscription, oem, volume
    quantity = Column(Integer, default=1)  # Number of allowed installations
    purchase_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)
    purchase_price = Column(Numeric(12, 2), nullable=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    software = relationship("Software", back_populates="licenses")
    supplier = relationship("Supplier")


class SoftwareInstallation(Base):
    """
    Tracks software installations on equipment.
    """
    __tablename__ = "software_installations"

    id = Column(Integer, primary_key=True, index=True)
    software_id = Column(Integer, ForeignKey("software.id"), nullable=False)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    installed_version = Column(String, nullable=True)
    installation_date = Column(DateTime, default=utc_now)
    discovered_at = Column(DateTime, nullable=True)  # For auto-discovered software
    notes = Column(Text, nullable=True)

    software = relationship("Software", back_populates="installations")
    equipment = relationship("Equipment", back_populates="software_installations")

    __table_args__ = (
        UniqueConstraint('software_id', 'equipment_id', name='uq_software_installation'),
    )


# ==================== NETWORK PORT & PATCHING MODELS ====================

class NetworkPort(Base):
    """
    Network ports on equipment for physical connectivity mapping.
    """
    __tablename__ = "network_ports"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    name = Column(String, nullable=False)  # e.g., "eth0", "GigabitEthernet0/1"
    port_type = Column(String, default="ethernet")  # ethernet, fiber, console, management
    speed = Column(String, nullable=True)  # 1G, 10G, 25G, 40G, 100G
    mac_address = Column(String, nullable=True)
    connected_to_id = Column(Integer, ForeignKey("network_ports.id"), nullable=True)
    notes = Column(Text, nullable=True)

    equipment = relationship("Equipment", back_populates="network_ports")
    connected_to = relationship("NetworkPort", remote_side=[id], foreign_keys=[connected_to_id])


# ==================== DOCUMENT ATTACHMENT MODEL ====================

class Attachment(Base):
    """
    File attachments for equipment (invoices, diagrams, etc.).
    """
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(Integer, ForeignKey("equipment.id"), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_type = Column(String, nullable=True)  # pdf, png, jpg, doc
    file_size = Column(Integer, nullable=True)  # Size in bytes
    category = Column(String, nullable=True)  # invoice, diagram, manual, photo, other
    description = Column(Text, nullable=True)
    uploaded_by = Column(String, nullable=True)
    uploaded_at = Column(DateTime, default=utc_now)

    equipment = relationship("Equipment", back_populates="attachments")


# ==================== AUDIT LOG MODEL ====================

class AuditLog(Base):
    """
    System audit log for tracking critical operations.
    Logs all create, update, and delete operations on sensitive resources.
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=utc_now, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    username = Column(String, nullable=False)  # Denormalized for historical accuracy
    action = Column(String, nullable=False, index=True)  # CREATE, UPDATE, DELETE, LOGIN, LOGOUT
    resource_type = Column(String, nullable=False, index=True)  # equipment, subnet, user, etc.
    resource_id = Column(String, nullable=True)  # ID of the affected resource
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    ip_address = Column(String, nullable=True)  # Client IP address
    changes = Column(JSONB, nullable=True)  # {"field": {"old": "value", "new": "value"}} - JSONB for GIN index
    extra_data = Column(JSONB, nullable=True)  # Additional context - JSONB for GIN index

    # Note: No relationship to User to preserve logs even after user deletion

    # GIN indexes for JSON columns (fast audit log searches)
    __table_args__ = (
        Index('ix_audit_logs_changes_gin', changes, postgresql_using='gin'),
        Index('ix_audit_logs_extra_data_gin', extra_data, postgresql_using='gin'),
    )


# ==================== HELPDESK TICKET MODELS ====================

class Ticket(Base):
    """
    Helpdesk ticket for incident/request management.
    Supports full ITIL-aligned workflow with SLA tracking.
    """
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String, unique=True, nullable=False, index=True)  # AUTO: TKT-YYYYMMDD-XXXX
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)

    # Classification
    ticket_type = Column(String, default="incident")  # incident, request, problem, change
    category = Column(String, nullable=True)  # hardware, software, network, access, other
    subcategory = Column(String, nullable=True)

    # Status & Priority
    status = Column(String, default="new", index=True)  # new, open, pending, resolved, closed
    priority = Column(String, default="medium", index=True)  # critical, high, medium, low
    impact = Column(String, default="medium")  # high, medium, low
    urgency = Column(String, default="medium")  # high, medium, low

    # Assignment
    requester_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assigned_group = Column(String, nullable=True)  # support_l1, support_l2, network, systems

    # Related entities
    equipment_id = Column(Integer, ForeignKey("equipment.id", ondelete="SET NULL"), nullable=True)
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)

    # SLA Tracking
    sla_due_date = Column(DateTime, nullable=True)
    first_response_at = Column(DateTime, nullable=True)
    first_response_due = Column(DateTime, nullable=True)
    resolution_due = Column(DateTime, nullable=True)
    sla_breached = Column(Boolean, default=False)

    # Resolution
    resolution = Column(Text, nullable=True)
    resolution_code = Column(String, nullable=True)  # fixed, workaround, cannot_reproduce, duplicate, user_error

    # Timestamps
    created_at = Column(DateTime, default=utc_now, index=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Customer Satisfaction (CSAT) - collected after ticket closure
    rating = Column(Integer, nullable=True)  # 1-5 star rating
    rating_comment = Column(Text, nullable=True)  # Optional feedback text
    rating_submitted_at = Column(DateTime, nullable=True)  # When the rating was submitted

    # Email integration - for threading inbound emails to this ticket
    email_message_id = Column(String, nullable=True, index=True)  # Original email Message-ID that created this ticket
    sla_warning_sent = Column(Boolean, default=False)  # Track if SLA warning email was sent

    # Relationships
    requester = relationship("User", foreign_keys=[requester_id], backref="requested_tickets")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], backref="assigned_tickets")
    equipment = relationship("Equipment", backref="tickets")
    entity = relationship("Entity", backref="tickets")
    comments = relationship("TicketComment", back_populates="ticket", cascade="all, delete-orphan")
    history = relationship("TicketHistory", back_populates="ticket", cascade="all, delete-orphan")
    attachments = relationship("TicketAttachment", back_populates="ticket", cascade="all, delete-orphan")
    time_entries = relationship("TicketTimeEntry", back_populates="ticket", cascade="all, delete-orphan")
    # Relations where this ticket is the source
    related_from = relationship("TicketRelation", foreign_keys="TicketRelation.source_ticket_id", back_populates="source_ticket", cascade="all, delete-orphan")
    # Relations where this ticket is the target
    related_to = relationship("TicketRelation", foreign_keys="TicketRelation.target_ticket_id", back_populates="target_ticket", cascade="all, delete-orphan")


class TicketComment(Base):
    """
    Comments/notes on tickets for communication tracking.
    """
    __tablename__ = "ticket_comments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # Internal note vs public reply
    is_resolution = Column(Boolean, default=False)  # Marked as resolution
    created_at = Column(DateTime, default=utc_now)

    # Email integration
    email_message_id = Column(String, nullable=True, index=True)  # Email Message-ID if created from inbound email
    is_email_reply = Column(Boolean, default=False)  # True if this comment was created from an email reply

    ticket = relationship("Ticket", back_populates="comments")
    user = relationship("User", backref="ticket_comments")


class TicketHistory(Base):
    """
    Audit trail for ticket changes.
    """
    __tablename__ = "ticket_history"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String, nullable=False)  # created, updated, assigned, status_changed, commented, resolved, closed
    field_name = Column(String, nullable=True)  # Which field changed
    old_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    ticket = relationship("Ticket", back_populates="history")
    user = relationship("User", backref="ticket_history")


class TicketAttachment(Base):
    """
    File attachments for tickets.
    """
    __tablename__ = "ticket_attachments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_type = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    uploaded_at = Column(DateTime, default=utc_now)

    ticket = relationship("Ticket", back_populates="attachments")
    uploaded_by = relationship("User", backref="ticket_attachments")


class TicketRelation(Base):
    """
    Relations between tickets for linking related issues.

    Relation Types:
        - duplicate_of: This ticket is a duplicate of the target ticket
        - child_of: This ticket is a sub-task of the target ticket (parent-child)
        - blocked_by: This ticket is blocked by the target ticket
        - related_to: General relation between tickets

    The source_ticket is the ticket that has the relation TO the target_ticket.
    Example: Ticket A is a "duplicate_of" Ticket B
        - source_ticket_id = A.id
        - target_ticket_id = B.id
        - relation_type = "duplicate_of"
    """
    __tablename__ = "ticket_relations"

    id = Column(Integer, primary_key=True, index=True)
    source_ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    target_ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    relation_type = Column(String, nullable=False, index=True)  # duplicate_of, child_of, blocked_by, related_to
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    notes = Column(Text, nullable=True)  # Optional notes about the relation

    # Relationships
    source_ticket = relationship("Ticket", foreign_keys=[source_ticket_id], back_populates="related_from")
    target_ticket = relationship("Ticket", foreign_keys=[target_ticket_id], back_populates="related_to")
    created_by = relationship("User", backref="ticket_relations_created")

    __table_args__ = (
        # Prevent duplicate relations (same source, target, and type)
        UniqueConstraint('source_ticket_id', 'target_ticket_id', 'relation_type', name='uq_ticket_relation'),
        # Index for efficient lookup of all relations for a ticket
        Index('ix_ticket_relations_source_target', source_ticket_id, target_ticket_id),
    )


class TicketTimeEntry(Base):
    """
    Time tracking entries for tickets.

    Allows technicians to log time spent working on tickets.
    Used for reporting, billing, and workload analysis.
    """
    __tablename__ = "ticket_time_entries"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    minutes = Column(Integer, nullable=False)  # Time spent in minutes
    description = Column(Text, nullable=True)  # What was done during this time
    work_date = Column(DateTime, default=utc_now)  # When the work was performed
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Time entry type for categorization
    entry_type = Column(String, default="work")  # work, research, communication, testing, travel

    # Billable tracking
    is_billable = Column(Boolean, default=True)
    hourly_rate = Column(Numeric(10, 2), nullable=True)  # Optional rate for billing calculations

    # Relationships
    ticket = relationship("Ticket", back_populates="time_entries")
    user = relationship("User", backref="ticket_time_entries")

    __table_args__ = (
        # Index for efficient time reports by user
        Index('ix_ticket_time_entries_user_date', user_id, work_date),
    )


# ==================== TICKET NUMBER GENERATION HOOK ====================

@event.listens_for(Ticket, 'before_insert')
def generate_ticket_number_on_insert(mapper, connection, target):
    """
    Automatically generate unique ticket_number before inserting Ticket.

    Format: TKT-YYYYMMDD-XXXX where XXXX is a sequential number per day.
    Uses PostgreSQL advisory lock + SELECT FOR UPDATE to ensure atomicity
    under high concurrency and prevent race conditions.
    """
    if target.ticket_number:
        return  # Already set, skip

    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    pattern = f"TKT-{today}-%"

    # Use advisory lock to prevent race conditions under high concurrency
    # Lock key is based on the date to minimize contention across days
    lock_key = int(today)  # Convert date string to integer for advisory lock

    # Acquire advisory lock, get max ticket number, and release in one transaction
    # CHECK DIALECT: Only use advisory locks on PostgreSQL
    if connection.dialect.name == 'postgresql':
        result = connection.execute(
            text("""
                SELECT pg_advisory_xact_lock(:lock_key);
                SELECT COALESCE(
                    MAX(
                        CAST(
                            SUBSTRING(ticket_number FROM 'TKT-[0-9]{8}-([0-9]+)') AS INTEGER
                        )
                    ),
                    0
                ) + 1
                FROM tickets
                WHERE ticket_number LIKE :pattern
            """),
            {"lock_key": lock_key, "pattern": pattern}
        ).scalar()
    else:
        # WARNING: SQLite/other databases do not support advisory locks.
        # This fallback is NOT safe for concurrent ticket creation and may result
        # in duplicate ticket numbers under high load. Use PostgreSQL in production.
        # This fallback exists only for development/testing purposes.
        import logging
        _logger = logging.getLogger(__name__)
        _logger.warning(
            "Generating ticket number without advisory lock. "
            "This is NOT safe for concurrent access. Use PostgreSQL in production."
        )
        result = connection.execute(
            text("""
                SELECT COALESCE(
                    MAX(
                        CAST(
                            SUBSTR(ticket_number, 14) AS INTEGER
                        )
                    ),
                    0
                ) + 1
                FROM tickets
                WHERE ticket_number LIKE :pattern
            """),
            {"pattern": pattern}
        ).scalar()

    target.ticket_number = f"TKT-{today}-{result:04d}"


# ==================== NOTIFICATION MODELS ====================

class Notification(Base):
    """
    In-app notifications for users.
    """
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String, default="info")  # info, warning, error, success, ticket

    # Link to related entity
    link_type = Column(String, nullable=True)  # ticket, equipment, contract, etc.
    link_id = Column(Integer, nullable=True)

    # Status
    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=utc_now, index=True)
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", backref="notifications")


# ==================== KNOWLEDGE BASE MODELS ====================

class KnowledgeCategory(Base):
    """
    Categories for organizing knowledge base articles.
    User-created and manageable from the web interface.
    """
    __tablename__ = "knowledge_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String, default="pi-folder")  # PrimeIcons class
    color = Column(String, default="#0ea5e9")  # Accent color for UI
    is_active = Column(Boolean, default=True, index=True)
    display_order = Column(Integer, default=0)  # For custom sorting
    article_count = Column(Integer, default=0)  # Cached count for performance
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    articles = relationship("KnowledgeArticle", back_populates="category_rel")


class KnowledgeArticle(Base):
    """
    Knowledge base articles for self-service and technician reference.
    """
    __tablename__ = "knowledge_articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    slug = Column(String, unique=True, nullable=False, index=True)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)  # Short description for search results

    # Classification
    category = Column(String, nullable=True, index=True)  # Legacy string category (deprecated)
    category_id = Column(Integer, ForeignKey("knowledge_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    tags = Column(JSONB, default=[])  # ["network", "vpn", "connectivity"] - JSONB for GIN index

    # Visibility
    is_published = Column(Boolean, default=False, index=True)
    is_internal = Column(Boolean, default=False)  # Internal-only (technicians)

    # Authoring
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    last_editor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Metrics
    view_count = Column(Integer, default=0)
    helpful_count = Column(Integer, default=0)
    not_helpful_count = Column(Integer, default=0)

    # Versioning
    version = Column(Integer, default=1)

    # Timestamps
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    published_at = Column(DateTime, nullable=True)

    # Related entities
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)

    author = relationship("User", foreign_keys=[author_id], backref="authored_articles")
    last_editor = relationship("User", foreign_keys=[last_editor_id])
    entity = relationship("Entity", backref="knowledge_articles")
    category_rel = relationship("KnowledgeCategory", back_populates="articles")

    # GIN index for JSON tags column (fast tag-based searches)
    __table_args__ = (
        Index('ix_knowledge_articles_tags_gin', tags, postgresql_using='gin'),
    )


class KnowledgeArticleView(Base):
    """
    Tracks unique article views per user.
    Prevents duplicate view counts when the same user views an article multiple times.
    """
    __tablename__ = "knowledge_article_views"

    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("knowledge_articles.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    viewed_at = Column(DateTime, default=utc_now)

    # Unique constraint: one view record per user per article
    __table_args__ = (
        Index('ix_knowledge_article_views_article_user', 'article_id', 'user_id', unique=True),
    )

    article = relationship("KnowledgeArticle", backref="views")
    user = relationship("User", backref="article_views")


# ==================== SLA CONFIGURATION MODELS ====================

class SLAPolicy(Base):
    """
    SLA policy definitions for automatic SLA calculation.
    """
    __tablename__ = "sla_policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Priority-based response times (in minutes)
    critical_response_time = Column(Integer, default=15)  # 15 min
    critical_resolution_time = Column(Integer, default=240)  # 4 hours
    high_response_time = Column(Integer, default=60)  # 1 hour
    high_resolution_time = Column(Integer, default=480)  # 8 hours
    medium_response_time = Column(Integer, default=240)  # 4 hours
    medium_resolution_time = Column(Integer, default=1440)  # 24 hours
    low_response_time = Column(Integer, default=480)  # 8 hours
    low_resolution_time = Column(Integer, default=2880)  # 48 hours

    # Business hours
    business_hours_only = Column(Boolean, default=True)
    business_start = Column(String, default="09:00")  # HH:MM
    business_end = Column(String, default="18:00")
    business_days = Column(JSONB, default=[1, 2, 3, 4, 5])  # Monday=1 to Sunday=7 - JSONB for GIN index

    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    entity = relationship("Entity", backref="sla_policies")

    # GIN index for JSON business_days column
    __table_args__ = (
        Index('ix_sla_policies_business_days_gin', business_days, postgresql_using='gin'),
    )


# ==================== TICKET TEMPLATE MODELS ====================

class TicketTemplate(Base):
    """
    Pre-defined ticket templates for quick ticket creation.
    Allows creating commonly used ticket types like "Hardware Request", "Software Installation", etc.
    """
    __tablename__ = "ticket_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Template fields (pre-filled values)
    title_template = Column(String, nullable=False)  # Can contain placeholders like {user}, {date}
    description_template = Column(Text, nullable=True)
    ticket_type = Column(String, default="request")  # incident, request, problem, change
    category = Column(String, nullable=True)
    subcategory = Column(String, nullable=True)
    priority = Column(String, default="medium")  # critical, high, medium, low
    assigned_group = Column(String, nullable=True)  # Default assignment group

    # Visibility
    is_active = Column(Boolean, default=True, index=True)
    is_public = Column(Boolean, default=True)  # Visible to all users or just tech/admin

    # Metadata
    icon = Column(String, default="pi-ticket")  # PrimeIcons class
    color = Column(String, default="#0ea5e9")  # Accent color for UI
    usage_count = Column(Integer, default=0)  # Track template usage

    # Ownership
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    entity = relationship("Entity", backref="ticket_templates")
    created_by = relationship("User", backref="created_templates")


# ==================== WEBHOOKS MODELS ====================

class Webhook(Base):
    """
    Webhook configuration for external integrations.
    Supports event-based notifications to external systems.
    """
    __tablename__ = "webhooks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)  # Target URL for webhook delivery
    secret = Column(String, nullable=True)  # Shared secret for HMAC signature

    # Event subscriptions
    events = Column(JSONB, default=[])  # List of events: ticket.created, etc. - JSONB for GIN index

    # Configuration
    is_active = Column(Boolean, default=True)
    content_type = Column(String, default="application/json")  # application/json or application/x-www-form-urlencoded
    retry_count = Column(Integer, default=3)  # Number of retries on failure
    timeout_seconds = Column(Integer, default=30)

    # Stats
    last_triggered = Column(DateTime, nullable=True)
    last_status_code = Column(Integer, nullable=True)
    failure_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)

    # Ownership
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    entity = relationship("Entity", backref="webhooks")
    created_by = relationship("User", backref="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")

    # GIN index for JSON events column (fast event-based queries)
    __table_args__ = (
        Index('ix_webhooks_events_gin', events, postgresql_using='gin'),
    )


class WebhookDelivery(Base):
    """
    Log of webhook delivery attempts for debugging and monitoring.
    """
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, index=True)
    webhook_id = Column(Integer, ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False)

    # Delivery details
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)

    # Response
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    response_time_ms = Column(Integer, nullable=True)

    # Status
    success = Column(Boolean, default=False)
    error_message = Column(Text, nullable=True)
    attempt_count = Column(Integer, default=1)

    created_at = Column(DateTime, default=utc_now, index=True)

    webhook = relationship("Webhook", back_populates="deliveries")


# ==================== EMAIL INTEGRATION MODELS ====================

class EmailConfiguration(Base):
    """
    Email configuration for inbound/outbound email integration.
    Supports SMTP/IMAP and Microsoft 365 (Graph API) providers.
    Entity-scoped for multi-tenant support.
    """
    __tablename__ = "email_configurations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    entity_id = Column(Integer, ForeignKey("entities.id", ondelete="SET NULL"), nullable=True)
    provider_type = Column(String, nullable=False)  # smtp_imap, microsoft_365
    is_active = Column(Boolean, default=True)
    is_inbound_enabled = Column(Boolean, default=False)
    is_outbound_enabled = Column(Boolean, default=True)

    # SMTP settings (outbound)
    smtp_host = Column(String, nullable=True)
    smtp_port = Column(Integer, default=587)
    smtp_username = Column(String, nullable=True)
    smtp_password = Column(EncryptedString, nullable=True)
    smtp_use_tls = Column(Boolean, default=True)

    # IMAP settings (inbound)
    imap_host = Column(String, nullable=True)
    imap_port = Column(Integer, default=993)
    imap_username = Column(String, nullable=True)
    imap_password = Column(EncryptedString, nullable=True)
    imap_use_ssl = Column(Boolean, default=True)
    imap_folder = Column(String, default="INBOX")

    # Microsoft 365 settings
    m365_tenant_id = Column(String, nullable=True)
    m365_client_id = Column(String, nullable=True)
    m365_client_secret = Column(EncryptedString, nullable=True)
    m365_user_email = Column(String, nullable=True)  # Service account email with access to shared mailboxes
    m365_mailbox = Column(String, nullable=True)  # Shared mailbox email address
    m365_folder_id = Column(String, nullable=True)  # Folder ID to monitor for inbound emails

    # Common settings
    from_email = Column(String, nullable=True)
    from_name = Column(String, default="Inframate")
    reply_to_email = Column(String, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    entity = relationship("Entity", backref="email_configurations")
    sent_emails = relationship("SentEmail", back_populates="email_config", cascade="all, delete-orphan")
    inbound_emails = relationship("InboundEmail", back_populates="email_config", cascade="all, delete-orphan")


class SentEmail(Base):
    """
    Tracking for outbound email notifications.
    Records all sent emails for delivery status and threading.
    """
    __tablename__ = "sent_emails"

    id = Column(Integer, primary_key=True, index=True)
    email_config_id = Column(Integer, ForeignKey("email_configurations.id", ondelete="SET NULL"), nullable=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="SET NULL"), nullable=True, index=True)
    comment_id = Column(Integer, ForeignKey("ticket_comments.id", ondelete="SET NULL"), nullable=True)

    # RFC 5322 headers for threading
    message_id = Column(String, unique=True, nullable=False, index=True)  # <ticket-123-abc@inframate.local>
    in_reply_to = Column(String, nullable=True)
    references = Column(Text, nullable=True)  # Space-separated list of Message-IDs

    # Recipient info
    recipient_email = Column(String, nullable=False)
    recipient_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Email content
    subject = Column(String, nullable=False)
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)

    # Classification
    email_type = Column(String, nullable=False, index=True)  # ticket_created, ticket_assigned, comment_added, ticket_resolved, sla_warning, sla_breach

    # Status tracking
    status = Column(String, default="pending", index=True)  # pending, sent, failed
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=utc_now)
    sent_at = Column(DateTime, nullable=True)

    # Relationships
    email_config = relationship("EmailConfiguration", back_populates="sent_emails")
    ticket = relationship("Ticket", backref="sent_emails")
    recipient_user = relationship("User", backref="received_emails")


class InboundEmail(Base):
    """
    Log of received emails for ticket creation and comment threading.
    Stores raw email data for audit and debugging.
    """
    __tablename__ = "inbound_emails"

    id = Column(Integer, primary_key=True, index=True)
    email_config_id = Column(Integer, ForeignKey("email_configurations.id", ondelete="SET NULL"), nullable=True)

    # RFC 5322 headers
    message_id = Column(String, unique=True, nullable=False, index=True)
    in_reply_to = Column(String, nullable=True, index=True)
    references = Column(Text, nullable=True)

    # Sender/recipient
    from_email = Column(String, nullable=False, index=True)
    from_name = Column(String, nullable=True)
    to_email = Column(String, nullable=False)

    # Content
    subject = Column(String, nullable=False)
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    raw_headers = Column(JSONB, nullable=True)

    # Processing status
    processing_status = Column(String, default="pending", index=True)  # pending, processed, ignored, error
    processing_result = Column(JSONB, nullable=True)  # {"ticket_id": 123, "comment_id": 456, "action": "created|commented"}
    error_message = Column(Text, nullable=True)

    # Timestamps
    received_at = Column(DateTime, default=utc_now)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    email_config = relationship("EmailConfiguration", back_populates="inbound_emails")


# ==================== SYSTEM SETTINGS MODEL ====================

class SystemSettings(Base):
    """
    System-wide configuration settings.
    Only accessible by superadmin users.
    Stores key-value pairs with categorization.
    """
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)  # JSON-encoded value
    category = Column(String, nullable=False, index=True)  # smtp, general, security, notifications, etc.
    description = Column(Text, nullable=True)
    value_type = Column(String, default="string")  # string, integer, boolean, json, password
    is_sensitive = Column(Boolean, default=False)  # If true, value is encrypted and masked in UI
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    updated_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    updated_by = relationship("User", backref="settings_updates")


# ==================== HELPER FUNCTION ====================

def get_role_hierarchy():
    """Import role hierarchy from security module to avoid circular imports."""
    from backend.core.security import ROLE_HIERARCHY
    return ROLE_HIERARCHY