"""
Dependency utilities for authentication and authorization in FastAPI routes.

- Provides functions to get the current user from a JWT token.
- Checks for active users and admin permissions.
- Raises appropriate HTTP exceptions for unauthorized or inactive users.
"""

from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.user import User
from app.schemas.users import TokenData
from app.security import SECRET_KEY, ALGORITHM
from sqlalchemy.future import select

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """
    Retrieve the current user based on the JWT token.

    - **Parameters:**
        - token: JWT access token from the request
        - db: AsyncSession database session
    - **Raises:**
        - 401 if credentials are invalid or user is not found
    - **Returns:**
        - User model instance of the authenticated user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email, role=role)
    except JWTError:
        raise credentials_exception

    result = await db.execute(select(User).filter(User.email == token_data.email))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)):
    """
    Ensure the current user is active.

    - **Parameters:**
        - current_user: User model instance
    - **Raises:**
        - 400 if the user is inactive
    - **Returns:**
        - User model instance if active
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_admin(current_user: User = Depends(get_current_user)):
    """
    Ensure the current user has admin role.

    - **Parameters:**
        - current_user: User model instance
    - **Raises:**
        - 403 if the user does not have admin role
    - **Returns:**
        - User model instance if admin
    """
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user


def admin_required(current_user: User = Depends(get_current_active_user)):
    """
    Ensure the current user is an active admin.

    - **Parameters:**
        - current_user: User model instance
    - **Raises:**
        - 403 if the user is not an admin
    - **Returns:**
        - User model instance if active admin
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")
    return current_user


def get_current_staff_or_admin(current_user: User = Depends(get_current_active_user)):
    """
    Ensure the current user is either a staff member or an admin.

    - **Parameters:**
        - current_user: User model instance
    - **Raises:**
        - 403 if the user is neither a staff member nor an admin
    - **Returns:**
        - User model instance if staff or admin
    """
    if not (current_user.role == 'admin' or current_user.role == 'staff'):
        raise HTTPException(status_code=403, detail="Staff or Admin only")
    return current_user
