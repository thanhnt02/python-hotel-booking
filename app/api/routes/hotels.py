"""
Hotel management routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.dependencies import get_current_active_user, get_hotel_manager, validate_pagination, get_optional_user
from app.schemas.hotel import Hotel as HotelSchema, HotelCreate, HotelUpdate, HotelSearch
from app.models.user import User
from app.repositories.hotel import hotel_repository

router = APIRouter()


@router.get("/", response_model=List[HotelSchema])
async def get_hotels(
    search: HotelSearch = Depends(),
    pagination: dict = Depends(validate_pagination),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get hotels with optional search filters."""
    hotels = hotel_repository.search(
        db=db,
        search_params=search,
        skip=pagination["skip"],
        limit=pagination["limit"]
    )
    return hotels


@router.get("/{hotel_id}", response_model=HotelSchema)
async def get_hotel(
    hotel_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """Get hotel by ID."""
    hotel = hotel_repository.get(db, id=hotel_id)
    if not hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotel not found"
        )
    
    return hotel


@router.post("/", response_model=HotelSchema, status_code=status.HTTP_201_CREATED)
async def create_hotel(
    hotel_data: HotelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hotel_manager)
):
    """Create a new hotel."""
    # Set the manager ID to current user
    hotel_data.manager_id = current_user.id
    
    hotel = hotel_repository.create(db, obj_in=hotel_data)
    return hotel


@router.put("/{hotel_id}", response_model=HotelSchema)
async def update_hotel(
    hotel_id: int,
    hotel_update: HotelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hotel_manager)
):
    """Update hotel."""
    hotel = hotel_repository.get(db, id=hotel_id)
    if not hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotel not found"
        )
    
    # Check if user can manage this hotel
    if hotel.manager_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    hotel = hotel_repository.update(db, db_obj=hotel, obj_in=hotel_update)
    return hotel


@router.delete("/{hotel_id}")
async def delete_hotel(
    hotel_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_hotel_manager)
):
    """Delete hotel."""
    hotel = hotel_repository.get(db, id=hotel_id)
    if not hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotel not found"
        )
    
    # Check if user can manage this hotel
    if hotel.manager_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    hotel_repository.remove(db, id=hotel_id)
    return {"message": "Hotel deleted successfully"}
