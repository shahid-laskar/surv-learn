from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime, timezone
from app.database import Base


class User(Base):
    __tablename__ = "survapp_user"

    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name     = Column(String(200))
    role          = Column(String(50), default="operator", nullable=False)
    is_active     = Column(Boolean, default=True, nullable=False)
    last_login    = Column(DateTime(timezone=True))
    created_at    = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
