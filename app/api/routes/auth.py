from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from app.database import get_db
from app.schemas import Token, UserRead, UserCreate
from app.schemas.users import RegisterRequest, UserClient
from app.schemas.clients import ClientCreate
from app.security import create_access_token
from app.services.user_service import authenticate_user, create_user, get_client_me
from app.services.clients import create_client
from app.dependencies import get_current_user

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """
    Authenticate a user and return an access token.

    - **Request body:** OAuth2PasswordRequestForm (username and password fields)
    - **Authentication:** No authentication required
    - **Response:**
        - access_token: JWT token for authentication
        - token_type: 'bearer'
    - **Raises:**
        - 401 Unauthorized if credentials are invalid
    """
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={'sub': user.email, 'role': user.role})
    return {
        'access_token': access_token,
        'token_type': 'bearer',
    }


@router.post("/register", response_model=UserRead)
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user and create a client profile.

    - **Request body:** RegisterRequest object with user and client details
    - **Authentication:** No authentication required
    - **Response:** UserRead object with the created user's information
    - **Side effects:** Also creates a client profile associated with the user
    """
    user = await create_user(db, UserCreate(
        email=req.email,
        full_name=req.full_name,
        password=req.password,
        role=req.role
    ))
    client = await create_client(db, ClientCreate(
        name=req.name,
        email=req.email,
        phone=req.phone,
        address=req.address
    ), user_id=user.id)
    return user


@router.get('/me', response_model=UserClient)
async def read_user_me(
    db: AsyncSession = Depends(get_db),
    current_user: UserRead = Depends(get_current_user)
):
    """
    Get the current authenticated user's information.

    - **Authentication:** Requires an authenticated user
    - **Response:** UserClient object with the user's details
    """
    return await get_client_me(db=db, current_user=current_user)
