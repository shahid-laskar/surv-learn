"""
app/models/organization.py
SQLAlchemy models for the organization tree, closure table,
customer, and customer site.
"""

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey,
    Integer, Numeric, String, Text, UniqueConstraint,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class CircleMaster(Base):
    __tablename__ = "circle_master"

    id         = Column(BigInteger, primary_key=True, index=True)
    cir_code   = Column(String(50), nullable=False, unique=True)
    cir_name   = Column(String(200), nullable=False)
    is_active  = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    bas           = relationship("BAMaster", back_populates="circle", lazy="select")
    organizations = relationship("Organization", back_populates="circle", lazy="select")
    customers     = relationship("Customer", back_populates="circle", lazy="select")
    cameras       = relationship("Camera", back_populates="circle", lazy="select")
    users         = relationship("User", back_populates="circle", lazy="select")


class BAMaster(Base):
    __tablename__ = "ba_master"

    id         = Column(BigInteger, primary_key=True, index=True)
    ba_code    = Column(String(50), nullable=False)
    ba_name    = Column(String(200), nullable=False)
    circle_id  = Column(BigInteger, ForeignKey("circle_master.id"), nullable=False)
    is_active  = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    circle        = relationship("CircleMaster", back_populates="bas")
    organizations = relationship("Organization", back_populates="ba", lazy="select")
    customers     = relationship("Customer", back_populates="ba", lazy="select")
    cameras       = relationship("Camera", back_populates="ba", lazy="select")
    users         = relationship("User", back_populates="ba", lazy="select")


class Organization(Base):
    __tablename__ = "organization"

    id        = Column(BigInteger, primary_key=True, index=True)
    parent_id = Column(BigInteger, ForeignKey("organization.id"), nullable=True)
    code      = Column(String(50), nullable=False, unique=True)
    name      = Column(String(200), nullable=False)
    type      = Column(String(50), nullable=False)   # ROOT|CIRCLE|BA|SSA|DISTRICT|SITE|NOC
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    circle_id  = Column(BigInteger, ForeignKey("circle_master.id"), nullable=True)
    ba_id      = Column(BigInteger, ForeignKey("ba_master.id"), nullable=True)

    # Self-referential relationship
    parent   = relationship("Organization", remote_side="Organization.id", back_populates="children")
    children = relationship("Organization", back_populates="parent", lazy="select")

    customers = relationship("Customer", back_populates="organization", lazy="select")
    cameras   = relationship("Camera",   back_populates="organization", lazy="select")
    users     = relationship("User",     back_populates="organization", lazy="select")
    circle    = relationship("CircleMaster", back_populates="organizations")
    ba        = relationship("BAMaster", back_populates="organizations")


class OrganizationClosure(Base):
    """
    Precomputed closure table for fast subtree queries.
    Each org node has a self-reference row (depth=0).
    Populated/maintained by the org creation service.
    """
    __tablename__ = "organization_closure"

    parent_id = Column(BigInteger, ForeignKey("organization.id"), nullable=False, primary_key=True)
    child_id  = Column(BigInteger, ForeignKey("organization.id"), nullable=False, primary_key=True)
    depth     = Column(Integer, nullable=False)


class Customer(Base):
    __tablename__ = "customer"

    id                 = Column(BigInteger, primary_key=True, index=True)
    parent_customer_id = Column(BigInteger, ForeignKey("customer.id"), nullable=True)
    customer_code      = Column(String(100), nullable=True, unique=True)
    name               = Column(String(200), nullable=False)
    customer_type      = Column(String(50), nullable=True)  # ENTERPRISE|BANK|SCHOOL|...
    organization_id    = Column(BigInteger, ForeignKey("organization.id"), nullable=True)
    email              = Column(String(255), nullable=True)
    phone              = Column(String(30), nullable=True)
    address            = Column(Text, nullable=True)
    is_active          = Column(Boolean, nullable=False, default=True)
    created_at         = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at         = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                                onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    circle_id          = Column(BigInteger, ForeignKey("circle_master.id"), nullable=True)
    ba_id              = Column(BigInteger, ForeignKey("ba_master.id"), nullable=True)

    organization = relationship("Organization", back_populates="customers")
    sites        = relationship("CustomerSite",  back_populates="customer", lazy="select")
    cameras      = relationship("Camera",        back_populates="customer",  lazy="select")
    users        = relationship("User",          back_populates="customer",  lazy="select")
    circle       = relationship("CircleMaster",  back_populates="customers")
    ba           = relationship("BAMaster",      back_populates="customers")

    # Self-referential parent/child customers
    parent_customer  = relationship("Customer", remote_side="Customer.id", back_populates="sub_customers")
    sub_customers    = relationship("Customer", back_populates="parent_customer", lazy="select")


class CustomerSite(Base):
    __tablename__ = "customer_site"

    id          = Column(BigInteger, primary_key=True, index=True)
    customer_id = Column(BigInteger, ForeignKey("customer.id"), nullable=False)
    site_code   = Column(String(100), nullable=True)
    name        = Column(String(200), nullable=True)
    state       = Column(String(100), nullable=True)
    district    = Column(String(100), nullable=True)
    city        = Column(String(100), nullable=True)
    address     = Column(Text, nullable=True)
    latitude    = Column(Numeric(10, 7), nullable=True)
    longitude   = Column(Numeric(10, 7), nullable=True)
    is_active   = Column(Boolean, nullable=False, default=True)
    created_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    customer = relationship("Customer",  back_populates="sites")
    cameras  = relationship("Camera",    back_populates="customer_site", lazy="select")
