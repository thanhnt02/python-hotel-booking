"""
Repository layer imports and global instances.
"""
from .base import BaseRepository
from .user import UserRepository, user_repository
from .hotel import HotelRepository, hotel_repository
from .booking import BookingRepository, booking_repository

__all__ = [
    "BaseRepository",
    "UserRepository", "user_repository",
    "HotelRepository", "hotel_repository", 
    "BookingRepository", "booking_repository",
]
