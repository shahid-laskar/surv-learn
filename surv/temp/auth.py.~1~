from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    expires_in:   int          # seconds
    # Identity
    username:     str
    user_type:    str = "EMPLOYEE"
    # Legacy flat role kept for frontend compat during transition
    role:         str
    # New RBAC fields
    roles:        list[str] = []
    permissions:  list[str] = []
    # Org context
    org_id:       Optional[int] = None
    customer_id:  Optional[int] = None


class UserCreate(BaseModel):
    username:   str = Field(..., min_length=3, max_length=100)
    password:   str = Field(..., min_length=8)
    email:      Optional[str] = None
    mobile:     Optional[str] = None
    first_name: Optional[str] = None
    last_name:  Optional[str] = None
    full_name:  Optional[str] = None   # legacy compat
    user_type:  str = "EMPLOYEE"       # EMPLOYEE | CUSTOMER | PARTNER | SYSTEM
    role:       str = "operator"       # legacy flat role
    organization_id: Optional[int] = None
    customer_id:     Optional[int] = None
    circle_id:       Optional[int] = None
    ba_id:           Optional[int] = None


class UserOut(BaseModel):
    id:           int
    username:     str
    email:        Optional[str]
    mobile:       Optional[str]
    first_name:   Optional[str]
    last_name:    Optional[str]
    full_name:    Optional[str]
    user_type:    str
    role:         str
    is_active:    bool
    is_locked:    bool
    organization_id: Optional[int]
    customer_id:     Optional[int]
    circle_id:       Optional[int]
    ba_id:           Optional[int]
    last_login:   Optional[datetime]
    created_at:   datetime
    # RBAC — populated by join, not from DB column
    roles:        list[str] = []
    permissions:  list[str] = []

    model_config = {"from_attributes": True}


class StreamTokenResponse(BaseModel):
    cam_id:     str
    hls_url:    str
    token:      str
    expires_at: str
