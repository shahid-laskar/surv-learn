from pydantic import BaseModel
from typing import Optional

# ── Roles ─────────────────────────────────────────────────────────────────────

class RoleCreate(BaseModel):
    code:        str
    name:        Optional[str] = None
    description: Optional[str] = None


class RoleOut(BaseModel):
    id:          int
    code:        str
    name:        Optional[str]
    description: Optional[str]

    model_config = {"from_attributes": True}


# ── Permissions ───────────────────────────────────────────────────────────────

class PermissionCreate(BaseModel):
    code:        str
    name:        Optional[str] = None
    description: Optional[str] = None


class PermissionOut(BaseModel):
    id:          int
    code:        str
    name:        Optional[str]
    description: Optional[str]

    model_config = {"from_attributes": True}


# ── Assignments ───────────────────────────────────────────────────────────────

class RolePermissionAssign(BaseModel):
    permission_id: int


class UserRoleAssign(BaseModel):
    role_id: int


# ── Camera Groups ─────────────────────────────────────────────────────────────

class CameraGroupCreate(BaseModel):
    name:            str
    organization_id: Optional[int] = None
    customer_id:     Optional[int] = None


class CameraGroupOut(BaseModel):
    id:              int
    name:            str
    organization_id: Optional[int]
    customer_id:     Optional[int]

    model_config = {"from_attributes": True}


class CameraGroupCameraAssign(BaseModel):
    camera_id: int


class UserGroupAssign(BaseModel):
    user_id: int
