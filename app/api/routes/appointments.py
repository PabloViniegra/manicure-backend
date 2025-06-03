from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import app.schemas
from app.database import get_db
import app.schemas.appointments
import app.schemas.common
import app.schemas.users
from app.services.appointments import create_appointment, get_appointments, get_my_appointments, update_appointment, delete_appointment, cancel_appointment, complete_appointment
from app.dependencies import get_current_active_user, get_current_admin, get_current_staff_or_admin
from sqlalchemy.future import select
from app.schemas.cancelation import CancelationCreate, CancelationRead
from app.models import Appointment
from sqlalchemy.orm import selectinload

router = APIRouter()


@router.post('/', response_model=app.schemas.AppointmentRead)
async def create_appointment_endpoint(
    appointment: app.schemas.AppointmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: app.schemas.UserRead = Depends(get_current_active_user)
):
    """
    Create a new appointment.

    - **Request body:** AppointmentCreate object with appointment details.
    - **Authentication:** Requires an authenticated user (client).
    - **Response:** AppointmentRead object with the created appointment information.
    """
    return await create_appointment(db, appointment)


@router.get('/', response_model=app.schemas.common.PaginationResponse[app.schemas.AppointmentRead])
async def get_appointments_endpoint(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    search: Optional[str] = Query(
        None, description="Search for appointments by title or description"),
    current_user: app.schemas.UserRead = Depends(get_current_admin)
):
    """
    Get a paginated list of all appointments. Allows searching by title or description.

    - **Query params:**
        - skip: Number of items to skip (pagination, default: 0)
        - limit: Maximum number of items to return (default: 20)
        - search: Text to search in title or description
    - **Authentication:** Requires admin user.
    - **Response:** PaginationResponse[AppointmentRead] with the list of appointments.
    """
    return await get_appointments(db, skip=skip, limit=limit, search=search or "")


@router.get('/my', response_model=app.schemas.common.PaginationResponse[app.schemas.AppointmentRead])
async def get_my_appointments_endpoint(
    skip: int = 0,
    limit: int = 100,
    search: str = "",
    db: AsyncSession = Depends(get_db),
    current_user: app.schemas.UserRead = Depends(get_current_active_user)
):
    """
    Get a paginated list of the authenticated user's appointments.

    - **Query params:**
        - skip: Number of items to skip (pagination, default: 0)
        - limit: Maximum number of items to return (default: 100)
        - search: Text to search in the user's appointments
    - **Authentication:** Requires an authenticated user (client).
    - **Response:** PaginationResponse[AppointmentRead] with the user's appointments.
    """
    result = await db.execute(
        select(app.models.Client).where(
            app.models.Client.user_id == current_user.id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return await get_my_appointments(db, client_id=client.id, skip=skip, limit=limit, search=search or "")


@router.patch('/{appointment_id}', response_model=app.schemas.appointments.AppointmentRead)
async def patch_appointment_endpoint(
    appointment_id: int,
    appointment_in: app.schemas.appointments.AppointmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: app.schemas.UserRead = Depends(get_current_active_user)
):
    """
    Partially update an existing appointment.

    - **Path param:** appointment_id (ID of the appointment to update)
    - **Request body:** AppointmentUpdate object with fields to modify
    - **Authentication:** Requires an authenticated user (client).
    - **Response:** AppointmentRead object with the updated information.
    """
    return await update_appointment(db, appointment_id, appointment_in, current_user)


@router.delete('/{appointment_id}', response_model=app.schemas.appointments.AppointmentRead)
async def delete_appointment_endpoint(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: app.schemas.users.UserRead = Depends(get_current_active_user)
):
    """
    Delete an existing appointment.

    - **Path param:** appointment_id (ID of the appointment to delete)
    - **Authentication:** Requires an authenticated user (client).
    - **Response:** AppointmentRead object of the deleted appointment.
    """
    await delete_appointment(db, appointment_id, current_user)


@router.post('/{appointment_id}/cancel', response_model=CancelationRead)
async def cancel_my_appointment_endpoint(
    appointment_id: int,
    body: CancelationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: app.schemas.users.UserRead = Depends(get_current_active_user)
):
    """
    Cancel an existing appointment.
    - **Path param:** appointment_id (ID of the appointment to cancel)
    - **Request body:** CancelationCreate object with the reason for cancellation
    - **Authentication:** Requires an authenticated user (client).
    - **Response:** CancelationRead object with cancellation details.
    """
    return await cancel_appointment(
        db=db,
        appointment_id=appointment_id,
        reason=body.reason,
        current_user=current_user
    )


@router.post('/{appointment_id}/complete', response_model=app.schemas.appointments.AppointmentRead)
async def complete_appointment_endpoint(
    appointment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: app.schemas.users.UserRead = Depends(
        get_current_staff_or_admin)
):
    """
    Mark an appointment as completed.
    - **Path param:** appointment_id (ID of the appointment to complete)
    - **Authentication:** Requires an authenticated staff or admin user.
    - **Response:** AppointmentRead object with the completed appointment information.
    """
    if current_user.role not in ['staff', 'admin']:
        raise HTTPException(
            status_code=403, detail="You do not have permission to complete appointments")
    return await complete_appointment(db, appointment_id)


@router.get('/blocked', response_model=List[app.schemas.appointments.BlockedSlot])
async def get_blocked_slots(db: AsyncSession = Depends(get_db), user: app.models.User = Depends(get_current_active_user)):
    result = await db.execute(
        select(Appointment)
        .options(selectinload(Appointment.services))
        .where(Appointment.status.in_(['pending', 'confirmed']))
        .where(Appointment.client_id != user.id)
    )
    appointments = result.scalars().all()
    blocked_slots = []
    for appt in appointments:
        duration = sum(s.duration for s in appt.services)
        start = appt.date

        if isinstance(start, str):
            start = datetime.fromisoformat(start)
        end = start + timedelta(minutes=duration)
        blocked_slots.append(app.schemas.appointments.BlockedSlot(
            start=start.isoformat(),
            end=end.isoformat()
        ))
    return blocked_slots
