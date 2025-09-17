"""
String and text manipulation utility functions.
"""
import re
import secrets
import string
from typing import Optional, List
from urllib.parse import quote, unquote
import unicodedata


def generate_random_string(length: int = 10, include_digits: bool = True, include_uppercase: bool = True, include_lowercase: bool = True, include_special: bool = False) -> str:
    """
    Generate a random string with specified parameters.
    
    Args:
        length: Length of the string
        include_digits: Include digits (0-9)
        include_uppercase: Include uppercase letters (A-Z)
        include_lowercase: Include lowercase letters (a-z)
        include_special: Include special characters
    
    Returns:
        Random string
    """
    characters = ""
    
    if include_lowercase:
        characters += string.ascii_lowercase
    if include_uppercase:
        characters += string.ascii_uppercase
    if include_digits:
        characters += string.digits
    if include_special:
        characters += "!@#$%^&*"
    
    if not characters:
        raise ValueError("At least one character type must be included")
    
    return ''.join(secrets.choice(characters) for _ in range(length))


def generate_booking_reference() -> str:
    """Generate a unique booking reference code."""
    # Format: 2 letters + 6 digits (e.g., AB123456)
    letters = ''.join(secrets.choice(string.ascii_uppercase) for _ in range(2))
    numbers = ''.join(secrets.choice(string.digits) for _ in range(6))
    return f"{letters}{numbers}"


def generate_verification_token() -> str:
    """Generate a secure verification token."""
    return secrets.token_urlsafe(32)


def slugify(text: str, max_length: Optional[int] = None) -> str:
    """
    Convert text to URL-friendly slug.
    
    Args:
        text: Text to slugify
        max_length: Maximum length of slug
    
    Returns:
        URL-friendly slug
    """
    # Convert to lowercase and remove accents
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = text.lower()
    
    # Replace non-alphanumeric characters with hyphens
    text = re.sub(r'[^a-z0-9]+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    # Truncate if necessary
    if max_length and len(text) > max_length:
        text = text[:max_length].rstrip('-')
    
    return text


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate text to specified length with optional suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncating
    
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    truncated_length = max_length - len(suffix)
    if truncated_length <= 0:
        return suffix[:max_length]
    
    return text[:truncated_length].rstrip() + suffix


def clean_string(text: str, remove_extra_spaces: bool = True, remove_newlines: bool = False) -> str:
    """
    Clean and normalize string.
    
    Args:
        text: Text to clean
        remove_extra_spaces: Remove extra spaces
        remove_newlines: Remove newline characters
    
    Returns:
        Cleaned text
    """
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Remove newlines if requested
    if remove_newlines:
        text = text.replace('\n', ' ').replace('\r', ' ')
    
    # Remove extra spaces if requested
    if remove_extra_spaces:
        text = re.sub(r'\s+', ' ', text)
    
    return text


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid email format, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
    
    Returns:
        True if valid phone format, False otherwise
    """
    # Remove all non-digit characters for validation
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it has 10-15 digits (international format)
    return 10 <= len(digits_only) <= 15


def format_phone(phone: str, country_code: str = "+1") -> str:
    """
    Format phone number with country code.
    
    Args:
        phone: Phone number to format
        country_code: Country code prefix
    
    Returns:
        Formatted phone number
    """
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Add country code if not present
    if not digits_only.startswith(country_code.replace('+', '')):
        return f"{country_code}-{digits_only}"
    
    return f"+{digits_only}"


def extract_keywords(text: str, min_length: int = 3) -> List[str]:
    """
    Extract keywords from text.
    
    Args:
        text: Text to extract keywords from
        min_length: Minimum keyword length
    
    Returns:
        List of unique keywords
    """
    # Convert to lowercase and remove punctuation
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # Split into words and filter by length
    words = [word.strip() for word in text.split() if len(word.strip()) >= min_length]
    
    # Remove duplicates while preserving order
    keywords = list(dict.fromkeys(words))
    
    return keywords


def mask_email(email: str) -> str:
    """
    Mask email address for privacy.
    
    Args:
        email: Email address to mask
    
    Returns:
        Masked email address
    """
    if '@' not in email:
        return email
    
    local, domain = email.split('@', 1)
    
    if len(local) <= 2:
        masked_local = '*' * len(local)
    else:
        masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
    
    return f"{masked_local}@{domain}"


def mask_phone(phone: str) -> str:
    """
    Mask phone number for privacy.
    
    Args:
        phone: Phone number to mask
    
    Returns:
        Masked phone number
    """
    # Keep only the last 4 digits visible
    if len(phone) <= 4:
        return '*' * len(phone)
    
    return '*' * (len(phone) - 4) + phone[-4:]


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system usage.
    
    Args:
        filename: Filename to sanitize
    
    Returns:
        Sanitized filename
    """
    # Remove or replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_length = 255 - len(ext) - 1 if ext else 255
        filename = name[:max_name_length] + ('.' + ext if ext else '')
    
    return filename


def url_encode(text: str) -> str:
    """URL encode text."""
    return quote(text, safe='')


def url_decode(text: str) -> str:
    """URL decode text."""
    return unquote(text)


def camel_to_snake(text: str) -> str:
    """
    Convert camelCase to snake_case.
    
    Args:
        text: camelCase text
    
    Returns:
        snake_case text
    """
    # Insert underscore before uppercase letters (except at the beginning)
    text = re.sub('([a-z0-9])([A-Z])', r'\1_\2', text)
    return text.lower()


def snake_to_camel(text: str, capitalize_first: bool = False) -> str:
    """
    Convert snake_case to camelCase.
    
    Args:
        text: snake_case text
        capitalize_first: Whether to capitalize the first letter
    
    Returns:
        camelCase text
    """
    components = text.split('_')
    if capitalize_first:
        return ''.join(word.capitalize() for word in components)
    else:
        return components[0] + ''.join(word.capitalize() for word in components[1:])


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts using simple character comparison.
    
    Args:
        text1: First text
        text2: Second text
    
    Returns:
        Similarity score between 0.0 and 1.0
    """
    if not text1 or not text2:
        return 0.0
    
    text1, text2 = text1.lower(), text2.lower()
    
    if text1 == text2:
        return 1.0
    
    # Simple character-based similarity
    len1, len2 = len(text1), len(text2)
    max_len = max(len1, len2)
    min_len = min(len1, len2)
    
    # Count matching characters
    matches = sum(c1 == c2 for c1, c2 in zip(text1, text2))
    
    # Calculate similarity score
    similarity = matches / max_len
    
    return similarity
