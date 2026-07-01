from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in:  int   # seconds
    username:    str
    role:        str


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    role: str = "operator"  # operator | admin


class UserOut(BaseModel):
    id:         int
    username:   str
    full_name:  Optional[str]
    role:       str
    is_active:  bool
    last_login: Optional[datetime]
    created_at: datetime

    model_config = {"from_attributes": True}


class StreamTokenResponse(BaseModel):
    cam_id:     str
    hls_url:    str
    token:      str
    expires_at: str
