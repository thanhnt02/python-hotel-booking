"""
Hotel schemas for request/response validation.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, validator


class HotelBase(BaseModel):
    """Base hotel schema."""
    name: str
    description: Optional[str] = None
    address: str
    city: str
    country: str
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    star_rating: Optional[int] = None
    check_in_time: str = "15:00"
    check_out_time: str = "11:00"
    amenities: Optional[List[str]] = None
    
    @validator('star_rating')
    def validate_star_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Star rating must be between 1 and 5')
        return v


class HotelCreate(HotelBase):
    """Schema for hotel creation."""
    manager_id: Optional[int] = None


class HotelUpdate(BaseModel):
    """Schema for hotel updates."""
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    star_rating: Optional[int] = None
    check_in_time: Optional[str] = None
    check_out_time: Optional[str] = None
    amenities: Optional[List[str]] = None
    main_image: Optional[str] = None
    images: Optional[List[str]] = None
    is_active: Optional[bool] = None
    
    @validator('star_rating')
    def validate_star_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Star rating must be between 1 and 5')
        return v


class HotelResponse(HotelBase):
    """Schema for hotel response."""
    id: int
    main_image: Optional[str] = None
    images: Optional[List[str]] = None
    is_active: bool
    is_verified: bool
    manager_id: Optional[int] = None
    average_rating: float
    total_reviews: int
    available_rooms_count: int
    price_range: Dict[str, float]
    created_at: datetime
    
    class Config:
        from_attributes = True


class HotelSummary(BaseModel):
    """Schema for hotel summary (used in listings)."""
    id: int
    name: str
    city: str
    country: str
    star_rating: Optional[int] = None
    main_image: Optional[str] = None
    average_rating: float
    total_reviews: int
    available_rooms_count: int
    price_range: Dict[str, float]
    amenities: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class HotelSearch(BaseModel):
    """Schema for hotel search parameters."""
    location: Optional[str] = None  # City, country, or address
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius: Optional[float] = 10.0  # Search radius in km
    check_in_date: Optional[datetime] = None
    check_out_date: Optional[datetime] = None
    guest_count: Optional[int] = 1
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    star_rating: Optional[List[int]] = None
    amenities: Optional[List[str]] = None
    sort_by: Optional[str] = "relevance"  # relevance, price_low, price_high, rating, distance
    page: int = 1
    page_size: int = 20
    
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
    
    @validator('star_rating')
    def validate_star_ratings(cls, v):
        if v is not None:
            for rating in v:
                if rating < 1 or rating > 5:
                    raise ValueError('Star ratings must be between 1 and 5')
        return v


class HotelSearchResponse(BaseModel):
    """Schema for hotel search response."""
    hotels: List[HotelSummary]
    total_count: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class HotelAvailability(BaseModel):
    """Schema for hotel availability check."""
    hotel_id: int
    check_in_date: datetime
    check_out_date: datetime
    guest_count: int = 1
    available_rooms: int
    lowest_price: Optional[float] = None
    
    class Config:
        from_attributes = True
