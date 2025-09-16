from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum


Base = declarative_base()


class StatusEnum(enum.Enum):
    ACTIVE = "Active"
    DISABLED = "Disabled"


class CanonicalIdentity(Base):
    __tablename__ = "canonical_identities"
    
    cid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, nullable=False, unique=True)
    department = Column(String, nullable=False)
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(SQLEnum(StatusEnum), nullable=False, default=StatusEnum.ACTIVE)
    
    # Additional personal info
    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    manager = Column(String)
    location = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    devices = relationship("Device", back_populates="owner", cascade="all, delete-orphan")
    group_memberships = relationship("GroupMembership", back_populates="identity", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="identity", cascade="all, delete-orphan")


class Device(Base):
    __tablename__ = "devices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    last_seen = Column(DateTime(timezone=True), server_default=func.now())
    compliant = Column(Boolean, nullable=False, default=True)
    owner_cid = Column(UUID(as_uuid=True), ForeignKey("canonical_identities.cid"), nullable=False)
    
    # Relationships
    owner = relationship("CanonicalIdentity", back_populates="devices")


class GroupMembership(Base):
    __tablename__ = "group_memberships"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cid = Column(UUID(as_uuid=True), ForeignKey("canonical_identities.cid"), nullable=False)
    group_name = Column(String, nullable=False)
    
    # Relationships
    identity = relationship("CanonicalIdentity", back_populates="group_memberships")


class Account(Base):
    __tablename__ = "accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service = Column(String, nullable=False)
    status = Column(SQLEnum(StatusEnum), nullable=False, default=StatusEnum.ACTIVE)
    user_email = Column(String, nullable=False)
    cid = Column(UUID(as_uuid=True), ForeignKey("canonical_identities.cid"), nullable=False)
    
    # Relationships
    identity = relationship("CanonicalIdentity", back_populates="accounts")
