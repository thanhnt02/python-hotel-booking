"""
User repository for user-related database operations.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.user import User, UserRole
from app.repositories.base import BaseRepository
from app.core.cache import CacheManager


class UserRepository(BaseRepository[User]):
    """Repository for User model."""
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        """
        Get user by email address.
        
        Args:
            db: Database session
            email: User email address
        
        Returns:
            User instance or None if not found
        """
        # Try cache first
        cached_user = CacheManager.get_cached_user(email=email)
        if cached_user:
            return User(**cached_user)
        
        user = db.query(User).filter(User.email == email).first()
        
        # Cache the result
        if user:
            user_data = {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role.value,
                'is_active': user.is_active,
                'is_verified': user.is_verified
            }
            CacheManager.cache_user(user_data)
        
        return user
    
    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            db: Database session
            username: Username
        
        Returns:
            User instance or None if not found
        """
        return db.query(User).filter(User.username == username).first()
    
    def get_by_keycloak_id(self, db: Session, *, keycloak_id: str) -> Optional[User]:
        """
        Get user by Keycloak ID.
        
        Args:
            db: Database session
            keycloak_id: Keycloak user ID
        
        Returns:
            User instance or None if not found
        """
        return db.query(User).filter(User.keycloak_id == keycloak_id).first()
    
    def search_users(self, db: Session, *, query: str, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Search users by email, username, first name, or last name.
        
        Args:
            db: Database session
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of matching users
        """
        search_filter = or_(
            User.email.ilike(f"%{query}%"),
            User.username.ilike(f"%{query}%"),
            User.first_name.ilike(f"%{query}%"),
            User.last_name.ilike(f"%{query}%")
        )
        
        return db.query(User).filter(search_filter).offset(skip).limit(limit).all()
    
    def get_by_role(self, db: Session, *, role: UserRole, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get users by role.
        
        Args:
            db: Database session
            role: User role
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of users with the specified role
        """
        return db.query(User).filter(User.role == role).offset(skip).limit(limit).all()
    
    def get_active_users(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get active users.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of active users
        """
        return db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
    
    def get_verified_users(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get verified users.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
        
        Returns:
            List of verified users
        """
        return db.query(User).filter(User.is_verified == True).offset(skip).limit(limit).all()
    
    def update_last_login(self, db: Session, *, user_id: int) -> Optional[User]:
        """
        Update user's last login timestamp.
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            Updated user instance or None if not found
        """
        from datetime import datetime
        
        user = self.get(db, user_id)
        if user:
            user.last_login = datetime.utcnow()
            db.commit()
            db.refresh(user)
            
            # Invalidate cache
            CacheManager.invalidate_user_cache(user.id, user.email)
        
        return user
    
    def deactivate_user(self, db: Session, *, user_id: int) -> Optional[User]:
        """
        Deactivate a user account.
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            Updated user instance or None if not found
        """
        user = self.get(db, user_id)
        if user:
            user.is_active = False
            db.commit()
            db.refresh(user)
            
            # Invalidate cache
            CacheManager.invalidate_user_cache(user.id, user.email)
        
        return user
    
    def activate_user(self, db: Session, *, user_id: int) -> Optional[User]:
        """
        Activate a user account.
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            Updated user instance or None if not found
        """
        user = self.get(db, user_id)
        if user:
            user.is_active = True
            db.commit()
            db.refresh(user)
            
            # Invalidate cache
            CacheManager.invalidate_user_cache(user.id, user.email)
        
        return user
    
    def verify_user(self, db: Session, *, user_id: int) -> Optional[User]:
        """
        Verify a user account.
        
        Args:
            db: Database session
            user_id: User ID
        
        Returns:
            Updated user instance or None if not found
        """
        user = self.get(db, user_id)
        if user:
            user.is_verified = True
            db.commit()
            db.refresh(user)
            
            # Invalidate cache
            CacheManager.invalidate_user_cache(user.id, user.email)
        
        return user
    
    def change_role(self, db: Session, *, user_id: int, new_role: UserRole) -> Optional[User]:
        """
        Change user role.
        
        Args:
            db: Database session
            user_id: User ID
            new_role: New user role
        
        Returns:
            Updated user instance or None if not found
        """
        user = self.get(db, user_id)
        if user:
            user.role = new_role
            db.commit()
            db.refresh(user)
            
            # Invalidate cache
            CacheManager.invalidate_user_cache(user.id, user.email)
        
        return user
    
    def get_user_stats(self, db: Session) -> dict:
        """
        Get user statistics.
        
        Args:
            db: Database session
        
        Returns:
            Dictionary with user statistics
        """
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        verified_users = db.query(User).filter(User.is_verified == True).count()
        
        role_counts = {}
        for role in UserRole:
            count = db.query(User).filter(User.role == role).count()
            role_counts[role.value] = count
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'verified_users': verified_users,
            'role_distribution': role_counts
        }


# Global repository instance
user_repository = UserRepository()
