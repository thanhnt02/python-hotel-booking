"""
Payment schemas for request/response validation.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, validator
from app.models.payment import PaymentStatus, PaymentMethod, PaymentType


class PaymentBase(BaseModel):
    """Base payment schema."""
    amount: float
    currency: str = "USD"
    payment_method: PaymentMethod
    payment_type: PaymentType = PaymentType.BOOKING
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v


class PaymentCreate(PaymentBase):
    """Schema for payment creation."""
    booking_id: int
    # Card information (for credit/debit cards)
    card_number: Optional[str] = None
    card_expiry_month: Optional[int] = None
    card_expiry_year: Optional[int] = None
    card_cvv: Optional[str] = None
    card_holder_name: Optional[str] = None
    
    # Billing information
    billing_name: Optional[str] = None
    billing_email: Optional[str] = None
    billing_address: Optional[str] = None
    billing_city: Optional[str] = None
    billing_country: Optional[str] = None
    billing_postal_code: Optional[str] = None
    
    # Additional payment data
    return_url: Optional[str] = None  # For redirect-based payments
    cancel_url: Optional[str] = None
    
    @validator('card_expiry_month')
    def validate_expiry_month(cls, v):
        if v is not None and (v < 1 or v > 12):
            raise ValueError('Expiry month must be between 1 and 12')
        return v
    
    @validator('card_expiry_year')
    def validate_expiry_year(cls, v):
        if v is not None and v < datetime.now().year:
            raise ValueError('Expiry year cannot be in the past')
        return v


class PaymentResponse(PaymentBase):
    """Schema for payment response."""
    id: int
    transaction_id: str
    booking_id: int
    status: PaymentStatus
    gateway: Optional[str] = None
    gateway_transaction_id: Optional[str] = None
    card_last_four: Optional[str] = None
    card_brand: Optional[str] = None
    billing_name: Optional[str] = None
    billing_email: Optional[str] = None
    processed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PaymentSummary(BaseModel):
    """Schema for payment summary."""
    id: int
    transaction_id: str
    amount: float
    currency: str
    payment_method: PaymentMethod
    status: PaymentStatus
    processed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentIntent(BaseModel):
    """Schema for payment intent (used with payment gateways)."""
    payment_id: int
    client_secret: str
    amount: float
    currency: str
    status: str
    
    class Config:
        from_attributes = True


class PaymentConfirmation(BaseModel):
    """Schema for payment confirmation."""
    payment_id: int
    transaction_id: str
    status: PaymentStatus
    amount: float
    processed_at: datetime
    receipt_url: Optional[str] = None
    
    class Config:
        from_attributes = True


class PaymentRefundCreate(BaseModel):
    """Schema for payment refund creation."""
    payment_id: int
    amount: Optional[float] = None  # If None, refund full amount
    reason: Optional[str] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Refund amount must be positive')
        return v


class PaymentRefundResponse(BaseModel):
    """Schema for payment refund response."""
    id: int
    refund_id: str
    original_payment_id: int
    amount: float
    reason: Optional[str] = None
    status: PaymentStatus
    gateway_refund_id: Optional[str] = None
    processed_at: Optional[datetime] = None
    failure_reason: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentWebhook(BaseModel):
    """Schema for payment webhook data."""
    event_type: str
    payment_id: Optional[int] = None
    transaction_id: Optional[str] = None
    gateway_data: Dict[str, Any]
    signature: Optional[str] = None
    timestamp: datetime


class PaymentSearch(BaseModel):
    """Schema for payment search parameters."""
    booking_id: Optional[int] = None
    user_id: Optional[int] = None
    status: Optional[List[PaymentStatus]] = None
    payment_method: Optional[List[PaymentMethod]] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = 1
    page_size: int = 20
    sort_by: Optional[str] = "created_at_desc"
    
    @validator('page')
    def validate_page(cls, v):
        if v < 1:
            raise ValueError('Page must be at least 1')
        return v
    
    @validator('page_size')
    def validate_page_size(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Page size must be between 1 and 100')
        return v


class PaymentSearchResponse(BaseModel):
    """Schema for payment search response."""
    payments: List[PaymentSummary]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
