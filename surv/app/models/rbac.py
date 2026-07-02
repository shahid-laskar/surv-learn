"""
app/models/rbac.py
SQLAlchemy models for roles, permissions, role-permission mapping,
user-role mapping, user-camera overrides, camera groups,
user sessions, device tokens, audit log, notifications,
and password reset tokens.
"""

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey,
    Integer, JSON, String, Text,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


# ─── Role & Permission ────────────────────────────────────────────────────────

class Role(Base):
    __tablename__ = "survapp_role"

    id          = Column(BigInteger, primary_key=True, index=True)
    code        = Column(String(100), nullable=False, unique=True)
    name        = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)

    permissions  = relationship("Permission",    secondary="survapp_role_permission", lazy="select")
    user_roles   = relationship("UserRole",      back_populates="role", lazy="select")


class Permission(Base):
    __tablename__ = "survapp_permission"

    id          = Column(BigInteger, primary_key=True, index=True)
    code        = Column(String(100), nullable=False, unique=True)
    name        = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)


class RolePermission(Base):
    __tablename__ = "survapp_role_permission"

    role_id       = Column(BigInteger, ForeignKey("survapp_role.id"),       nullable=False, primary_key=True)
    permission_id = Column(BigInteger, ForeignKey("survapp_permission.id"), nullable=False, primary_key=True)


class UserRole(Base):
    __tablename__ = "survapp_user_role"

    user_id = Column(BigInteger, ForeignKey("survapp_user.id"), nullable=False, primary_key=True)
    role_id = Column(BigInteger, ForeignKey("survapp_role.id"), nullable=False, primary_key=True)

    role = relationship("Role", back_populates="user_roles")
    user = relationship("User", back_populates="user_roles")


# ─── Camera Access Overrides ──────────────────────────────────────────────────

class UserCamera(Base):
    """Direct per-user camera access grant (overrides org-scope)."""
    __tablename__ = "survapp_user_camera"

    user_id   = Column(BigInteger, ForeignKey("survapp_user.id"),          nullable=False, primary_key=True)
    camera_id = Column(BigInteger, ForeignKey("survapp_camera_master.id"), nullable=False, primary_key=True)


# ─── Camera Groups ────────────────────────────────────────────────────────────

class CameraGroup(Base):
    __tablename__ = "camera_group"

    id              = Column(BigInteger, primary_key=True, index=True)
    name            = Column(String(200), nullable=False)
    organization_id = Column(BigInteger, ForeignKey("organization.id"), nullable=True)
    customer_id     = Column(BigInteger, ForeignKey("customer.id"),     nullable=True)
    created_at      = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    cameras = relationship("Camera", secondary="camera_group_mapping", lazy="select")
    users   = relationship("User",   secondary="user_group_mapping",   lazy="select")


class CameraGroupMapping(Base):
    __tablename__ = "camera_group_mapping"

    group_id  = Column(BigInteger, ForeignKey("camera_group.id"),          nullable=False, primary_key=True)
    camera_id = Column(BigInteger, ForeignKey("survapp_camera_master.id"), nullable=False, primary_key=True)


class UserGroupMapping(Base):
    __tablename__ = "user_group_mapping"

    user_id  = Column(BigInteger, ForeignKey("survapp_user.id"),  nullable=False, primary_key=True)
    group_id = Column(BigInteger, ForeignKey("camera_group.id"),  nullable=False, primary_key=True)


# ─── Sessions & Devices ───────────────────────────────────────────────────────

class UserSession(Base):
    __tablename__ = "user_session"

    id                 = Column(String(36), primary_key=True)   # UUID
    user_id            = Column(BigInteger, ForeignKey("survapp_user.id"), nullable=False)
    refresh_token_hash = Column(Text, nullable=True)
    device_name        = Column(String(200), nullable=True)
    device_type        = Column(String(100), nullable=True)
    ip_address         = Column(String(100), nullable=True)
    created_at         = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at         = Column(DateTime(timezone=True), nullable=True)
    is_active          = Column(Boolean, nullable=False, default=True)

    user = relationship("User", back_populates="sessions")


class DeviceToken(Base):
    __tablename__ = "device_token"

    id         = Column(BigInteger, primary_key=True, index=True)
    user_id    = Column(BigInteger, ForeignKey("survapp_user.id"), nullable=False)
    platform   = Column(String(20), nullable=True)   # android|ios|web
    token      = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="device_tokens")


# ─── Audit ────────────────────────────────────────────────────────────────────

class AuditLog(Base):
    """Immutable audit trail — only INSERT, never UPDATE or DELETE."""
    __tablename__ = "audit_log"

    id          = Column(BigInteger, primary_key=True, index=True)
    user_id     = Column(BigInteger, nullable=True)
    username    = Column(String(100), nullable=True)
    action      = Column(String(100), nullable=False)   # CREATE|UPDATE|DELETE|LOGIN|LOGOUT
    entity_type = Column(String(100), nullable=True)
    entity_id   = Column(String(100), nullable=True)
    old_value   = Column(JSON, nullable=True)
    new_value   = Column(JSON, nullable=True)
    ip_address  = Column(String(100), nullable=True)
    created_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)


# ─── Notifications ────────────────────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notification"

    id         = Column(BigInteger, primary_key=True, index=True)
    user_id    = Column(BigInteger, ForeignKey("survapp_user.id"), nullable=True)
    title      = Column(String(500), nullable=True)
    message    = Column(Text, nullable=True)
    payload    = Column(JSON, nullable=True)
    is_read    = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="notifications")


# ─── Password Reset ───────────────────────────────────────────────────────────

class PasswordResetToken(Base):
    __tablename__ = "password_reset_token"

    id         = Column(String(36), primary_key=True)   # UUID
    user_id    = Column(BigInteger, ForeignKey("survapp_user.id"), nullable=False)
    token_hash = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used       = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="password_reset_tokens")
