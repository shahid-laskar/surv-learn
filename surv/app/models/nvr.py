from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey,
    Integer, Numeric, String
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class NvrNode(Base):
    __tablename__ = "nvr_node"

    id               = Column(Integer, primary_key=True, index=True)
    site_code        = Column(String(50), unique=True, nullable=False, index=True)
    customer_site_id = Column(BigInteger, ForeignKey("customer_site.id"), nullable=True)
    overlay_ip       = Column(String(50), nullable=True)
    wg_node_key      = Column(String(200), nullable=True)
    hardware_label   = Column(String(100), nullable=True)
    agent_version    = Column(String(50), nullable=True)
    last_heartbeat   = Column(DateTime(timezone=True), nullable=True)
    disk_used_pct    = Column(Numeric(5, 2), nullable=True)
    is_provisioned   = Column(Boolean, default=False, nullable=True)
    site_enrollment_secret = Column(String(64), nullable=True)
    created_at       = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    site             = relationship("CustomerSite", backref="nvr_nodes", lazy="select")
    camera_mappings  = relationship("NvrCameraMap", back_populates="nvr_node", cascade="all, delete-orphan")
    backup_clips     = relationship("BackupClip", back_populates="nvr_node", lazy="select")
    
    # In Phase 13 this gets expanded with 4G/ISP columns, but this is the Phase 12 base.


class NvrCameraMap(Base):
    __tablename__ = "nvr_camera_map"

    nvr_node_id = Column(Integer, ForeignKey("nvr_node.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    camera_id   = Column(Integer, ForeignKey("survapp_camera_master.id", ondelete="CASCADE"), primary_key=True, nullable=False)

    nvr_node = relationship("NvrNode", back_populates="camera_mappings")
    camera   = relationship("Camera", back_populates="nvr_mapping")


class BackupClip(Base):
    __tablename__ = "backup_clip"

    id          = Column(BigInteger, primary_key=True, index=True)
    nvr_node_id = Column(Integer, ForeignKey("nvr_node.id", ondelete="SET NULL"), nullable=True, index=True)
    camera_id   = Column(Integer, ForeignKey("survapp_camera_master.id", ondelete="SET NULL"), nullable=True, index=True)
    object_key  = Column(String(500), nullable=True)
    reason      = Column(String(50), nullable=True)
    captured_at = Column(DateTime(timezone=True), nullable=True)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    nvr_node = relationship("NvrNode", back_populates="backup_clips")
    camera   = relationship("Camera", backref="backup_clips")
