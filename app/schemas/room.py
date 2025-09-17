"""
Room schemas for request/response validation.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, validator
from app.models.room import RoomType, BedType


class RoomBase(BaseModel):
    """Base room schema."""
    room_number: str
    name: str
    description: Optional[str] = None
    room_type: RoomType
    bed_type: BedType
    max_occupancy: int = 2
    size_sqm: Optional[float] = None
    price_per_night: float
    weekend_price: Optional[float] = None
    amenities: Optional[List[str]] = None
    is_smoking: bool = False
    is_accessible: bool = False
    min_nights: int = 1
    max_nights: int = 30
    cancellation_hours: int = 24
    
    @validator('price_per_night')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v
    
    @validator('max_occupancy')
    def validate_occupancy(cls, v):
        if v < 1 or v > 10:
            raise ValueError('Max occupancy must be between 1 and 10')
        return v


class RoomCreate(RoomBase):
    """Schema for room creation."""
    hotel_id: int


class RoomUpdate(BaseModel):
    """Schema for room updates."""
    room_number: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    room_type: Optional[RoomType] = None
    bed_type: Optional[BedType] = None
    max_occupancy: Optional[int] = None
    size_sqm: Optional[float] = None
    price_per_night: Optional[float] = None
    weekend_price: Optional[float] = None
    amenities: Optional[List[str]] = None
    main_image: Optional[str] = None
    images: Optional[List[str]] = None
    is_available: Optional[bool] = None
    is_smoking: Optional[bool] = None
    is_accessible: Optional[bool] = None
    min_nights: Optional[int] = None
    max_nights: Optional[int] = None
    cancellation_hours: Optional[int] = None
    
    @validator('price_per_night')
    def validate_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Price must be positive')
        return v
    
    @validator('max_occupancy')
    def validate_occupancy(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError('Max occupancy must be between 1 and 10')
        return v


class RoomResponse(RoomBase):
    """Schema for room response."""
    id: int
    hotel_id: int
    main_image: Optional[str] = None
    images: Optional[List[str]] = None
    is_available: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class RoomSummary(BaseModel):
    """Schema for room summary (used in search results)."""
    id: int
    name: str
    room_type: RoomType
    bed_type: BedType
    max_occupancy: int
    price_per_night: float
    main_image: Optional[str] = None
    amenities: Optional[List[str]] = None
    is_available: bool
    
    class Config:
        from_attributes = True


class RoomAvailability(BaseModel):
    """Schema for room availability."""
    room_id: int
    check_in_date: datetime
    check_out_date: datetime
    is_available: bool
    price: float
    total_price: float
    nights: int
    
    class Config:
        from_attributes = True


class RoomAvailabilityCheck(BaseModel):
    """Schema for checking room availability."""
    room_id: int
    check_in_date: datetime
    check_out_date: datetime
    guest_count: int = 1
    
    @validator('check_out_date')
    def validate_dates(cls, v, values):
        if 'check_in_date' in values and v <= values['check_in_date']:
            raise ValueError('Check-out date must be after check-in date')
        return v


class RoomSearch(BaseModel):
    """Schema for room search parameters."""
    hotel_id: int
    check_in_date: datetime
    check_out_date: datetime
    guest_count: int = 1
    room_type: Optional[List[RoomType]] = None
    bed_type: Optional[List[BedType]] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    amenities: Optional[List[str]] = None
    is_accessible: Optional[bool] = None
    is_smoking: Optional[bool] = None
    sort_by: Optional[str] = "price_low"  # price_low, price_high, occupancy
    
    @validator('check_out_date')
    def validate_dates(cls, v, values):
        if 'check_in_date' in values and v <= values['check_in_date']:
            raise ValueError('Check-out date must be after check-in date')
        return v


class RoomSearchResponse(BaseModel):
    """Schema for room search response."""
    rooms: List[RoomAvailability]
    total_count: int
    check_in_date: datetime
    check_out_date: datetime
    nights: int
