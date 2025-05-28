from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import app.models
import app.schemas
import app.schemas.common
import app.schemas.services
from sqlalchemy import func


async def create_service(db: AsyncSession, service: app.schemas.ServiceCreate):
    """
    Create a new service.

    - **Parameters:**
        - db: AsyncSession database session
        - service: ServiceCreate object with service details
    - **Raises:**
        - 400 if a service with the same name already exists
    - **Returns:**
        - The created Service model instance
    """
    result = await db.execute(select(app.models.Service).filter_by(name=service.name))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="Service with this name already exists")
    db_service = app.models.Service(**service.dict())
    db.add(db_service)
    await db.commit()
    await db.refresh(db_service)
    return db_service


async def get_services(db: AsyncSession, skip: int = 0, limit: int = 100, search: str = None) -> app.schemas.common.PaginationResponse[app.schemas.services.ServiceRead]:
    """
    Retrieve a paginated list of services, optionally filtered by name.

    - **Parameters:**
        - db: AsyncSession database session
        - skip: Number of items to skip (pagination)
        - limit: Maximum number of items to return
        - search: Filter by service name (optional)
    - **Returns:**
        - PaginationResponse[ServiceRead] with service data and pagination info
    """
    query = select(app.models.Service)
    if search:
        query = query.where(app.models.Service.name.ilike(f"%{search}%"))

    total_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(total_query)

    paginated_query = query.offset(skip).limit(limit)
    result = await db.execute(paginated_query)
    items = result.scalars().all()

    page = (skip // limit) + 1 if limit else 1
    total_pages = (total + limit - 1) // limit if limit else 1
    return app.schemas.common.PaginationResponse[app.schemas.services.ServiceRead](
        info=app.schemas.common.PaginationInfo(
            page=page,
            per_page=limit,
            total=total,
            total_pages=total_pages
        ),
        data=[app.schemas.services.ServiceRead.model_validate(
            item, from_attributes=True) for item in items]
    )
