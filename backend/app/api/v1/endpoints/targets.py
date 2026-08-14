from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.api.deps import get_db
from app.models.target import Target, TargetStatus
from app.schemas.target import TargetCreate, TargetResponse, TargetDetailResponse, TargetUpdate

router = APIRouter()


@router.get("/", response_model=List[TargetResponse])
async def get_targets(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    """Retrieve all targets with pagination."""
    result = await db.execute(select(Target).offset(skip).limit(limit))
    return result.scalars().all()


@router.post("/", response_model=TargetResponse, status_code=status.HTTP_201_CREATED)
async def create_target(target_in: TargetCreate, db: AsyncSession = Depends(get_db)):
    """Create a new target profile."""
    result = await db.execute(select(Target).filter(Target.email == target_in.email))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Target with this email already exists")

    target = Target(
        email=target_in.email,
        phone_number=target_in.phone_number,
        provider=target_in.provider,
        status=TargetStatus.IDLE,
    )
    db.add(target)
    await db.commit()
    await db.refresh(target)
    return target


@router.get("/{target_id}", response_model=TargetDetailResponse)
async def get_target(target_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get detailed target profile including relationship counts."""
    result = await db.execute(select(Target).filter(Target.id == target_id))
    target = result.scalars().first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    # The relationships are selectin-loaded, but we need counts
    target.credential_count = len(target.credentials)
    target.session_count = len(target.sessions)
    target.otp_count = len(target.otps)

    return target


@router.patch("/{target_id}", response_model=TargetResponse)
async def update_target(target_id: UUID, target_update: TargetUpdate, db: AsyncSession = Depends(get_db)):
    """Partially update a target profile."""
    result = await db.execute(select(Target).filter(Target.id == target_id))
    target = result.scalars().first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    update_data = target_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(target, key, value)

    await db.commit()
    await db.refresh(target)
    return target


@router.delete("/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(target_id: UUID, db: AsyncSession = Depends(get_db)):
    """Delete a target profile and all cascading data (credentials, sessions, OTPs)."""
    result = await db.execute(select(Target).filter(Target.id == target_id))
    target = result.scalars().first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")

    await db.delete(target)
    await db.commit()
    return None
