from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# ── Organization ──────────────────────────────────────────────────────────────

ORG_TYPES = ["ROOT", "CIRCLE", "BA", "SSA", "DISTRICT", "SITE", "NOC"]


class CircleMasterOut(BaseModel):
    id: int
    cir_code: str
    cir_name: str
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class BAMasterOut(BaseModel):
    id: int
    ba_code: str
    ba_name: str
    circle_id: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class OrganizationCreate(BaseModel):
    parent_id: Optional[int] = None
    code:      str
    name:      str
    type:      str   # one of ORG_TYPES
    circle_id: Optional[int] = None
    ba_id:     Optional[int] = None


class OrganizationUpdate(BaseModel):
    name:      Optional[str] = None
    type:      Optional[str] = None
    circle_id: Optional[int] = None
    ba_id:     Optional[int] = None
    is_active: Optional[bool] = None


class OrganizationOut(BaseModel):
    id:        int
    parent_id: Optional[int]
    code:      str
    name:      str
    type:      str
    circle_id: Optional[int]
    ba_id:     Optional[int]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class OrganizationTree(OrganizationOut):
    """Recursive tree node — children populated by the router."""
    children: list["OrganizationTree"] = []

    model_config = {"from_attributes": True}


OrganizationTree.model_rebuild()
