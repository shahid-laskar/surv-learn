"""
app/models/camera.py
Camera master model (expanded with org/customer/site linkage),
plus MotionEvent and VideoSegment.
"""

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey,
    Index, Integer, String,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Camera(Base):
    __tablename__ = "survapp_camera_master"

    id             = Column(Integer,     primary_key=True, index=True)
    cam_id         = Column(String(100), unique=True, nullable=False, index=True)
    cam_name       = Column(String(200), nullable=True)

    # ── Org / Customer / Site linkage (added in 0003) ─────────────
    organization_id  = Column(BigInteger, ForeignKey("organization.id"),  nullable=True)
    customer_id      = Column(BigInteger, ForeignKey("customer.id"),      nullable=True)
    customer_site_id = Column(BigInteger, ForeignKey("customer_site.id"), nullable=True)
    circle_id        = Column(BigInteger, ForeignKey("circle_master.id"), nullable=True)
    ba_id            = Column(BigInteger, ForeignKey("ba_master.id"),     nullable=True)

    # ── Device info ────────────────────────────────────────────────
    cam_ip         = Column(String(50),  nullable=False)
    cam_port       = Column(Integer,     default=554)
    onvif_port     = Column(Integer,     default=80)
    rtsp_url       = Column(String(500), nullable=True)
    onvif_username = Column(String(100), default="admin")
    onvif_password = Column(String(100), default="admin")
    camera_model   = Column(String(100), nullable=True)
    manufacturer   = Column(String(100), nullable=True)

    # ── Status ─────────────────────────────────────────────────────
    is_active     = Column(Boolean, default=True,  nullable=False)
    is_online     = Column(Boolean, default=False, nullable=False)
    motion_active = Column(Boolean, default=True,  nullable=False)
    last_seen     = Column(DateTime(timezone=True), nullable=True)
    created_at    = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # ── Relationships ─────────────────────────────────────────────
    organization  = relationship("Organization", back_populates="cameras",      lazy="select")
    customer      = relationship("Customer",     back_populates="cameras",      lazy="select")
    customer_site = relationship("CustomerSite", back_populates="cameras",      lazy="select")
    circle        = relationship("CircleMaster", back_populates="cameras",      lazy="select")
    ba            = relationship("BAMaster",     back_populates="cameras",      lazy="select")
    motion_events = relationship("MotionEvent",  back_populates="camera",       lazy="select")
    video_segments = relationship("VideoSegment", back_populates="camera",      lazy="select")


class MotionEvent(Base):
    __tablename__ = "survapp_motion_event"

    id           = Column(Integer,  primary_key=True, index=True)
    camera_id    = Column(Integer,  ForeignKey("survapp_camera_master.id"), nullable=False, index=True)
    motion_start = Column(DateTime(timezone=True), nullable=False)
    motion_end   = Column(DateTime(timezone=True), nullable=True)
    is_active    = Column(Boolean, default=True, nullable=False)
    created_at   = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    camera = relationship("Camera", back_populates="motion_events")

    __table_args__ = (
        Index("ix_motion_event_camera_active", "camera_id", "is_active"),
    )


class VideoSegment(Base):
    __tablename__ = "survapp_video_segment"

    id               = Column(Integer,     primary_key=True, index=True)
    camera_id        = Column(Integer,     ForeignKey("survapp_camera_master.id"), nullable=False, index=True)
    object_key       = Column(String(500), nullable=False, unique=True)
    bucket           = Column(String(100), default="recordings", nullable=False)
    segment_start    = Column(DateTime(timezone=True), nullable=False)
    segment_end      = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer,     nullable=True)
    file_size_bytes  = Column(BigInteger,  nullable=True)
    deleted_at       = Column(DateTime(timezone=True), nullable=True)
    created_at       = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    camera = relationship("Camera", back_populates="video_segments")

    __table_args__ = (
        Index("ix_video_segment_camera_start", "camera_id", "segment_start"),
    )