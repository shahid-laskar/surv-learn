"""
app/models/user.py
Expanded User model with org/customer FK, fine-grained user_type,
account-security columns, and relationships to all new RBAC/session tables.
The legacy `role` VARCHAR column is kept for backward-compatibility
during the migration period; new code should use the `user_roles`
relationship instead.
"""

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey,
    Integer, String,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class User(Base):
    __tablename__ = "survapp_user"

    # ── Core identity ──────────────────────────────────────────────
    id            = Column(BigInteger, primary_key=True, index=True)
    username      = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email         = Column(String(255), nullable=True)
    mobile        = Column(String(20),  nullable=True)
    first_name    = Column(String(100), nullable=True)
    last_name     = Column(String(100), nullable=True)
    full_name     = Column(String(200), nullable=True)  # legacy — kept for compat

    # ── Classification ─────────────────────────────────────────────
    user_type = Column(String(30), nullable=False, default="EMPLOYEE")
    # EMPLOYEE | CUSTOMER | PARTNER | SYSTEM

    # ── Legacy flat role (Phase 7 compat) — superseded by survapp_user_role
    role      = Column(String(50), default="operator", nullable=False)

    # ── Org / Customer linkage ────────────────────────────────────
    organization_id = Column(BigInteger, ForeignKey("organization.id"), nullable=True)
    customer_id     = Column(BigInteger, ForeignKey("customer.id"),     nullable=True)
    circle_id       = Column(BigInteger, ForeignKey("circle_master.id"), nullable=True)
    ba_id           = Column(BigInteger, ForeignKey("ba_master.id"),    nullable=True)

    # ── Account security ──────────────────────────────────────────
    is_active            = Column(Boolean,  default=True,  nullable=False)
    is_locked            = Column(Boolean,  default=False, nullable=False)
    failed_login_count   = Column(Integer,  default=0,     nullable=False)
    last_login           = Column(DateTime(timezone=True), nullable=True)
    last_password_change = Column(DateTime(timezone=True), nullable=True)

    # ── Audit ─────────────────────────────────────────────────────
    created_by = Column(BigInteger, nullable=True)
    updated_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=True)

    # ── Relationships ─────────────────────────────────────────────
    organization = relationship("Organization", back_populates="users",   lazy="select")
    customer     = relationship("Customer",     back_populates="users",   lazy="select")
    circle       = relationship("CircleMaster", back_populates="users",   lazy="select")
    ba           = relationship("BAMaster",     back_populates="users",   lazy="select")
    user_roles   = relationship("UserRole",     back_populates="user",    lazy="select",
                                cascade="all, delete-orphan")
    sessions          = relationship("UserSession",      back_populates="user", lazy="select",
                                     cascade="all, delete-orphan")
    device_tokens     = relationship("DeviceToken",      back_populates="user", lazy="select",
                                     cascade="all, delete-orphan")
    notifications     = relationship("Notification",     back_populates="user", lazy="select")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user", lazy="select",
                                         cascade="all, delete-orphan")
