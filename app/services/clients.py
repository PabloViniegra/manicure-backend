from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import app.models
import app.schemas
import app.schemas.clients
import app.schemas.common
from sqlalchemy import func


async def create_client(db: AsyncSession, client: app.schemas.ClientCreate, user_id: int):
    """
    Create a new client and associate it with a user.

    - **Parameters:**
        - db: AsyncSession database session
        - client: ClientCreate object with client details
        - user_id: ID of the associated user
    - **Raises:**
        - 400 if a client with the same email already exists
    - **Returns:**
        - The created Client model instance
    """
    result = await db.execute(select(app.models.Client).filter_by(email=client.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="Client with this email already exists")
    new_client = app.models.Client(
        user_id=user_id,
        name=client.name,
        email=client.email,
        phone=client.phone,
        address=client.address,
    )
    db.add(new_client)
    await db.commit()
    await db.refresh(new_client)
    return new_client


async def get_clients(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    search: str = ""
) -> app.schemas.common.PaginationResponse[app.schemas.clients.ClientRead]:
    """
    Retrieve a paginated list of clients, optionally filtered by email.

    - **Parameters:**
        - db: AsyncSession database session
        - skip: Number of items to skip (pagination)
        - limit: Maximum number of items to return
        - search: Filter by client email (optional)
    - **Returns:**
        - PaginationResponse[ClientRead] with client data and pagination info
    """
    query = select(app.models.Client)
    if search:
        query = query.where(app.models.Client.email.ilike(f"%{search}%"))

    total = await db.scalar(select(func.count()).select_from(query.subquery()))

    result = await db.execute(query.offset(skip).limit(limit))
    items = result.scalars().all()

    page = (skip // limit) + 1 if limit else 1
    total_pages = (total + limit - 1) // limit if limit else 1

    return app.schemas.common.PaginationResponse[app.schemas.clients.ClientRead](
        info=app.schemas.common.PaginationInfo(
            page=page,
            per_page=limit,
            total=total,
            total_pages=total_pages
        ),
        data=[app.schemas.clients.ClientRead.model_validate(
            item, from_attributes=True) for item in items]
    )
