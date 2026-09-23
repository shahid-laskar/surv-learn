"""
app/models/incident.py
SQLAlchemy models for ICCC Incident Management & State Transition Auditing.
Tracks lifecycle (NEW -> ASSIGNED -> ESCALATED -> RESOLVED -> CLOSED)
with complete timeline audit trails linked to ANPR, motion, or camera alerts.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey,
    Index, Integer, String, Text
)
from sqlalchemy.orm import relationship

from app.database import Base


class Incident(Base):
    """
    Central operational incident entity for ICCC control rooms.
    """
    __tablename__ = "incident"

    id                  = Column(BigInteger, primary_key=True, index=True)
    incident_number     = Column(String(100), unique=True, nullable=False, index=True)
    title               = Column(String(255), nullable=False)
    description         = Column(Text, nullable=True)
    
    # State machine: NEW | ASSIGNED | ESCALATED | RESOLVED | CLOSED
    status              = Column(String(50), nullable=False, default="NEW", index=True)
    # CRITICAL | HIGH | MEDIUM | LOW
    severity            = Column(String(20), nullable=False, default="MEDIUM", index=True)
    # manual | anpr_alert | motion_alert | camera_offline
    source_type         = Column(String(50), nullable=False, default="manual")
    source_id           = Column(BigInteger, nullable=True)

    camera_id           = Column(Integer, ForeignKey("survapp_camera_master.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_site_id    = Column(BigInteger, ForeignKey("customer_site.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_to_user_id = Column(BigInteger, ForeignKey("survapp_user.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_user_id  = Column(BigInteger, ForeignKey("survapp_user.id", ondelete="SET NULL"), nullable=True)
    evidence_package_id = Column(BigInteger, nullable=True)

    created_at          = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at          = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                                 onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    camera      = relationship("Camera", lazy="select")
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id], lazy="select")
    created_by  = relationship("User", foreign_keys=[created_by_user_id], lazy="select")
    timeline    = relationship("IncidentTimeline", back_populates="incident", cascade="all, delete-orphan",
                               order_by="IncidentTimeline.created_at.asc()", lazy="select")


class IncidentTimeline(Base):
    """
    Audit log of incident lifecycle transitions and operator investigations.
    """
    __tablename__ = "incident_timeline"

    id                  = Column(BigInteger, primary_key=True, index=True)
    incident_id         = Column(BigInteger, ForeignKey("incident.id", ondelete="CASCADE"), nullable=False, index=True)
    from_status         = Column(String(50), nullable=True)
    to_status           = Column(String(50), nullable=False)
    changed_by_user_id  = Column(BigInteger, ForeignKey("survapp_user.id", ondelete="SET NULL"), nullable=True)
    notes               = Column(Text, nullable=True)
    created_at          = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    incident   = relationship("Incident", back_populates="timeline")
    changed_by = relationship("User", foreign_keys=[changed_by_user_id], lazy="select")
