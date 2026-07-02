"""
app/models/__init__.py
Central import so Alembic's env.py discovers all models from
`from app.models import Base` — no extra imports needed in env.py.
"""

from app.database import Base  # noqa: F401

# Import all models so SQLAlchemy's mapper registry is fully populated
# and Alembic can generate correct --autogenerate diffs.
from app.models.user import User                                    # noqa: F401
from app.models.camera import Camera, MotionEvent, VideoSegment    # noqa: F401
from app.models.organization import (                               # noqa: F401
    CircleMaster, BAMaster,
    Organization, OrganizationClosure, Customer, CustomerSite,
)
from app.models.rbac import (                                       # noqa: F401
    Role, Permission, RolePermission, UserRole,
    UserCamera,
    CameraGroup, CameraGroupMapping, UserGroupMapping,
    UserSession, DeviceToken,
    AuditLog, Notification, PasswordResetToken,
)
