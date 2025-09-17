"""
Pydantic schemas for the hotel booking application.
"""
from .user import (
    UserBase, UserCreate, UserUpdate, UserResponse, UserLogin,
    UserRegistration, PasswordChange, PasswordReset, PasswordResetConfirm,
    Token, TokenRefresh, UserProfile
)

from .hotel import (
    HotelBase, HotelCreate, HotelUpdate, HotelResponse, HotelSummary,
    HotelSearch, HotelSearchResponse, HotelAvailability
)

from .room import (
    RoomBase, RoomCreate, RoomUpdate, RoomResponse, RoomSummary,
    RoomAvailability, RoomAvailabilityCheck, RoomSearch, RoomSearchResponse
)

from .booking import (
    BookingBase, BookingCreate, BookingUpdate, BookingResponse, BookingSummary,
    BookingConfirmation, BookingCancellation, BookingCancellationResponse,
    BookingSearch, BookingSearchResponse, BookingCheckIn, BookingCheckOut
)

from .payment import (
    PaymentBase, PaymentCreate, PaymentResponse, PaymentSummary,
    PaymentIntent, PaymentConfirmation, PaymentRefundCreate, PaymentRefundResponse,
    PaymentWebhook, PaymentSearch, PaymentSearchResponse
)

__all__ = [
    # User schemas
    "UserBase", "UserCreate", "UserUpdate", "UserResponse", "UserLogin",
    "UserRegistration", "PasswordChange", "PasswordReset", "PasswordResetConfirm",
    "Token", "TokenRefresh", "UserProfile",
    
    # Hotel schemas
    "HotelBase", "HotelCreate", "HotelUpdate", "HotelResponse", "HotelSummary",
    "HotelSearch", "HotelSearchResponse", "HotelAvailability",
    
    # Room schemas
    "RoomBase", "RoomCreate", "RoomUpdate", "RoomResponse", "RoomSummary",
    "RoomAvailability", "RoomAvailabilityCheck", "RoomSearch", "RoomSearchResponse",
    
    # Booking schemas
    "BookingBase", "BookingCreate", "BookingUpdate", "BookingResponse", "BookingSummary",
    "BookingConfirmation", "BookingCancellation", "BookingCancellationResponse",
    "BookingSearch", "BookingSearchResponse", "BookingCheckIn", "BookingCheckOut",
    
    # Payment schemas
    "PaymentBase", "PaymentCreate", "PaymentResponse", "PaymentSummary",
    "PaymentIntent", "PaymentConfirmation", "PaymentRefundCreate", "PaymentRefundResponse",
    "PaymentWebhook", "PaymentSearch", "PaymentSearchResponse",
]
