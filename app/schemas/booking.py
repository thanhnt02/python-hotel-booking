"""
Booking schemas for request/response validation.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, validator
from app.models.booking import BookingStatus, CancellationReason


class BookingBase(BaseModel):
    """Base booking schema."""
    room_id: int
    check_in_date: datetime
    check_out_date: datetime
    guest_count: int = 1
    adult_count: int = 1
    child_count: int = 0
    guest_first_name: str
    guest_last_name: str
    guest_email: str
    guest_phone: Optional[str] = None
    special_requests: Optional[str] = None
    early_check_in: bool = False
    late_check_out: bool = False
    
    @validator('check_out_date')
    def validate_dates(cls, v, values):
        if 'check_in_date' in values and v <= values['check_in_date']:
            raise ValueError('Check-out date must be after check-in date')
        return v
    
    @validator('guest_count')
    def validate_guest_count(cls, v, values):
        adult_count = values.get('adult_count', 1)
        child_count = values.get('child_count', 0)
        if v != adult_count + child_count:
            raise ValueError('Guest count must equal adult count plus child count')
        return v


class BookingCreate(BookingBase):
    """Schema for booking creation."""
    pass


class BookingUpdate(BaseModel):
    """Schema for booking updates."""
    guest_first_name: Optional[str] = None
    guest_last_name: Optional[str] = None
    guest_email: Optional[str] = None
    guest_phone: Optional[str] = None
    special_requests: Optional[str] = None
    early_check_in: Optional[bool] = None
    late_check_out: Optional[bool] = None


class BookingResponse(BookingBase):
    """Schema for booking response."""
    id: int
    booking_reference: str
    user_id: int
    nights: int
    room_rate: float
    total_amount: float
    tax_amount: float
    discount_amount: float
    final_amount: float
    status: BookingStatus
    is_cancelled: bool
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[CancellationReason] = None
    cancellation_note: Optional[str] = None
    actual_check_in: Optional[datetime] = None
    actual_check_out: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Additional computed fields
    is_active: bool
    can_cancel: bool
    is_past_checkout: bool
    days_until_checkin: int
    
    class Config:
        from_attributes = True


class BookingSummary(BaseModel):
    """Schema for booking summary (used in listings)."""
    id: int
    booking_reference: str
    hotel_name: str
    room_name: str
    check_in_date: datetime
    check_out_date: datetime
    nights: int
    guest_count: int
    final_amount: float
    status: BookingStatus
    created_at: datetime
    
    class Config:
        from_attributes = True


class BookingConfirmation(BaseModel):
    """Schema for booking confirmation."""
    booking_id: int
    booking_reference: str
    status: BookingStatus
    confirmation_number: str
    qr_code: Optional[str] = None  # QR code for check-in
    
    class Config:
        from_attributes = True


class BookingCancellation(BaseModel):
    """Schema for booking cancellation."""
    reason: CancellationReason
    note: Optional[str] = None


class BookingCancellationResponse(BaseModel):
    """Schema for booking cancellation response."""
    booking_id: int
    booking_reference: str
    cancelled_at: datetime
    refund_amount: float
    refund_status: str
    
    class Config:
        from_attributes = True


class BookingSearch(BaseModel):
    """Schema for booking search parameters."""
    user_id: Optional[int] = None
    hotel_id: Optional[int] = None
    status: Optional[List[BookingStatus]] = None
    check_in_from: Optional[datetime] = None
    check_in_to: Optional[datetime] = None
    created_from: Optional[datetime] = None
    created_to: Optional[datetime] = None
    page: int = 1
    page_size: int = 20
    sort_by: Optional[str] = "created_at_desc"  # created_at_desc, created_at_asc, check_in_asc, check_in_desc
    
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


class BookingSearchResponse(BaseModel):
    """Schema for booking search response."""
    bookings: List[BookingSummary]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class BookingCheckIn(BaseModel):
    """Schema for booking check-in."""
    booking_id: int
    check_in_time: Optional[datetime] = None
    notes: Optional[str] = None


class BookingCheckOut(BaseModel):
    """Schema for booking check-out."""
    booking_id: int
    check_out_time: Optional[datetime] = None
    notes: Optional[str] = None
    room_condition: Optional[str] = None
