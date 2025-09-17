"""
Hotel model for hotel management.
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Hotel(Base):
    """Hotel model."""
    __tablename__ = "hotels"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False, index=True)
    country = Column(String(100), nullable=False, index=True)
    postal_code = Column(String(20), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Contact information
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(500), nullable=True)
    
    # Hotel details
    star_rating = Column(Integer, nullable=True)  # 1-5 stars
    check_in_time = Column(String(10), default="15:00", nullable=False)
    check_out_time = Column(String(10), default="11:00", nullable=False)
    
    # Amenities (JSON field for flexibility)
    amenities = Column(JSON, nullable=True)  # e.g., ["wifi", "pool", "gym", "spa", "parking"]
    
    # Images
    images = Column(JSON, nullable=True)  # Array of image URLs
    main_image = Column(String(500), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Manager
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    manager = relationship("User", back_populates="managed_hotels")
    rooms = relationship("Room", back_populates="hotel", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="hotel", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Hotel(id={self.id}, name='{self.name}', city='{self.city}')>"
    
    @property
    def average_rating(self):
        """Calculate average rating from reviews."""
        if not self.reviews:
            return 0.0
        return sum(review.rating for review in self.reviews) / len(self.reviews)
    
    @property
    def total_reviews(self):
        """Get total number of reviews."""
        return len(self.reviews)
    
    @property
    def available_rooms_count(self):
        """Get count of available rooms."""
        return len([room for room in self.rooms if room.is_available])
    
    def get_price_range(self):
        """Get price range of rooms."""
        if not self.rooms:
            return {"min": 0, "max": 0}
        
        prices = [room.price_per_night for room in self.rooms if room.is_available]
        if not prices:
            return {"min": 0, "max": 0}
            
        return {"min": min(prices), "max": max(prices)}
