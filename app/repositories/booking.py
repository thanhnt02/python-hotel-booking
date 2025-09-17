"""
Booking repository for booking-related database operations.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from datetime import datetime, timedelta
from app.models.booking import Booking, BookingStatus
from app.models.user import User
from app.models.hotel import Hotel
from app.models.room import Room
from app.repositories.base import BaseRepository


class BookingRepository(BaseRepository[Booking]):
    """Repository for Booking model."""
    
    def __init__(self):
        super().__init__(Booking)
    
    def get_with_relations(self, db: Session, booking_id: int) -> Optional[Booking]:
        """
        Get booking with related user, room, and hotel data.
        
        Args:
            db: Database session
            booking_id: Booking ID
        
        Returns:
            Booking instance with relations or None if not found
        """
        return db.query(Booking).options(
            joinedload(Booking.user),
            joinedload(Booking.room).joinedload(Room.hotel)
        ).filter(Booking.id == booking_id).first()
    
    def get_by_reference(self, db: Session, *, booking_reference: str) -> Optional[Booking]:
        """
        Get booking by reference number.
        
        Args:
            db: Database session
            booking_reference: Booking reference number
        
        Returns:
            Booking instance or None if not found
        """
        return db.query(Booking).filter(
            Booking.booking_reference == booking_reference
        ).first()
    
    def get_user_bookings(self, db: Session, *, user_id: int, 
                         status: Optional[List[BookingStatus]] = None,
                         skip: int = 0, limit: int = 100) -> List[Booking]:
        """
        Get bookings for a specific user.
        
        Args:
            db: Database session
            user_id: User ID
            status: List of booking statuses to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of user bookings
        """
        query = db.query(Booking).filter(Booking.user_id == user_id)
        
        if status:
            query = query.filter(Booking.status.in_(status))
        
        return query.order_by(Booking.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_hotel_bookings(self, db: Session, *, hotel_id: int,
                          status: Optional[List[BookingStatus]] = None,
                          date_from: Optional[datetime] = None,
                          date_to: Optional[datetime] = None,
                          skip: int = 0, limit: int = 100) -> List[Booking]:
        """
        Get bookings for a specific hotel.
        
        Args:
            db: Database session
            hotel_id: Hotel ID
            status: List of booking statuses to filter by
            date_from: Filter bookings from this date
            date_to: Filter bookings to this date
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of hotel bookings
        """
        query = db.query(Booking).join(Room).filter(Room.hotel_id == hotel_id)
        
        if status:
            query = query.filter(Booking.status.in_(status))
        
        if date_from:
            query = query.filter(Booking.check_in_date >= date_from)
        
        if date_to:
            query = query.filter(Booking.check_out_date <= date_to)
        
        return query.order_by(Booking.created_at.desc()).offset(skip).limit(limit).all()
    
    def get_room_bookings(self, db: Session, *, room_id: int,
                         date_from: Optional[datetime] = None,
                         date_to: Optional[datetime] = None) -> List[Booking]:
        """
        Get bookings for a specific room within a date range.
        
        Args:
            db: Database session
            room_id: Room ID
            date_from: Start date for filtering
            date_to: End date for filtering
        
        Returns:
            List of room bookings
        """
        query = db.query(Booking).filter(
            Booking.room_id == room_id,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN])
        )
        
        if date_from and date_to:
            # Check for date overlaps
            query = query.filter(
                and_(
                    Booking.check_in_date < date_to,
                    Booking.check_out_date > date_from
                )
            )
        
        return query.order_by(Booking.check_in_date).all()
    
    def get_upcoming_checkins(self, db: Session, *, 
                             hotel_id: Optional[int] = None,
                             days_ahead: int = 1) -> List[Booking]:
        """
        Get bookings with upcoming check-ins.
        
        Args:
            db: Database session
            hotel_id: Optional hotel ID to filter by
            days_ahead: Number of days ahead to look for check-ins
        
        Returns:
            List of bookings with upcoming check-ins
        """
        tomorrow = datetime.utcnow() + timedelta(days=days_ahead)
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        query = db.query(Booking).filter(
            Booking.check_in_date.between(today, tomorrow),
            Booking.status == BookingStatus.CONFIRMED
        )
        
        if hotel_id:
            query = query.join(Room).filter(Room.hotel_id == hotel_id)
        
        return query.order_by(Booking.check_in_date).all()
    
    def get_upcoming_checkouts(self, db: Session, *, 
                              hotel_id: Optional[int] = None,
                              days_ahead: int = 1) -> List[Booking]:
        """
        Get bookings with upcoming check-outs.
        
        Args:
            db: Database session
            hotel_id: Optional hotel ID to filter by
            days_ahead: Number of days ahead to look for check-outs
        
        Returns:
            List of bookings with upcoming check-outs
        """
        tomorrow = datetime.utcnow() + timedelta(days=days_ahead)
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        query = db.query(Booking).filter(
            Booking.check_out_date.between(today, tomorrow),
            Booking.status == BookingStatus.CHECKED_IN
        )
        
        if hotel_id:
            query = query.join(Room).filter(Room.hotel_id == hotel_id)
        
        return query.order_by(Booking.check_out_date).all()
    
    def get_overdue_checkouts(self, db: Session, *, hotel_id: Optional[int] = None) -> List[Booking]:
        """
        Get bookings that are overdue for checkout.
        
        Args:
            db: Database session
            hotel_id: Optional hotel ID to filter by
        
        Returns:
            List of overdue bookings
        """
        now = datetime.utcnow()
        
        query = db.query(Booking).filter(
            Booking.check_out_date < now,
            Booking.status == BookingStatus.CHECKED_IN
        )
        
        if hotel_id:
            query = query.join(Room).filter(Room.hotel_id == hotel_id)
        
        return query.order_by(Booking.check_out_date).all()
    
    def check_room_availability(self, db: Session, *, room_id: int,
                               check_in_date: datetime, check_out_date: datetime) -> bool:
        """
        Check if a room is available for given dates.
        
        Args:
            db: Database session
            room_id: Room ID
            check_in_date: Desired check-in date
            check_out_date: Desired check-out date
        
        Returns:
            True if room is available, False otherwise
        """
        conflicting_bookings = db.query(Booking).filter(
            Booking.room_id == room_id,
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.CHECKED_IN]),
            and_(
                Booking.check_in_date < check_out_date,
                Booking.check_out_date > check_in_date
            )
        ).count()
        
        return conflicting_bookings == 0
    
    def cancel_booking(self, db: Session, *, booking_id: int, 
                      cancellation_reason: str, cancellation_note: Optional[str] = None) -> Optional[Booking]:
        """
        Cancel a booking.
        
        Args:
            db: Database session
            booking_id: Booking ID
            cancellation_reason: Reason for cancellation
            cancellation_note: Optional cancellation note
        
        Returns:
            Updated booking instance or None if not found
        """
        booking = self.get(db, booking_id)
        if booking and booking.can_cancel:
            booking.status = BookingStatus.CANCELLED
            booking.is_cancelled = True
            booking.cancelled_at = datetime.utcnow()
            booking.cancellation_reason = cancellation_reason
            booking.cancellation_note = cancellation_note
            
            db.commit()
            db.refresh(booking)
        
        return booking
    
    def check_in_booking(self, db: Session, *, booking_id: int, 
                        check_in_time: Optional[datetime] = None) -> Optional[Booking]:
        """
        Check in a booking.
        
        Args:
            db: Database session
            booking_id: Booking ID
            check_in_time: Actual check-in time (defaults to now)
        
        Returns:
            Updated booking instance or None if not found
        """
        booking = self.get(db, booking_id)
        if booking and booking.status == BookingStatus.CONFIRMED:
            booking.status = BookingStatus.CHECKED_IN
            booking.actual_check_in = check_in_time or datetime.utcnow()
            
            db.commit()
            db.refresh(booking)
        
        return booking
    
    def check_out_booking(self, db: Session, *, booking_id: int,
                         check_out_time: Optional[datetime] = None) -> Optional[Booking]:
        """
        Check out a booking.
        
        Args:
            db: Database session
            booking_id: Booking ID
            check_out_time: Actual check-out time (defaults to now)
        
        Returns:
            Updated booking instance or None if not found
        """
        booking = self.get(db, booking_id)
        if booking and booking.status == BookingStatus.CHECKED_IN:
            booking.status = BookingStatus.CHECKED_OUT
            booking.actual_check_out = check_out_time or datetime.utcnow()
            
            db.commit()
            db.refresh(booking)
        
        return booking
    
    def get_booking_statistics(self, db: Session, *, 
                              hotel_id: Optional[int] = None,
                              date_from: Optional[datetime] = None,
                              date_to: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get booking statistics.
        
        Args:
            db: Database session
            hotel_id: Optional hotel ID to filter by
            date_from: Start date for filtering
            date_to: End date for filtering
        
        Returns:
            Dictionary with booking statistics
        """
        query = db.query(Booking)
        
        if hotel_id:
            query = query.join(Room).filter(Room.hotel_id == hotel_id)
        
        if date_from:
            query = query.filter(Booking.created_at >= date_from)
        
        if date_to:
            query = query.filter(Booking.created_at <= date_to)
        
        total_bookings = query.count()
        
        # Status distribution
        status_stats = db.query(
            Booking.status,
            func.count(Booking.id).label('count')
        ).group_by(Booking.status)
        
        if hotel_id:
            status_stats = status_stats.join(Room).filter(Room.hotel_id == hotel_id)
        
        if date_from:
            status_stats = status_stats.filter(Booking.created_at >= date_from)
        
        if date_to:
            status_stats = status_stats.filter(Booking.created_at <= date_to)
        
        status_distribution = {status.value: count for status, count in status_stats.all()}
        
        # Revenue calculation
        revenue_query = query.filter(Booking.status == BookingStatus.COMPLETED)
        total_revenue = revenue_query.with_entities(
            func.sum(Booking.final_amount)
        ).scalar() or 0
        
        return {
            'total_bookings': total_bookings,
            'status_distribution': status_distribution,
            'total_revenue': float(total_revenue),
            'average_booking_value': float(total_revenue / total_bookings) if total_bookings > 0 else 0
        }


# Global repository instance
booking_repository = BookingRepository()
