"""
app/models/parking.py
SQLAlchemy models for multi-site Parking Management System (PMS):
ParkingZone, ParkingLane, and ParkingSession.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey,
    Integer, Numeric, String, Text, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship

from app.database import Base


class ParkingZone(Base):
    """
    Parking Ground / Zone (e.g. Ground 1 to 12 at Nilakkal).
    Holds capacity, current occupancy, and vehicle type allocation policies.
    """
    __tablename__ = "parking_zone"

    id               = Column(BigInteger, primary_key=True, index=True)
    customer_site_id = Column(BigInteger, ForeignKey("customer_site.id"), nullable=True, index=True)
    zone_code        = Column(String(50), nullable=False, index=True)
    name             = Column(String(200), nullable=False)
    # 'ALL' | 'LMV' | 'HMV' | '2W' | '3W' | 'BUS'
    vehicle_type     = Column(String(50), nullable=False, default="ALL")
    total_capacity   = Column(Integer, nullable=False, default=100)
    current_occupancy = Column(Integer, nullable=False, default=0)
    is_active        = Column(Boolean, nullable=False, default=True)
    display_order    = Column(Integer, nullable=False, default=0)
    created_at       = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at       = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                              onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    site     = relationship("CustomerSite", backref="parking_zones", lazy="select")
    lanes    = relationship("ParkingLane", back_populates="zone", cascade="all, delete-orphan", lazy="select")
    sessions = relationship("ParkingSession", back_populates="zone", lazy="select")

    __table_args__ = (
        UniqueConstraint("customer_site_id", "zone_code", name="uq_parking_zone_site_code"),
    )

    @property
    def available_slots(self) -> int:
        return max(0, self.total_capacity - self.current_occupancy)

    @property
    def occupancy_pct(self) -> float:
        if self.total_capacity <= 0:
            return 100.0
        return round((self.current_occupancy / self.total_capacity) * 100.0, 1)


class ParkingLane(Base):
    """
    Entry/Exit lane equipped with ANPR / boom barrier / handheld POS printer.
    """
    __tablename__ = "parking_lane"

    id               = Column(BigInteger, primary_key=True, index=True)
    parking_zone_id  = Column(BigInteger, ForeignKey("parking_zone.id", ondelete="CASCADE"), nullable=True, index=True)
    customer_site_id = Column(BigInteger, ForeignKey("customer_site.id"), nullable=True, index=True)
    lane_code        = Column(String(50), nullable=False)
    name             = Column(String(100), nullable=False)
    lane_type        = Column(String(20), nullable=False)  # 'ENTRY' | 'EXIT'
    camera_id        = Column(Integer, ForeignKey("survapp_camera_master.id", ondelete="SET NULL"), nullable=True)
    is_active        = Column(Boolean, nullable=False, default=True)
    created_at       = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    zone   = relationship("ParkingZone", back_populates="lanes")
    camera = relationship("Camera", backref="parking_lanes", lazy="select")

    __table_args__ = (
        UniqueConstraint("customer_site_id", "lane_code", name="uq_parking_lane_site_code"),
    )


class ParkingSession(Base):
    """
    Records vehicle lifecycle from entry through parking and exit.
    """
    __tablename__ = "parking_session"

    id                   = Column(BigInteger, primary_key=True, index=True)
    customer_site_id     = Column(BigInteger, ForeignKey("customer_site.id"), nullable=True, index=True)
    parking_zone_id      = Column(BigInteger, ForeignKey("parking_zone.id"), nullable=False, index=True)
    entry_lane_id        = Column(BigInteger, ForeignKey("parking_lane.id"), nullable=True)
    exit_lane_id         = Column(BigInteger, ForeignKey("parking_lane.id"), nullable=True)
    vehicle_number       = Column(String(50), nullable=False, index=True)
    normalized_plate     = Column(String(50), nullable=False, index=True)
    vehicle_type         = Column(String(50), nullable=False, default="LMV")
    entry_time           = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    exit_time            = Column(DateTime(timezone=True), nullable=True)
    status               = Column(String(30), nullable=False, default="ACTIVE", index=True)  # 'ACTIVE' | 'COMPLETED' | 'CANCELLED'
    entry_slip_number    = Column(String(100), unique=True, nullable=False, index=True)
    fee_amount           = Column(Numeric(10, 2), nullable=True, default=0.0)
    anpr_transaction_id  = Column(BigInteger, nullable=True, index=True)
    created_at           = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    zone       = relationship("ParkingZone", back_populates="sessions")
    entry_lane = relationship("ParkingLane", foreign_keys=[entry_lane_id])
    exit_lane  = relationship("ParkingLane", foreign_keys=[exit_lane_id])

    __table_args__ = (
        Index("ix_parking_session_site_status", "customer_site_id", "status"),
        Index("ix_parking_session_plate_status", "normalized_plate", "status"),
    )
