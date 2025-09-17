"""
Review management routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies import get_current_active_user, validate_pagination, get_optional_user
from app.schemas.review import Review as ReviewSchema, ReviewCreate, ReviewUpdate
from app.models.user import User
from app.repositories.review import review_repository

router = APIRouter()


@router.get("/hotel/{hotel_id}", response_model=List[ReviewSchema])
async def get_hotel_reviews(
    hotel_id: int,
    pagination: dict = Depends(validate_pagination),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Get reviews for a hotel."""
    reviews = review_repository.get_by_hotel(
        db=db,
        hotel_id=hotel_id,
        skip=pagination["skip"],
        limit=pagination["limit"]
    )
    return reviews


@router.get("/{review_id}", response_model=ReviewSchema)
async def get_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user)
):
    """Get review by ID."""
    review = review_repository.get(db, id=review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    return review


@router.post("/", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new review."""
    # Set the user ID to current user
    review_data.user_id = current_user.id
    
    review = review_repository.create(db, obj_in=review_data)
    return review


@router.put("/{review_id}", response_model=ReviewSchema)
async def update_review(
    review_id: int,
    review_update: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update review."""
    review = review_repository.get(db, id=review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Check if user owns this review
    if review.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    review = review_repository.update(db, db_obj=review, obj_in=review_update)
    return review


@router.delete("/{review_id}")
async def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete review."""
    review = review_repository.get(db, id=review_id)
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found"
        )
    
    # Check if user owns this review
    if review.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    review_repository.remove(db, id=review_id)
    return {"message": "Review deleted successfully"}
