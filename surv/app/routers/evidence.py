"""
app/routers/evidence.py
FastAPI router for Tamper-Evident Evidence Export & Cryptographic Verification.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import get_current_user, CurrentUser
from app.models.evidence import EvidencePackage
from app.schemas.evidence import (
    EvidenceExportRequest,
    EvidencePackageOut,
    EvidenceVerificationResult,
)
from app.services.evidence_service import EvidenceService

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post("/export", response_model=EvidencePackageOut, status_code=status.HTTP_201_CREATED)
async def export_evidence_package(
    payload: EvidenceExportRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Exports a sealed evidence archive with video, snapshots, metadata,
    and a cryptographic SHA-256 manifest.
    """
    pkg = await EvidenceService.create_evidence_package(db, payload, user_id=user.user_id)
    return EvidencePackageOut.model_validate(pkg)


@router.get("/packages", response_model=List[EvidencePackageOut])
async def list_evidence_packages(
    incident_id: Optional[int] = Query(None, description="Filter by linked incident ID"),
    camera_id: Optional[int] = Query(None, description="Filter by camera ID"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """List historical sealed evidence packages."""
    stmt = select(EvidencePackage).order_by(EvidencePackage.created_at.desc())
    if incident_id is not None:
        stmt = stmt.where(EvidencePackage.incident_id == incident_id)
    if camera_id is not None:
        stmt = stmt.where(EvidencePackage.camera_id == camera_id)

    stmt = stmt.offset(offset).limit(limit)
    res = await db.execute(stmt)
    items = res.scalars().all()
    return [EvidencePackageOut.model_validate(item) for item in items]


@router.get("/packages/{package_id}", response_model=EvidencePackageOut)
async def get_evidence_package(
    package_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """Get metadata and SHA-256 seal for an evidence package."""
    pkg = await db.get(EvidencePackage, package_id)
    if not pkg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence package not found")
    return EvidencePackageOut.model_validate(pkg)


@router.get("/packages/{package_id}/verify", response_model=EvidenceVerificationResult)
async def verify_stored_package(
    package_id: int,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """
    Performs forensic checksum verification on an existing stored evidence package.
    Recalculates individual file hashes against manifest.json and validates the manifest seal.
    """
    pkg = await db.get(EvidencePackage, package_id)
    if not pkg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evidence package not found")

    return EvidenceService.verify_evidence_package(pkg.file_path)
