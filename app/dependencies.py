"""
FastAPI dependencies for dependency injection.
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError

from app.database import get_db
from app.core.security import verify_token
from app.repositories.user import user_repository
from app.models.user import User, UserRole
from app.core.cache import CacheManager
from app.core.logging import security_logger

# Security scheme
security = HTTPBearer()


def get_current_user(
    db: Session = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """
    Get current authenticated user.
    
    Args:
        db: Database session
        credentials: JWT token credentials
    
    Returns:
        Current user instance
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token
        payload = verify_token(credentials.credentials, token_type="access")
        if payload is None:
            raise credentials_exception
        
        # Get user ID from token
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    
    # Get user from database or cache
    user = user_repository.get(db, id=user_id)
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Log authentication
    security_logger.log_authentication(
        user_id=user.id,
        email=user.email,
        success=True
    )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user.
    
    Args:
        current_user: Current user from token
    
    Returns:
        Active user instance
    
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current verified user.
    
    Args:
        current_user: Current active user
    
    Returns:
        Verified user instance
    
    Raises:
        HTTPException: If user is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User not verified"
        )
    return current_user


class RoleChecker:
    """Role-based access control checker."""
    
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles
    
    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        """
        Check if user has required role.
        
        Args:
            current_user: Current active user
        
        Returns:
            User if authorized
        
        Raises:
            HTTPException: If user doesn't have required role
        """
        if current_user.role not in self.allowed_roles:
            security_logger.log_authorization(
                user_id=current_user.id,
                resource="role_check",
                action="access",
                granted=False,
                reason=f"Required roles: {[role.value for role in self.allowed_roles]}, User role: {current_user.role.value}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        
        security_logger.log_authorization(
            user_id=current_user.id,
            resource="role_check",
            action="access",
            granted=True
        )
        
        return current_user


# Role-based dependencies
require_customer = RoleChecker([UserRole.CUSTOMER, UserRole.HOTEL_MANAGER, UserRole.ADMIN])
require_manager = RoleChecker([UserRole.HOTEL_MANAGER, UserRole.ADMIN])
require_admin = RoleChecker([UserRole.ADMIN])


def get_hotel_manager(
    current_user: User = Depends(require_manager)
) -> User:
    """Get current user if they are hotel manager or admin."""
    return current_user


def get_admin_user(
    current_user: User = Depends(require_admin)
) -> User:
    """Get current user if they are admin."""
    return current_user


def get_optional_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """
    Get current user if token is provided, otherwise return None.
    Used for endpoints that work for both authenticated and anonymous users.
    
    Args:
        db: Database session
        credentials: Optional JWT token credentials
    
    Returns:
        User instance if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        payload = verify_token(credentials.credentials, token_type="access")
        if payload is None:
            return None
        
        user_id: int = payload.get("sub")
        if user_id is None:
            return None
        
        user = user_repository.get(db, id=user_id)
        if user and user.is_active:
            return user
        
    except JWTError:
        pass
    
    return None


def validate_pagination(
    page: int = 1,
    page_size: int = 20
) -> dict:
    """
    Validate pagination parameters.
    
    Args:
        page: Page number (1-based)
        page_size: Number of items per page
    
    Returns:
        Dictionary with validated pagination parameters
    
    Raises:
        HTTPException: If parameters are invalid
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page number must be 1 or greater"
        )
    
    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 100"
        )
    
    skip = (page - 1) * page_size
    
    return {
        "page": page,
        "page_size": page_size,
        "skip": skip,
        "limit": page_size
    }
