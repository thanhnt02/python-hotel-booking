"""
Security utilities for JWT tokens, password hashing, and authentication.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
import secrets
import string
from app.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password to verify against
    
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plain text password to hash
    
    Returns:
        The hashed password
    """
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: The payload data to encode
        expires_delta: Token expiration time
    
    Returns:
        The encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: The payload data to encode
        expires_delta: Token expiration time
    
    Returns:
        The encoded JWT refresh token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: The JWT token to verify
        token_type: Expected token type ("access" or "refresh")
    
    Returns:
        The decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
            return None
        
        # Check expiration
        exp = payload.get("exp")
        if exp is None or datetime.utcnow() > datetime.fromtimestamp(exp):
            return None
        
        return payload
    except JWTError:
        return None


def generate_password_reset_token() -> str:
    """
    Generate a secure random token for password reset.
    
    Returns:
        A random token string
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))


def generate_verification_token() -> str:
    """
    Generate a secure random token for email verification.
    
    Returns:
        A random token string
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(32))


def create_api_key() -> str:
    """
    Generate a secure API key.
    
    Returns:
        A random API key string
    """
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(64))


def mask_card_number(card_number: str) -> str:
    """
    Mask credit card number, showing only last 4 digits.
    
    Args:
        card_number: The credit card number
    
    Returns:
        Masked card number
    """
    if len(card_number) < 4:
        return "*" * len(card_number)
    return "*" * (len(card_number) - 4) + card_number[-4:]


def validate_card_number(card_number: str) -> bool:
    """
    Basic validation of credit card number using Luhn algorithm.
    
    Args:
        card_number: The credit card number to validate
    
    Returns:
        True if valid, False otherwise
    """
    # Remove spaces and non-digit characters
    card_number = ''.join(filter(str.isdigit, card_number))
    
    # Check length
    if len(card_number) < 13 or len(card_number) > 19:
        return False
    
    # Luhn algorithm
    def luhn_check(card_num):
        def digits_of(n):
            return [int(d) for d in str(n)]
        
        digits = digits_of(card_num)
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        
        for d in even_digits:
            checksum += sum(digits_of(d * 2))
        
        return checksum % 10 == 0
    
    return luhn_check(card_number)


def get_card_brand(card_number: str) -> Optional[str]:
    """
    Determine the credit card brand based on card number.
    
    Args:
        card_number: The credit card number
    
    Returns:
        The card brand name or None if unknown
    """
    # Remove spaces and non-digit characters
    card_number = ''.join(filter(str.isdigit, card_number))
    
    if not card_number:
        return None
    
    # Card brand patterns
    if card_number.startswith('4'):
        return 'visa'
    elif card_number.startswith(('51', '52', '53', '54', '55')) or card_number.startswith(tuple(str(i) for i in range(2221, 2721))):
        return 'mastercard'
    elif card_number.startswith(('34', '37')):
        return 'amex'
    elif card_number.startswith('6011') or card_number.startswith(tuple(str(i) for i in range(622126, 622926))) or card_number.startswith(tuple(str(i) for i in range(644, 650))) or card_number.startswith('65'):
        return 'discover'
    elif card_number.startswith(('300', '301', '302', '303', '304', '305', '36', '38')):
        return 'diners'
    elif card_number.startswith(tuple(str(i) for i in range(3528, 3590))):
        return 'jcb'
    
    return None


class SecurityHeaders:
    """Security headers for HTTP responses."""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """
        Get recommended security headers.
        
        Returns:
            Dictionary of security headers
        """
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
