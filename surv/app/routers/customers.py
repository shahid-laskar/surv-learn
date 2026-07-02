"""
app/routers/customers.py
CRUD for customers and customer sites.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.dependencies.auth import get_current_user, require_permission, CurrentUser
from app.models.organization import Customer, CustomerSite
from app.schemas.customer import (
    CustomerCreate, CustomerUpdate, CustomerOut,
    CustomerSiteCreate, CustomerSiteOut,
)

log = logging.getLogger(__name__)
router = APIRouter(prefix="/customers", tags=["customers"])


# ── Customer endpoints ────────────────────────────────────────────────────────

@router.get("/", response_model=list[CustomerOut])
async def list_customers(
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(select(Customer).order_by(Customer.id))
    return result.scalars().all()


@router.post("/", response_model=CustomerOut, status_code=201)
async def create_customer(
    payload: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("customer.create")),
):
    customer = Customer(**payload.model_dump())
    db.add(customer)
    await db.commit()
    await db.refresh(customer)
    log.info(f"Customer created: {customer.name} (id={customer.id})")
    return customer


@router.get("/{customer_id}", response_model=CustomerOut)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    customer = await db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(404, "Customer not found")
    return customer


@router.patch("/{customer_id}", response_model=CustomerOut)
async def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("customer.update")),
):
    customer = await db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(404, "Customer not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(customer, k, v)
    await db.commit()
    await db.refresh(customer)
    return customer


# ── Customer Site endpoints ───────────────────────────────────────────────────

@router.get("/{customer_id}/sites", response_model=list[CustomerSiteOut])
async def list_sites(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    result = await db.execute(
        select(CustomerSite).where(CustomerSite.customer_id == customer_id)
    )
    return result.scalars().all()


@router.post("/{customer_id}/sites", response_model=CustomerSiteOut, status_code=201)
async def create_site(
    customer_id: int,
    payload: CustomerSiteCreate,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_permission("customer.update")),
):
    customer = await db.get(Customer, customer_id)
    if not customer:
        raise HTTPException(404, "Customer not found")
    site = CustomerSite(customer_id=customer_id, **payload.model_dump())
    db.add(site)
    await db.commit()
    await db.refresh(site)
    return site
