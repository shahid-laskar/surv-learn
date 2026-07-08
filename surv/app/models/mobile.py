"""
app/models/mobile.py
Mobile device registry: push notification tokens + WireGuard peer identity
for the embedded-VPN mobile app.

NOTE: app/models/rbac.py already defines a `DeviceToken` model
(`device_token` table) for push tokens. This is a deliberately separate
table rather than an extension of that one -- see migration
0007_mobile_devices.py. Revisit if the two should be consolidated.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey, String,
)
from sqlalchemy.orm import relationship

from app.database import Base


class MobileDevice(Base):
    __tablename__ = "mobile_device"

    id      = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("survapp_user.id", ondelete="CASCADE"), nullable=False, index=True)

    device_token = Column(String(500), nullable=False)
    platform     = Column(String(20),  nullable=False)   # 'ios' | 'android'
    device_name  = Column(String(200), nullable=True)
    app_version  = Column(String(20),  nullable=True)

    # -- Phase 16 -- WireGuard peer identity --
    wg_public_key      = Column(String(200), nullable=True)
    wg_peer_id         = Column(String(200), nullable=True)
    wg_peer_expires_at = Column(DateTime(timezone=True), nullable=True)

    is_active   = Column(Boolean, default=True, nullable=False)
    created_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_active = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="mobile_devices")

    def has_active_vpn_peer(self) -> bool:
        """True if this device currently holds a non-expired Headscale peer."""
        if not self.wg_peer_id:
            return False
        if self.wg_peer_expires_at is None:
            return True
        return self.wg_peer_expires_at > datetime.now(timezone.utc)