"""
Password utilities for secure handling
Handles bcrypt password length limitations and consistency
"""

def truncate_password_to_bcrypt_limit(password: str) -> str:
    """
    Truncate password to bcrypt's maximum limit of 72 bytes.
    
    Bcrypt has a hard limit of 72 bytes. Passwords longer than this
    should be truncated to avoid "password cannot be longer than 72 bytes" errors.
    
    Args:
        password: The password string to truncate
        
    Returns:
        Password truncated to maximum 72 bytes
        
    Example:
        >>> long_password = "a" * 100  # 100 character password
        >>> truncated = truncate_password_to_bcrypt_limit(long_password)
        >>> len(truncated.encode('utf-8')) <= 72
        True
    """
    if not password:
        return password
    
    password_bytes = password.encode('utf-8')
    
    # If password is already within limits, return as-is
    if len(password_bytes) <= 72:
        return password
    
    # Truncate to 72 bytes and decode back to string
    # Using errors='replace' to handle any incomplete multi-byte characters
    truncated = password_bytes[:72].decode('utf-8', errors='replace')
    return truncated
