"""
Payment model for payment processing and tracking.
"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class PaymentStatus(str, enum.Enum):
    """Payment status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class PaymentMethod(str, enum.Enum):
    """Payment method enum."""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"
    CRYPTO = "crypto"


class PaymentType(str, enum.Enum):
    """Payment type enum."""
    BOOKING = "booking"
    REFUND = "refund"
    PARTIAL_PAYMENT = "partial_payment"
    CANCELLATION_FEE = "cancellation_fee"


class Payment(Base):
    """Payment model."""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Booking reference
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False, index=True)
    
    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    payment_method = Column(Enum(PaymentMethod), nullable=False)
    payment_type = Column(Enum(PaymentType), default=PaymentType.BOOKING, nullable=False)
    
    # Status
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False, index=True)
    
    # Payment gateway information
    gateway = Column(String(50), nullable=True)  # stripe, paypal, square, etc.
    gateway_transaction_id = Column(String(255), nullable=True, index=True)
    gateway_response = Column(JSON, nullable=True)  # Store full gateway response
    
    # Card information (masked for security)
    card_last_four = Column(String(4), nullable=True)
    card_brand = Column(String(20), nullable=True)  # visa, mastercard, amex, etc.
    
    # Billing information
    billing_name = Column(String(255), nullable=True)
    billing_email = Column(String(255), nullable=True)
    billing_address = Column(Text, nullable=True)
    billing_city = Column(String(100), nullable=True)
    billing_country = Column(String(100), nullable=True)
    billing_postal_code = Column(String(20), nullable=True)
    
    # Processing information
    processed_at = Column(DateTime, nullable=True)
    failure_reason = Column(Text, nullable=True)
    refund_reason = Column(Text, nullable=True)
    
    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional payment metadata
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    booking = relationship("Booking", back_populates="payments")
    refunds = relationship("PaymentRefund", back_populates="original_payment", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, transaction_id='{self.transaction_id}', status='{self.status}')>"
    
    @property
    def is_successful(self):
        """Check if payment was successful."""
        return self.status == PaymentStatus.COMPLETED
    
    @property
    def is_refundable(self):
        """Check if payment can be refunded."""
        return (
            self.status == PaymentStatus.COMPLETED and
            self.payment_type == PaymentType.BOOKING
        )
    
    @property
    def total_refunded(self):
        """Get total amount refunded."""
        return sum(refund.amount for refund in self.refunds if refund.status == PaymentStatus.COMPLETED)
    
    @property
    def remaining_refundable(self):
        """Get remaining refundable amount."""
        return max(0, self.amount - self.total_refunded)
    
    def generate_transaction_id(self):
        """Generate unique transaction ID."""
        import uuid
        return f"TXN-{uuid.uuid4().hex[:12].upper()}"


class PaymentRefund(Base):
    """Payment refund model."""
    __tablename__ = "payment_refunds"
    
    id = Column(Integer, primary_key=True, index=True)
    refund_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # Original payment reference
    original_payment_id = Column(Integer, ForeignKey("payments.id"), nullable=False, index=True)
    
    # Refund details
    amount = Column(Float, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    
    # Gateway information
    gateway_refund_id = Column(String(255), nullable=True, index=True)
    gateway_response = Column(JSON, nullable=True)
    
    # Processing information
    processed_at = Column(DateTime, nullable=True)
    failure_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    # Relationships
    original_payment = relationship("Payment", back_populates="refunds")
    
    def __repr__(self):
        return f"<PaymentRefund(id={self.id}, refund_id='{self.refund_id}', amount={self.amount})>"
    
    def generate_refund_id(self):
        """Generate unique refund ID."""
        import uuid
        return f"REF-{uuid.uuid4().hex[:12].upper()}"
