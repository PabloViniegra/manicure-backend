"""
Security utilities for password hashing, verification, and JWT token creation.

- Loads security settings from environment variables.
- Provides functions for password hashing and verification.
- Handles JWT access token creation with expiration.
"""

from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
from dotenv import load_dotenv

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set.")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))

pws_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plan_password, hashed_password):
    """
    Verify a plain password against a hashed password.

    - **Parameters:**
        - plan_password: The plain text password to verify
        - hashed_password: The hashed password to compare against
    - **Returns:**
        - True if the password matches, False otherwise
    """
    return pws_context.verify(plan_password, hashed_password)


def get_password_hash(password):
    """
    Hash a plain password using the configured password context.

    - **Parameters:**
        - password: The plain text password to hash
    - **Returns:**
        - The hashed password string
    """
    return pws_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Create a JWT access token with an expiration time.

    - **Parameters:**
        - data: Dictionary of data to encode in the token
        - expires_delta: Optional timedelta for token expiration
    - **Returns:**
        - Encoded JWT token as a string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
