"""
Payment management routes.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.dependencies import get_current_active_user, validate_pagination
from app.schemas.payment import Payment as PaymentSchema, PaymentCreate
from app.models.user import User
from app.repositories.payment import payment_repository

router = APIRouter()


@router.get("/", response_model=List[PaymentSchema])
async def get_payments(
    pagination: dict = Depends(validate_pagination),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's payments."""
    payments = payment_repository.get_by_user(
        db=db,
        user_id=current_user.id,
        skip=pagination["skip"],
        limit=pagination["limit"]
    )
    return payments


@router.get("/{payment_id}", response_model=PaymentSchema)
async def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get payment by ID."""
    payment = payment_repository.get(db, id=payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    # Check if user owns this payment via booking
    if payment.booking.user_id != current_user.id and current_user.role.value != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return payment


@router.post("/", response_model=PaymentSchema, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Process a payment."""
    payment = payment_repository.create(db, obj_in=payment_data)
    return payment
