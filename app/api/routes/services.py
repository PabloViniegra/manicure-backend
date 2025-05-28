from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import app.schemas
from app.database import get_db
import app.schemas.common
from app.services.services import create_service, get_services
from app.dependencies import get_current_admin, get_current_active_user
router = APIRouter()


@router.post('/', response_model=app.schemas.ServiceRead)
async def create_service_endpoint(service: app.schemas.ServiceCreate, db: AsyncSession = Depends(get_db), current_user: app.schemas.UserRead = Depends(get_current_admin)):
    """
    Create a new service.

    - **Request body:** ServiceCreate object with service details.
    - **Authentication:** Requires admin user.
    - **Response:** ServiceRead object with the created service's information.
    """
    return await create_service(db, service)


@router.get('/', response_model=app.schemas.common.PaginationResponse[app.schemas.ServiceRead])
async def get_services_endpoint(
    skip: int = 0,
    limit: int = 20,
    search: Optional[str] = Query(
        None, description="Search for services by name or description"),
    db: AsyncSession = Depends(get_db),
    current_user: app.schemas.UserRead = Depends(get_current_active_user)
):
    """
    Get a paginated list of all services. Allows searching by name or description.

    - **Query params:**
        - skip: Number of items to skip (pagination, default: 0)
        - limit: Maximum number of items to return (default: 20)
        - search: Text to search in service name or description
    - **Authentication:** Requires authenticated user.
    - **Response:** PaginationResponse[ServiceRead] with the list of services.
    """
    return await get_services(db, skip=skip, limit=limit, search=search or '')
