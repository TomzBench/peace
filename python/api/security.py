"""Security utilities for password hashing."""

import hashlib


def hash_password(password: str) -> str:
    """Hash a password using SHA-256.

    Note: This is a simple implementation for demonstration.
    In production, use proper password hashing like bcrypt or argon2.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return hash_password(plain_password) == hashed_password
