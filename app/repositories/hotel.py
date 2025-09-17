"""
Hotel repository for hotel-related database operations.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime
from app.models.hotel import Hotel
from app.repositories.base import BaseRepository


class HotelRepository(BaseRepository[Hotel]):
    """Repository for Hotel model."""
    
    def __init__(self):
        super().__init__(Hotel)
    
    def search_hotels(self, db: Session, *, 
                     location: Optional[str] = None,
                     latitude: Optional[float] = None,
                     longitude: Optional[float] = None,
                     radius: float = 10.0,
                     min_rating: Optional[float] = None,
                     star_rating: Optional[List[int]] = None,
                     amenities: Optional[List[str]] = None,
                     is_active: bool = True,
                     skip: int = 0,
                     limit: int = 100) -> List[Hotel]:
        """
        Search hotels with various filters.
        
        Args:
            db: Database session
            location: City, country, or address search
            latitude: Latitude for location-based search
            longitude: Longitude for location-based search
            radius: Search radius in kilometers
            min_rating: Minimum average rating
            star_rating: List of star ratings to filter by
            amenities: List of required amenities
            is_active: Filter by active status
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of matching hotels
        """
        query = db.query(Hotel).filter(Hotel.is_active == is_active)
        
        # Location-based search
        if location:
            location_filter = or_(
                Hotel.city.ilike(f"%{location}%"),
                Hotel.country.ilike(f"%{location}%"),
                Hotel.address.ilike(f"%{location}%"),
                Hotel.name.ilike(f"%{location}%")
            )
            query = query.filter(location_filter)
        
        # Coordinate-based search (simplified - in production use PostGIS)
        if latitude and longitude:
            # Simple bounding box calculation (not accurate for large distances)
            lat_range = radius / 111.0  # Approximate km per degree latitude
            lng_range = radius / (111.0 * func.cos(func.radians(latitude)))
            
            query = query.filter(
                and_(
                    Hotel.latitude.between(latitude - lat_range, latitude + lat_range),
                    Hotel.longitude.between(longitude - lng_range, longitude + lng_range)
                )
            )
        
        # Star rating filter
        if star_rating:
            query = query.filter(Hotel.star_rating.in_(star_rating))
        
        # Amenities filter (simplified - check if any amenity matches)
        if amenities:
            for amenity in amenities:
                query = query.filter(Hotel.amenities.contains([amenity]))
        
        return query.offset(skip).limit(limit).all()
    
    def get_by_manager(self, db: Session, *, manager_id: int, skip: int = 0, limit: int = 100) -> List[Hotel]:
        """
        Get hotels managed by a specific user.
        
        Args:
            db: Database session
            manager_id: Manager user ID
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of hotels managed by the user
        """
        return db.query(Hotel).filter(
            Hotel.manager_id == manager_id
        ).offset(skip).limit(limit).all()
    
    def get_by_city(self, db: Session, *, city: str, skip: int = 0, limit: int = 100) -> List[Hotel]:
        """
        Get hotels in a specific city.
        
        Args:
            db: Database session
            city: City name
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of hotels in the city
        """
        return db.query(Hotel).filter(
            Hotel.city.ilike(f"%{city}%"),
            Hotel.is_active == True
        ).offset(skip).limit(limit).all()
    
    def get_by_country(self, db: Session, *, country: str, skip: int = 0, limit: int = 100) -> List[Hotel]:
        """
        Get hotels in a specific country.
        
        Args:
            db: Database session
            country: Country name
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of hotels in the country
        """
        return db.query(Hotel).filter(
            Hotel.country.ilike(f"%{country}%"),
            Hotel.is_active == True
        ).offset(skip).limit(limit).all()
    
    def get_by_star_rating(self, db: Session, *, star_rating: int, skip: int = 0, limit: int = 100) -> List[Hotel]:
        """
        Get hotels by star rating.
        
        Args:
            db: Database session
            star_rating: Star rating (1-5)
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of hotels with the specified star rating
        """
        return db.query(Hotel).filter(
            Hotel.star_rating == star_rating,
            Hotel.is_active == True
        ).offset(skip).limit(limit).all()
    
    def get_featured_hotels(self, db: Session, *, limit: int = 10) -> List[Hotel]:
        """
        Get featured hotels (highest rated active hotels).
        
        Args:
            db: Database session
            limit: Maximum number of hotels to return
        
        Returns:
            List of featured hotels
        """
        # This would typically involve calculating average ratings from reviews
        # For now, we'll just return active verified hotels
        return db.query(Hotel).filter(
            Hotel.is_active == True,
            Hotel.is_verified == True
        ).order_by(Hotel.created_at.desc()).limit(limit).all()
    
    def get_recent_hotels(self, db: Session, *, days: int = 30, limit: int = 10) -> List[Hotel]:
        """
        Get recently added hotels.
        
        Args:
            db: Database session
            days: Number of days to look back
            limit: Maximum number of hotels to return
        
        Returns:
            List of recently added hotels
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return db.query(Hotel).filter(
            Hotel.created_at >= cutoff_date,
            Hotel.is_active == True
        ).order_by(Hotel.created_at.desc()).limit(limit).all()
    
    def update_verification_status(self, db: Session, *, hotel_id: int, is_verified: bool) -> Optional[Hotel]:
        """
        Update hotel verification status.
        
        Args:
            db: Database session
            hotel_id: Hotel ID
            is_verified: Verification status
        
        Returns:
            Updated hotel instance or None if not found
        """
        hotel = self.get(db, hotel_id)
        if hotel:
            hotel.is_verified = is_verified
            db.commit()
            db.refresh(hotel)
        
        return hotel
    
    def update_active_status(self, db: Session, *, hotel_id: int, is_active: bool) -> Optional[Hotel]:
        """
        Update hotel active status.
        
        Args:
            db: Database session
            hotel_id: Hotel ID
            is_active: Active status
        
        Returns:
            Updated hotel instance or None if not found
        """
        hotel = self.get(db, hotel_id)
        if hotel:
            hotel.is_active = is_active
            db.commit()
            db.refresh(hotel)
        
        return hotel
    
    def get_hotels_with_stats(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get hotels with additional statistics.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of hotel dictionaries with statistics
        """
        hotels = self.get_multi(db, skip=skip, limit=limit)
        
        result = []
        for hotel in hotels:
            hotel_dict = {
                'id': hotel.id,
                'name': hotel.name,
                'city': hotel.city,
                'country': hotel.country,
                'star_rating': hotel.star_rating,
                'is_active': hotel.is_active,
                'is_verified': hotel.is_verified,
                'room_count': len(hotel.rooms),
                'available_rooms': len([room for room in hotel.rooms if room.is_available]),
                'total_reviews': len(hotel.reviews),
                'average_rating': hotel.average_rating,
                'created_at': hotel.created_at
            }
            result.append(hotel_dict)
        
        return result
    
    def get_hotel_statistics(self, db: Session) -> Dict[str, Any]:
        """
        Get overall hotel statistics.
        
        Args:
            db: Database session
        
        Returns:
            Dictionary with hotel statistics
        """
        total_hotels = db.query(Hotel).count()
        active_hotels = db.query(Hotel).filter(Hotel.is_active == True).count()
        verified_hotels = db.query(Hotel).filter(Hotel.is_verified == True).count()
        
        # City distribution
        city_stats = db.query(
            Hotel.city,
            func.count(Hotel.id).label('count')
        ).filter(Hotel.is_active == True).group_by(Hotel.city).all()
        
        # Star rating distribution
        rating_stats = db.query(
            Hotel.star_rating,
            func.count(Hotel.id).label('count')
        ).filter(Hotel.is_active == True).group_by(Hotel.star_rating).all()
        
        return {
            'total_hotels': total_hotels,
            'active_hotels': active_hotels,
            'verified_hotels': verified_hotels,
            'city_distribution': {city: count for city, count in city_stats},
            'rating_distribution': {rating: count for rating, count in rating_stats if rating}
        }


# Global repository instance
hotel_repository = HotelRepository()
