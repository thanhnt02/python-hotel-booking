"""
Booking model for reservation management.
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime, timedelta


class BookingStatus(str, enum.Enum):
    """Booking status enum."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class CancellationReason(str, enum.Enum):
    """Cancellation reason enum."""
    USER_REQUESTED = "user_requested"
    PAYMENT_FAILED = "payment_failed"
    HOTEL_UNAVAILABLE = "hotel_unavailable"
    SYSTEM_ERROR = "system_error"
    OTHER = "other"


class Booking(Base):
    """Booking model."""
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_reference = Column(String(20), unique=True, nullable=False, index=True)
    
    # User and Room
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False, index=True)
    
    # Booking dates
    check_in_date = Column(DateTime, nullable=False, index=True)
    check_out_date = Column(DateTime, nullable=False, index=True)
    nights = Column(Integer, nullable=False)
    
    # Guest information
    guest_count = Column(Integer, nullable=False, default=1)
    adult_count = Column(Integer, nullable=False, default=1)
    child_count = Column(Integer, nullable=False, default=0)
    
    # Guest details (for primary guest - could be different from user)
    guest_first_name = Column(String(100), nullable=False)
    guest_last_name = Column(String(100), nullable=False)
    guest_email = Column(String(255), nullable=False)
    guest_phone = Column(String(20), nullable=True)
    
    # Special requests
    special_requests = Column(Text, nullable=True)
    early_check_in = Column(Boolean, default=False, nullable=False)
    late_check_out = Column(Boolean, default=False, nullable=False)
    
    # Pricing
    room_rate = Column(Float, nullable=False)  # Rate per night
    total_amount = Column(Float, nullable=False)
    tax_amount = Column(Float, nullable=False, default=0)
    discount_amount = Column(Float, nullable=False, default=0)
    final_amount = Column(Float, nullable=False)
    
    # Status
    status = Column(Enum(BookingStatus), default=BookingStatus.PENDING, nullable=False, index=True)
    
    # Cancellation
    is_cancelled = Column(Boolean, default=False, nullable=False)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(Enum(CancellationReason), nullable=True)
    cancellation_note = Column(Text, nullable=True)
    
    # Check-in/Check-out
    actual_check_in = Column(DateTime, nullable=True)
    actual_check_out = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="bookings")
    room = relationship("Room", back_populates="bookings")
    payments = relationship("Payment", back_populates="booking", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Booking(id={self.id}, ref='{self.booking_reference}', status='{self.status}')>"
    
    @property
    def is_active(self):
        """Check if booking is active (not cancelled or completed)."""
        return self.status in [BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]
    
    @property
    def can_cancel(self):
        """Check if booking can be cancelled."""
        if self.is_cancelled or self.status in [BookingStatus.CHECKED_OUT, BookingStatus.NO_SHOW]:
            return False
        
        # Check cancellation policy (24 hours before check-in by default)
        cancellation_deadline = self.check_in_date - timedelta(hours=24)
        return datetime.utcnow() < cancellation_deadline
    
    @property
    def is_past_checkout(self):
        """Check if checkout date has passed."""
        return datetime.utcnow() > self.check_out_date
    
    @property
    def days_until_checkin(self):
        """Get days until check-in."""
        delta = self.check_in_date - datetime.utcnow()
        return max(0, delta.days)
    
    def calculate_refund_amount(self):
        """Calculate refund amount based on cancellation policy."""
        if not self.can_cancel:
            return 0
        
        days_until_checkin = self.days_until_checkin
        
        # Simple refund policy - more sophisticated logic could be implemented
        if days_until_checkin >= 7:
            return self.final_amount  # Full refund
        elif days_until_checkin >= 3:
            return self.final_amount * 0.5  # 50% refund
        elif days_until_checkin >= 1:
            return self.final_amount * 0.25  # 25% refund
        else:
            return 0  # No refund
    
    def generate_booking_reference(self):
        """Generate unique booking reference."""
        import random
        import string
        
        # Format: HB-YYYYMMDD-XXXX (Hotel Booking - Date - Random)
        date_str = datetime.utcnow().strftime("%Y%m%d")
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        return f"HB-{date_str}-{random_str}"
