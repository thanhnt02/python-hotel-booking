"""
Review model for hotel and booking reviews.
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Review(Base):
    """Review model."""
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # References
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True, index=True)  # Optional reference to booking
    
    # Review content
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    rating = Column(Float, nullable=False)  # Overall rating (1-5)
    
    # Detailed ratings (1-5 scale)
    cleanliness_rating = Column(Float, nullable=True)
    service_rating = Column(Float, nullable=True)
    location_rating = Column(Float, nullable=True)
    value_rating = Column(Float, nullable=True)
    amenities_rating = Column(Float, nullable=True)
    
    # Recommendations
    would_recommend = Column(Boolean, nullable=True)
    
    # Review metadata
    is_verified = Column(Boolean, default=False, nullable=False)  # Verified if from actual booking
    is_anonymous = Column(Boolean, default=False, nullable=False)
    is_approved = Column(Boolean, default=True, nullable=False)  # For moderation
    
    # Hotel response
    hotel_response = Column(Text, nullable=True)
    hotel_response_date = Column(DateTime, nullable=True)
    
    # Helpful votes
    helpful_count = Column(Integer, default=0, nullable=False)
    not_helpful_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="reviews")
    hotel = relationship("Hotel", back_populates="reviews")
    
    def __repr__(self):
        return f"<Review(id={self.id}, hotel_id={self.hotel_id}, rating={self.rating})>"
    
    @property
    def average_detailed_rating(self):
        """Calculate average of detailed ratings."""
        ratings = [
            self.cleanliness_rating,
            self.service_rating,
            self.location_rating,
            self.value_rating,
            self.amenities_rating
        ]
        valid_ratings = [r for r in ratings if r is not None]
        
        if not valid_ratings:
            return self.rating
        
        return sum(valid_ratings) / len(valid_ratings)
    
    @property
    def helpfulness_score(self):
        """Calculate helpfulness score."""
        total_votes = self.helpful_count + self.not_helpful_count
        if total_votes == 0:
            return 0
        return self.helpful_count / total_votes
    
    def is_recent(self, days=30):
        """Check if review is recent."""
        from datetime import datetime, timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.created_at >= cutoff_date
