from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

CUSTOMER_TYPES = [
    "ENTERPRISE", "BANK", "SCHOOL", "HOSPITAL",
    "APARTMENT", "GOVERNMENT", "INDIVIDUAL", "PARTNER",
]

# ── Customer ──────────────────────────────────────────────────────────────────

class CustomerCreate(BaseModel):
    parent_customer_id: Optional[int] = None
    customer_code:      Optional[str] = None
    name:               str
    customer_type:      Optional[str] = None
    organization_id:    Optional[int] = None
    circle_id:          Optional[int] = None
    ba_id:              Optional[int] = None
    email:              Optional[str] = None
    phone:              Optional[str] = None
    address:            Optional[str] = None


class CustomerUpdate(BaseModel):
    name:            Optional[str] = None
    customer_type:   Optional[str] = None
    organization_id: Optional[int] = None
    circle_id:       Optional[int] = None
    ba_id:           Optional[int] = None
    email:           Optional[str] = None
    phone:           Optional[str] = None
    address:         Optional[str] = None
    is_active:       Optional[bool] = None


class CustomerOut(BaseModel):
    id:                 int
    parent_customer_id: Optional[int]
    customer_code:      Optional[str]
    name:               str
    customer_type:      Optional[str]
    organization_id:    Optional[int]
    circle_id:          Optional[int]
    ba_id:              Optional[int]
    email:              Optional[str]
    phone:              Optional[str]
    is_active:          bool
    created_at:         datetime

    model_config = {"from_attributes": True}


# ── Customer Site ─────────────────────────────────────────────────────────────

class CustomerSiteCreate(BaseModel):
    site_code:  Optional[str] = None
    name:       Optional[str] = None
    state:      Optional[str] = None
    district:   Optional[str] = None
    city:       Optional[str] = None
    address:    Optional[str] = None
    latitude:   Optional[Decimal] = None
    longitude:  Optional[Decimal] = None


class CustomerSiteOut(BaseModel):
    id:          int
    customer_id: int
    site_code:   Optional[str]
    name:        Optional[str]
    state:       Optional[str]
    district:    Optional[str]
    city:        Optional[str]
    latitude:    Optional[Decimal]
    longitude:   Optional[Decimal]
    is_active:   bool
    created_at:  datetime

    model_config = {"from_attributes": True}
