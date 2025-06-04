from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
import app.models
import app.schemas
import app.schemas.users
from app.security import get_password_hash, verify_password
from app.models.client import Client


async def get_user_by_email(db: AsyncSession, email: str):
    """
    Retrieve a user by their email address.

    - **Parameters:**
        - db: AsyncSession database session
        - email: User's email address
    - **Returns:**
        - User model instance if found, otherwise None
    """
    result = await db.execute(select(app.models.User).filter(app.models.User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: app.schemas.UserCreate):
    """
    Create a new user with a hashed password.

    - **Parameters:**
        - db: AsyncSession database session
        - user: UserCreate object with user details
    - **Raises:**
        - 400 if the email is already registered
    - **Returns:**
        - The created User model instance
    """
    db_user = await get_user_by_email(db, user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    db_user = app.models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        role=user.role
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def authenticate_user(db: AsyncSession, email: str, password: str):
    """
    Authenticate a user by email and password.

    - **Parameters:**
        - db: AsyncSession database session
        - email: User's email address
        - password: Plain text password
    - **Raises:**
        - 401 if credentials are invalid
    - **Returns:**
        - User model instance if authentication is successful
    """
    user = await get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user


async def get_client_me(db: AsyncSession, current_user: app.schemas.users.UserRead):
    """
    Retrieve the client's profile associated with the current user.

    - **Parameters:**
        - db: AsyncSession database session
        - current_user: Authenticated user model instance
    - **Returns:**
        - UserClient object with the user's details
    - **Raises:**
        - 404 if the client profile is not found
    """
    client = await db.execute(
        select(Client).filter(Client.user_id == current_user.id)
    )
    client = client.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client profile not found")

    return app.schemas.users.UserClient(
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        id=current_user.id,
        client_id=client.id
    )
