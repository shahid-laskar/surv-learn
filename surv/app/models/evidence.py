"""
app/models/evidence.py
SQLAlchemy models for Tamper-Evident Evidence Export Packages.
Includes cryptographic SHA-256 manifests, chain-of-custody metadata,
and sealing verification for legal proceedings.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey,
    Index, Integer, String, Text
)
from sqlalchemy.orm import relationship

from app.database import Base


class EvidencePackage(Base):
    """
    Exported evidence container containing video clips, snapshots, metadata,
    and a SHA-256 checksum manifest.
    """
    __tablename__ = "evidence_package"

    id                  = Column(BigInteger, primary_key=True, index=True)
    package_number      = Column(String(100), unique=True, nullable=False, index=True)
    title               = Column(String(255), nullable=False)
    description         = Column(Text, nullable=True)

    incident_id         = Column(BigInteger, ForeignKey("incident.id", ondelete="SET NULL"), nullable=True, index=True)
    camera_id           = Column(Integer, ForeignKey("survapp_camera_master.id", ondelete="SET NULL"), nullable=True, index=True)
    customer_site_id    = Column(BigInteger, ForeignKey("customer_site.id", ondelete="SET NULL"), nullable=True)

    file_path           = Column(String(500), nullable=False)
    sha256_hash         = Column(String(64), nullable=False)
    file_size_bytes     = Column(BigInteger, nullable=False, default=0)

    exported_by_user_id = Column(BigInteger, ForeignKey("survapp_user.id", ondelete="SET NULL"), nullable=True)
    is_sealed           = Column(Boolean, nullable=False, default=True)

    created_at          = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    incident    = relationship("Incident", lazy="select")
    camera      = relationship("Camera", lazy="select")
    exported_by = relationship("User", foreign_keys=[exported_by_user_id], lazy="select")
