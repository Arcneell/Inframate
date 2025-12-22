from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import INET, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user") # admin, user
    permissions = Column(JSON, default={}) # ex: {"ipam": true, "scripts": false}

class Server(Base):
    __tablename__ = "servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    ip_address = Column(String, nullable=False)
    os_type = Column(String, nullable=False) # linux, windows
    connection_type = Column(String, default="ssh") # ssh, winrm
    username = Column(String, nullable=False)
    password = Column(String, nullable=True) 
    port = Column(Integer, default=22)

class Subnet(Base):
    __tablename__ = "subnets"

    id = Column(Integer, primary_key=True, index=True)
    cidr = Column(INET, unique=True, nullable=False)
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    
    ips = relationship("IPAddress", back_populates="subnet", cascade="all, delete-orphan")

class IPAddress(Base):
    __tablename__ = "ip_addresses"

    id = Column(Integer, primary_key=True, index=True)
    address = Column(INET, unique=True, nullable=False)
    status = Column(String, default="available")
    hostname = Column(String, nullable=True)
    mac_address = Column(String, nullable=True)
    last_scanned_at = Column(DateTime, nullable=True)
    subnet_id = Column(Integer, ForeignKey("subnets.id"))

    subnet = relationship("Subnet", back_populates="ips")

class Script(Base):
    __tablename__ = "scripts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    filename = Column(String, nullable=False)
    script_type = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    executions = relationship("ScriptExecution", back_populates="script")

class ScriptExecution(Base):
    __tablename__ = "script_executions"

    id = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id", ondelete="SET NULL"), nullable=True)
    server_id = Column(Integer, ForeignKey("servers.id"), nullable=True)
    task_id = Column(String, nullable=True)
    status = Column(String, default="pending")
    stdout = Column(Text, nullable=True)
    stderr = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    script = relationship("Script", back_populates="executions")
    server = relationship("Server")