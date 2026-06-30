from sqlalchemy import (
    Column, Integer, String, Boolean,
    DateTime, BigInteger, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class Camera(Base):
    __tablename__ = "survapp_camera_master"

    id             = Column(Integer, primary_key=True, index=True)
    cam_id         = Column(String(100), unique=True, nullable=False, index=True)
    cam_name       = Column(String(200))
    cam_ip         = Column(String(50), nullable=False)
    cam_port       = Column(Integer, default=554)
    onvif_port     = Column(Integer, default=80)
    rtsp_url       = Column(String(500))
    onvif_username = Column(String(100), default="admin")
    onvif_password = Column(String(100), default="admin")
    is_active      = Column(Boolean, default=True, nullable=False)
    is_online      = Column(Boolean, default=False, nullable=False)
    motion_active  = Column(Boolean, default=True, nullable=False)
    last_seen      = Column(DateTime(timezone=True))
    created_at     = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    motion_events  = relationship("MotionEvent", back_populates="camera",
                                  lazy="select")
    video_segments = relationship("VideoSegment", back_populates="camera",
                                  lazy="select")


class MotionEvent(Base):
    __tablename__ = "survapp_motion_event"

    id           = Column(Integer, primary_key=True, index=True)
    camera_id    = Column(Integer, ForeignKey("survapp_camera_master.id"),
                          nullable=False, index=True)
    motion_start = Column(DateTime(timezone=True), nullable=False)
    motion_end   = Column(DateTime(timezone=True))
    is_active    = Column(Boolean, default=True, nullable=False)
    created_at   = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    camera = relationship("Camera", back_populates="motion_events")

    __table_args__ = (
        Index("ix_motion_event_camera_active", "camera_id", "is_active"),
    )


class VideoSegment(Base):
    __tablename__ = "survapp_video_segment"

    id               = Column(Integer, primary_key=True, index=True)
    camera_id        = Column(Integer, ForeignKey("survapp_camera_master.id"),
                              nullable=False, index=True)
    object_key       = Column(String(500), nullable=False, unique=True)
    bucket           = Column(String(100), default="recordings", nullable=False)
    segment_start    = Column(DateTime(timezone=True), nullable=False)
    segment_end      = Column(DateTime(timezone=True))
    duration_seconds = Column(Integer)
    file_size_bytes  = Column(BigInteger)
    deleted_at       = Column(DateTime(timezone=True))
    created_at       = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    camera = relationship("Camera", back_populates="video_segments")

    __table_args__ = (
        Index("ix_video_segment_camera_start", "camera_id", "segment_start"),
    )