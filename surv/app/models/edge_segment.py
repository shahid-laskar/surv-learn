from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class EdgeVideoSegment(Base):
    __tablename__ = "edge_video_segment"
    __table_args__ = (
        UniqueConstraint("nvr_node_id", "camera_id", "segment_start", name="uq_edge_segment"),
    )

    id              = Column(BigInteger, primary_key=True, index=True)
    camera_id       = Column(Integer, ForeignKey("survapp_camera_master.id"), nullable=True, index=True)
    nvr_node_id     = Column(Integer, ForeignKey("nvr_node.id"), nullable=True, index=True)
    segment_start   = Column(DateTime(timezone=True), nullable=False)
    segment_end     = Column(DateTime(timezone=True), nullable=False)
    local_path      = Column(String(500), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=True)
    synced_at       = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    camera  = relationship("Camera", backref="edge_segments")
    nvr_node = relationship("NvrNode", backref="edge_segments")
