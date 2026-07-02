from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.models.organization import CircleMaster, BAMaster
from app.schemas.organization import CircleMasterOut, BAMasterOut
from app.dependencies.auth import get_current_user

router = APIRouter(
    prefix="/api/v1/bsnl",
    tags=["BSNL Masters"],
)

@router.get("/circles", response_model=list[CircleMasterOut])
async def get_circles(
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    result = await db.execute(select(CircleMaster).where(CircleMaster.is_active == True))
    return result.scalars().all()

@router.get("/bas", response_model=list[BAMasterOut])
async def get_bas(
    circle_id: int | None = None,
    db: AsyncSession = Depends(get_db),
    user = Depends(get_current_user),
):
    query = select(BAMaster).where(BAMaster.is_active == True)
    if circle_id is not None:
        query = query.where(BAMaster.circle_id == circle_id)
    result = await db.execute(query)
    return result.scalars().all()
