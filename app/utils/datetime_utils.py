"""
Date and time utility functions.
"""
from datetime import datetime, date, timedelta
from typing import Optional, Tuple
import pytz
from zoneinfo import ZoneInfo


def get_utc_now() -> datetime:
    """Get current UTC datetime."""
    return datetime.utcnow()


def get_local_now(timezone: str = "UTC") -> datetime:
    """
    Get current datetime in specified timezone.
    
    Args:
        timezone: Timezone string (e.g., 'US/Eastern', 'Europe/London')
    
    Returns:
        Current datetime in specified timezone
    """
    tz = ZoneInfo(timezone)
    return datetime.now(tz)


def to_utc(dt: datetime, from_timezone: str = "UTC") -> datetime:
    """
    Convert datetime to UTC.
    
    Args:
        dt: Datetime to convert
        from_timezone: Source timezone
    
    Returns:
        UTC datetime
    """
    if dt.tzinfo is None:
        # Localize naive datetime
        tz = ZoneInfo(from_timezone)
        dt = dt.replace(tzinfo=tz)
    
    return dt.astimezone(pytz.UTC)


def from_utc(dt: datetime, to_timezone: str) -> datetime:
    """
    Convert UTC datetime to specified timezone.
    
    Args:
        dt: UTC datetime
        to_timezone: Target timezone
    
    Returns:
        Datetime in target timezone
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)
    
    tz = ZoneInfo(to_timezone)
    return dt.astimezone(tz)


def date_range(start_date: date, end_date: date) -> list[date]:
    """
    Generate list of dates between start and end date (inclusive).
    
    Args:
        start_date: Start date
        end_date: End date
    
    Returns:
        List of dates
    """
    dates = []
    current_date = start_date
    
    while current_date <= end_date:
        dates.append(current_date)
        current_date += timedelta(days=1)
    
    return dates


def calculate_nights(check_in: date, check_out: date) -> int:
    """
    Calculate number of nights between check-in and check-out dates.
    
    Args:
        check_in: Check-in date
        check_out: Check-out date
    
    Returns:
        Number of nights
    
    Raises:
        ValueError: If check-out is before or same as check-in
    """
    if check_out <= check_in:
        raise ValueError("Check-out date must be after check-in date")
    
    return (check_out - check_in).days


def validate_date_range(
    check_in: date, 
    check_out: date,
    min_nights: int = 1,
    max_nights: int = 365
) -> Tuple[bool, Optional[str]]:
    """
    Validate check-in and check-out date range.
    
    Args:
        check_in: Check-in date
        check_out: Check-out date
        min_nights: Minimum number of nights
        max_nights: Maximum number of nights
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Check if check-out is after check-in
        if check_out <= check_in:
            return False, "Check-out date must be after check-in date"
        
        # Check if dates are in the future
        today = date.today()
        if check_in < today:
            return False, "Check-in date cannot be in the past"
        
        # Calculate nights
        nights = calculate_nights(check_in, check_out)
        
        # Check minimum nights
        if nights < min_nights:
            return False, f"Minimum stay is {min_nights} night(s)"
        
        # Check maximum nights
        if nights > max_nights:
            return False, f"Maximum stay is {max_nights} night(s)"
        
        return True, None
        
    except Exception as e:
        return False, f"Invalid date range: {str(e)}"


def is_weekend(date_obj: date) -> bool:
    """
    Check if date is weekend (Saturday or Sunday).
    
    Args:
        date_obj: Date to check
    
    Returns:
        True if weekend, False otherwise
    """
    return date_obj.weekday() >= 5  # Saturday=5, Sunday=6


def get_season(date_obj: date) -> str:
    """
    Get season for a given date (Northern Hemisphere).
    
    Args:
        date_obj: Date to check
    
    Returns:
        Season name ('spring', 'summer', 'autumn', 'winter')
    """
    month = date_obj.month
    day = date_obj.day
    
    if (month == 3 and day >= 20) or month in [4, 5] or (month == 6 and day < 21):
        return "spring"
    elif (month == 6 and day >= 21) or month in [7, 8] or (month == 9 and day < 23):
        return "summer"
    elif (month == 9 and day >= 23) or month in [10, 11] or (month == 12 and day < 21):
        return "autumn"
    else:
        return "winter"


def business_days_between(start_date: date, end_date: date) -> int:
    """
    Calculate number of business days between two dates.
    
    Args:
        start_date: Start date
        end_date: End date
    
    Returns:
        Number of business days
    """
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    
    business_days = 0
    current_date = start_date
    
    while current_date < end_date:
        if current_date.weekday() < 5:  # Monday=0, Friday=4
            business_days += 1
        current_date += timedelta(days=1)
    
    return business_days


def format_duration(start_time: datetime, end_time: datetime) -> str:
    """
    Format duration between two datetimes as human-readable string.
    
    Args:
        start_time: Start datetime
        end_time: End datetime
    
    Returns:
        Formatted duration string
    """
    duration = end_time - start_time
    
    days = duration.days
    hours, remainder = divmod(duration.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
    if seconds and not (days or hours):
        parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
    
    if not parts:
        return "0 seconds"
    
    return ", ".join(parts)


def next_business_day(date_obj: date) -> date:
    """
    Get next business day from given date.
    
    Args:
        date_obj: Starting date
    
    Returns:
        Next business day
    """
    next_day = date_obj + timedelta(days=1)
    
    # Skip weekends
    while next_day.weekday() >= 5:
        next_day += timedelta(days=1)
    
    return next_day


def previous_business_day(date_obj: date) -> date:
    """
    Get previous business day from given date.
    
    Args:
        date_obj: Starting date
    
    Returns:
        Previous business day
    """
    prev_day = date_obj - timedelta(days=1)
    
    # Skip weekends
    while prev_day.weekday() >= 5:
        prev_day -= timedelta(days=1)
    
    return prev_day
