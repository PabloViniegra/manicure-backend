from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import app.schemas
from app.database import get_db
import app.schemas.clients
import app.schemas.common
from app.services.clients import create_client, get_clients
from app.dependencies import get_current_admin

router = APIRouter()


@router.post("/", response_model=app.schemas.clients.ClientRead)
async def create_client_endpoint(client: app.schemas.clients.ClientCreate, db: AsyncSession = Depends(get_db)):
    """
    Create a new client.

    - **Request body:** ClientCreate object with client details.
    - **Authentication:** No authentication required.
    - **Response:** ClientRead object with the created client's information.
    """
    return await create_client(db, client)


@router.get("/", response_model=app.schemas.common.PaginationResponse[app.schemas.clients.ClientRead])
async def list_clients_endpoints(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    search: str = "",
    current_user: app.schemas.UserRead = Depends(get_current_admin)
):
    """
    Get a paginated list of all clients. Allows searching by client fields.

    - **Query params:**
        - skip: Number of items to skip (pagination, default: 0)
        - limit: Maximum number of items to return (default: 20)
        - search: Text to search in client fields
    - **Authentication:** Requires admin user.
    - **Response:** PaginationResponse[ClientRead] with the list of clients.
    """
    return await get_clients(db, skip=skip, limit=limit, search=search or "")
