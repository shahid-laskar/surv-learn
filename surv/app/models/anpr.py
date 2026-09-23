"""
app/models/anpr.py
SQLAlchemy models for ANPR Management Plane, Vehicle Watchlists, and Real-Time Alerts.
Decoupled from inference hardware — standard ingest and search schema.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Float, ForeignKey,
    Index, Integer, Numeric, String, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class AnprTransaction(Base):
    """
    Normalized central record for all vehicle plate reads emitted by Edge LPUs or Hub AI.
    """
    __tablename__ = "anpr_transaction"

    id                  = Column(BigInteger, primary_key=True, index=True)
    customer_site_id    = Column(BigInteger, ForeignKey("customer_site.id"), nullable=True, index=True)
    camera_id           = Column(Integer, ForeignKey("survapp_camera_master.id", ondelete="SET NULL"), nullable=True, index=True)
    lane_id             = Column(BigInteger, nullable=True, index=True)
    
    plate_number        = Column(String(50), nullable=False, index=True)
    normalized_plate    = Column(String(50), nullable=False, index=True)
    confidence          = Column(Float, nullable=False, default=1.0)
    
    # Classification
    vehicle_type        = Column(String(50), nullable=True, default="CAR")  # 2W, 3W, CAR, LMV, HMV, BUS, TRUCK
    vehicle_color       = Column(String(50), nullable=True)
    speed_kmh           = Column(Float, nullable=True)
    direction           = Column(String(20), nullable=True)  # IN / OUT
    
    # Media & Evidence references
    snapshot_key        = Column(String(500), nullable=True)
    video_reference     = Column(String(500), nullable=True)
    processing_source   = Column(String(50), nullable=False, default="edge_lpu")  # edge_lpu, hub_ai, synthetic
    
    # Human-in-the-loop Correction
    is_corrected        = Column(Boolean, nullable=False, default=False)
    original_plate      = Column(String(50), nullable=True)
    corrected_by_user_id = Column(BigInteger, ForeignKey("survapp_user.id", ondelete="SET NULL"), nullable=True)
    correction_notes    = Column(Text, nullable=True)
    
    captured_at         = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    created_at          = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    camera = relationship("Camera", backref="anpr_transactions", lazy="select")
    corrected_by = relationship("User", foreign_keys=[corrected_by_user_id], lazy="select")

    __table_args__ = (
        Index("ix_anpr_site_captured", "customer_site_id", "captured_at"),
        Index("ix_anpr_camera_captured", "camera_id", "captured_at"),
    )


class VehicleWatchlist(Base):
    """
    Hotlist / Blacklist / Stolen vehicle registry for instant alert matching.
    """
    __tablename__ = "vehicle_watchlist"

    id                  = Column(BigInteger, primary_key=True, index=True)
    plate_number        = Column(String(50), nullable=False, index=True)
    normalized_plate    = Column(String(50), unique=True, nullable=False, index=True)
    # 'WANTED' | 'STOLEN' | 'SUSPICIOUS' | 'CUSTOM' | 'VIP'
    category            = Column(String(50), nullable=False, default="WANTED")
    # 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'
    severity            = Column(String(20), nullable=False, default="HIGH")
    reason              = Column(Text, nullable=False)
    case_number         = Column(String(100), nullable=True)
    reporting_authority = Column(String(200), nullable=True)  # e.g., Kerala Police Pathanamthitta
    
    is_active           = Column(Boolean, nullable=False, default=True)
    created_by_user_id  = Column(BigInteger, ForeignKey("survapp_user.id", ondelete="SET NULL"), nullable=True)
    created_at          = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at          = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                                 onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    creator = relationship("User", foreign_keys=[created_by_user_id], lazy="select")
    alerts  = relationship("WatchlistAlert", back_populates="watchlist", cascade="all, delete-orphan", lazy="select")


class WatchlistAlert(Base):
    """
    Triggered when an ANPR read matches a VehicleWatchlist entry.
    """
    __tablename__ = "watchlist_alert"

    id                      = Column(BigInteger, primary_key=True, index=True)
    watchlist_id            = Column(BigInteger, ForeignKey("vehicle_watchlist.id", ondelete="CASCADE"), nullable=False, index=True)
    anpr_transaction_id     = Column(BigInteger, ForeignKey("anpr_transaction.id", ondelete="CASCADE"), nullable=False, index=True)
    plate_number            = Column(String(50), nullable=False, index=True)
    camera_id               = Column(Integer, ForeignKey("survapp_camera_master.id", ondelete="SET NULL"), nullable=True)
    customer_site_id        = Column(BigInteger, ForeignKey("customer_site.id", ondelete="SET NULL"), nullable=True)
    severity                = Column(String(20), nullable=False, default="HIGH")
    status                  = Column(String(30), nullable=False, default="ACTIVE", index=True)  # 'ACTIVE' | 'ACKNOWLEDGED' | 'DISMISSED'
    
    acknowledged_by_user_id = Column(BigInteger, ForeignKey("survapp_user.id", ondelete="SET NULL"), nullable=True)
    acknowledged_at         = Column(DateTime(timezone=True), nullable=True)
    notes                   = Column(Text, nullable=True)
    created_at              = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    watchlist   = relationship("VehicleWatchlist", back_populates="alerts")
    transaction = relationship("AnprTransaction", backref="alerts", lazy="select")
    camera      = relationship("Camera", lazy="select")
    acknowledged_by = relationship("User", foreign_keys=[acknowledged_by_user_id], lazy="select")

    __table_args__ = (
        Index("ix_watchlist_alert_status_created", "status", "created_at"),
    )
