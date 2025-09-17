"""
Room model for room management.
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class RoomType(str, enum.Enum):
    """Room types enum."""
    SINGLE = "single"
    DOUBLE = "double"
    TWIN = "twin"
    SUITE = "suite"
    DELUXE = "deluxe"
    PRESIDENTIAL = "presidential"
    FAMILY = "family"


class BedType(str, enum.Enum):
    """Bed types enum."""
    SINGLE = "single"
    DOUBLE = "double"
    QUEEN = "queen"
    KING = "king"
    SOFA_BED = "sofa_bed"


class Room(Base):
    """Room model."""
    __tablename__ = "rooms"
    
    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False, index=True)
    room_number = Column(String(20), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Room details
    room_type = Column(Enum(RoomType), nullable=False)
    bed_type = Column(Enum(BedType), nullable=False)
    max_occupancy = Column(Integer, nullable=False, default=2)
    size_sqm = Column(Float, nullable=True)  # Room size in square meters
    
    # Pricing
    price_per_night = Column(Float, nullable=False)
    weekend_price = Column(Float, nullable=True)  # Special weekend pricing
    
    # Amenities (JSON field for flexibility)
    amenities = Column(JSON, nullable=True)  # e.g., ["wifi", "tv", "minibar", "balcony"]
    
    # Images
    images = Column(JSON, nullable=True)  # Array of image URLs
    main_image = Column(String(500), nullable=True)
    
    # Availability
    is_available = Column(Boolean, default=True, nullable=False)
    is_smoking = Column(Boolean, default=False, nullable=False)
    is_accessible = Column(Boolean, default=False, nullable=False)  # Wheelchair accessible
    
    # Booking rules
    min_nights = Column(Integer, default=1, nullable=False)
    max_nights = Column(Integer, default=30, nullable=False)
    cancellation_hours = Column(Integer, default=24, nullable=False)  # Hours before check-in
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    hotel = relationship("Hotel", back_populates="rooms")
    bookings = relationship("Booking", back_populates="room", cascade="all, delete-orphan")
    availability = relationship("RoomAvailability", back_populates="room", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Room(id={self.id}, number='{self.room_number}', type='{self.room_type}')>"
    
    def is_available_for_dates(self, check_in_date, check_out_date):
        """Check if room is available for given dates."""
        # This would typically check against bookings and availability calendar
        # For now, return the basic availability status
        return self.is_available
    
    def get_price_for_dates(self, check_in_date, check_out_date):
        """Calculate price for given date range."""
        # Basic implementation - would include weekend pricing, seasonal rates, etc.
        from datetime import datetime, timedelta
        
        if not isinstance(check_in_date, datetime):
            return self.price_per_night
            
        total_nights = (check_out_date - check_in_date).days
        if total_nights <= 0:
            return 0
            
        # Check for weekends (simplified)
        base_price = self.price_per_night
        weekend_multiplier = 1.2 if self.weekend_price is None else self.weekend_price / base_price
        
        total_price = 0
        current_date = check_in_date
        
        for _ in range(total_nights):
            if current_date.weekday() >= 5:  # Saturday or Sunday
                total_price += base_price * weekend_multiplier
            else:
                total_price += base_price
            current_date += timedelta(days=1)
            
        return total_price


class RoomAvailability(Base):
    """Room availability calendar."""
    __tablename__ = "room_availability"
    
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    is_available = Column(Boolean, default=True, nullable=False)
    price_override = Column(Float, nullable=True)  # Special pricing for specific dates
    reason = Column(String(255), nullable=True)  # Reason for unavailability
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    room = relationship("Room", back_populates="availability")
    
    def __repr__(self):
        return f"<RoomAvailability(room_id={self.room_id}, date='{self.date}', available={self.is_available})>"
