from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import app.models
from sqlalchemy import func
import app.schemas
from datetime import datetime, timedelta, timezone
from app.utils import make_naive
import app.schemas.appointments
import app.schemas.common
import app.schemas.users
from app.utils import render_appointment_email
from app.services.notifications import send_notification_email
from app.models.cancelation import Cancelation
from app.schemas.cancelation import CancelationRead
from app.models.appointment import Appointment
from app.utils import make_naive


async def create_appointment(db: AsyncSession, appointment: app.schemas.AppointmentCreate):
    """
    Create a new appointment for a client with selected services.

    - **Parameters:**
        - db: AsyncSession database session
        - appointment: AppointmentCreate object with appointment details
    - **Raises:**
        - 404 if client or any service is not found
        - 400 if no services are selected or time slot is not available
    - **Returns:**
        - The created Appointment model instance
    """
    client = await db.execute(select(app.models.Client).filter_by(id=appointment.client_id))
    if not client.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Client not found")

    if not appointment.service_ids:
        raise HTTPException(
            status_code=400, detail="At least one service must be selected")

    result = await db.execute(select(app.models.Service).filter(app.models.Service.id.in_(appointment.service_ids)))
    services_found = result.scalars().all()
    if len(services_found) != len(appointment.service_ids):
        raise HTTPException(
            status_code=404, detail="One or more services not found")

    total_duration = sum(service.duration for service in services_found)
    appointment_start = make_naive(appointment.date)
    appointment_end = make_naive(
        appointment_start + timedelta(minutes=total_duration))

    q = (
        select(app.models.Appointment)
        .join(app.models.Appointment.services)
        .filter(
            app.models.Appointment.status != "cancelled",
            app.models.Appointment.date < appointment_end,
        )
        .group_by(app.models.Appointment.id)
        .having(
            (app.models.Appointment.date + func.make_interval(
                0, 0, 0, 0, 0, 0, func.sum(app.models.Service.duration*60)
            )) > appointment_start,
            func.count(app.models.Service.id) > 0
        )
    )
    result = await db.execute(q)
    if result.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="This time slot is not available due to another appointment."
        )
    db_appointment = app.models.Appointment(
        client_id=appointment.client_id,
        date=make_naive(appointment.date),
        notes=appointment.notes,
        services=services_found,
    )
    db.add(db_appointment)
    await db.commit()

    html_body = render_appointment_email(
        name=db_appointment.client.name,
        date=db_appointment.date.strftime("%d-%m-%Y %H:%M"),
        services=", ".join([s.name for s in db_appointment.services]),
        link=f"https://tudominio.com/mis-citas"
    )

    send_notification_email(
        email=db_appointment.client.email,
        subject="¡Tu cita ha sido reservada!",
        html_body=html_body,
    )

    result = await db.execute(
        select(app.models.Appointment)
        .options(
            selectinload(app.models.Appointment.client),
            selectinload(app.models.Appointment.services)
        )
        .where(app.models.Appointment.id == db_appointment.id)
    )
    db_appointment = result.scalar_one_or_none()
    return db_appointment


async def get_appointments(db: AsyncSession, skip=0, limit=100, search="") -> app.schemas.common.PaginationResponse[app.schemas.AppointmentRead]:
    """
    Retrieve a paginated list of all appointments, optionally filtered by client name.

    - **Parameters:**
        - db: AsyncSession database session
        - skip: Number of items to skip (pagination)
        - limit: Maximum number of items to return
        - search: Filter by client name (optional)
    - **Returns:**
        - PaginationResponse[AppointmentRead] with appointment data and pagination info
    """
    query = select(app.models.Appointment).options(selectinload(
        app.models.Appointment.client), selectinload(app.models.Appointment.services))
    if search:
        query = query.join(app.models.Client).filter(
            app.models.Client.name.ilike(f"%{search}%"))

    total_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(total_query)

    paginated_query = query.offset(skip).limit(limit)
    result = await db.execute(paginated_query)
    items = result.scalars().all()

    page = (skip // limit) + 1 if limit else 1
    total_pages = (total + limit - 1) // limit if limit else 1
    return app.schemas.common.PaginationResponse[app.schemas.appointments.AppointmentRead](
        info=app.schemas.common.PaginationInfo(
            page=page,
            per_page=limit,
            total=total,
            total_pages=total_pages
        ),
        data=[app.schemas.appointments.AppointmentRead.model_validate(
            item, from_attributes=True) for item in items]
    )


async def get_my_appointments(
    db: AsyncSession,
    client_id: int,
    skip: int = 0,
    limit: int = 100,
    search: str = ""
) -> app.schemas.common.PaginationResponse[app.schemas.appointments.AppointmentRead]:
    """
    Retrieve a paginated list of appointments for a specific client, optionally filtered by notes.

    - **Parameters:**
        - db: AsyncSession database session
        - client_id: ID of the client
        - skip: Number of items to skip (pagination)
        - limit: Maximum number of items to return
        - search: Filter by notes (optional)
    - **Returns:**
        - PaginationResponse[AppointmentRead] with appointment data and pagination info
    """
    query = select(app.models.Appointment).options(
        selectinload(app.models.Appointment.client),
        selectinload(app.models.Appointment.services)
    ).where(app.models.Appointment.client_id == client_id)

    if search:
        query = query.filter(
            app.models.Appointment.notes.ilike(f"%{search}%"))

    total_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(total_query)

    paginated_query = query.offset(skip).limit(limit)
    result = await db.execute(paginated_query)
    items = result.scalars().all()

    page = (skip // limit) + 1 if limit else 1
    total_pages = (total + limit - 1) // limit if limit else 1

    return app.schemas.common.PaginationResponse[app.schemas.appointments.AppointmentRead](
        info=app.schemas.common.PaginationInfo(
            page=page,
            per_page=limit,
            total=total,
            total_pages=total_pages
        ),
        data=[app.schemas.appointments.AppointmentRead.model_validate(
            item, from_attributes=True) for item in items]
    )


async def update_appointment(
    db: AsyncSession,
    appointment_id: int,
    appointment_in: app.schemas.appointments.AppointmentUpdate,
    current_user: app.schemas.users.UserRead
) -> app.schemas.appointments.AppointmentRead:
    """
    Update an existing appointment. Only the admin or the owner client can update.

    - **Parameters:**
        - db: AsyncSession database session
        - appointment_id: ID of the appointment to update
        - appointment_in: AppointmentUpdate object with fields to update
        - current_user: UserRead object of the current user
    - **Raises:**
        - 404 if appointment is not found
        - 403 if user is not authorized
    - **Returns:**
        - AppointmentRead object with updated appointment data
    """
    result = await db.execute(
        select(app.models.Appointment)
        .where(app.models.Appointment.id == appointment_id)
        .options(selectinload(app.models.Appointment.client), selectinload(app.models.Appointment.services))
    )

    appointment = result.scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if not (current_user.role == 'admin' or appointment.client_id == current_user.id):
        raise HTTPException(
            status_code=403, detail="Not authorized to update this appointment")

    for field, value in appointment_in.model_dump(exclude_unset=True).items():
        setattr(appointment, field, value)

    await db.commit()
    await db.refresh(appointment)
    return app.schemas.appointments.AppointmentRead.model_validate(appointment)


async def delete_appointment(
    db: AsyncSession,
    appointment_id: int,
    current_user: app.schemas.users.UserRead
) -> None:
    """
    Delete an existing appointment. Only the admin or the owner client can delete.

    - **Parameters:**
        - db: AsyncSession database session
        - appointment_id: ID of the appointment to delete
        - current_user: UserRead object of the current user
    - **Raises:**
        - 404 if appointment is not found
        - 403 if user is not authorized
    - **Returns:**
        - None
    """
    result = await db.execute(select(app.models.Appointment).where(app.models.Appointment.id == appointment_id))

    appointment = result.scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if not (current_user.role == 'admin' or appointment.client_id == current_user.id):
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this appointment")

    await db.delete(appointment)
    await db.commit()


async def cancel_appointment(
    db: AsyncSession,
    appointment_id: int,
    reason: str,
    current_user: app.schemas.users.UserRead
) -> CancelationRead:
    """
    Cancel an existing appointment with a reason. Only the admin or the owner client can cancel.

    - **Parameters:**
        - db: AsyncSession database session
        - appointment_id: ID of the appointment to cancel
        - reason: Reason for cancellation
        - current_user: UserRead object of the current user
    - **Raises:**
        - 404 if appointment is not found
        - 403 if user is not authorized
    - **Returns:**
        - CancelationRead object with cancellation details
    """
    result = await db.execute(
        select(app.models.Appointment)
        .where(app.models.Appointment.id == appointment_id)
        .options(selectinload(app.models.Appointment.client))
    )

    appointment = result.scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if not (current_user.role == 'admin' or appointment.client_id == current_user.id):
        raise HTTPException(
            status_code=403, detail="Not authorized to cancel this appointment")

    if appointment.status == "cancelled":
        raise HTTPException(
            status_code=400, detail="Appointment is already cancelled")

    now = make_naive(datetime.now())
    if make_naive(appointment.date) - now <= timedelta(hours=3):
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel appointment less than 3 hours before the scheduled time"
        )

    appointment.status = "cancelled"
    cancelation = Cancelation(
        appointment_id=appointment.id,
        reason=reason
    )
    db.add(cancelation)
    await db.commit()
    await db.refresh(cancelation)

    # Update appointment status to cancelled
    appointment.status = "cancelled"
    await db.commit()

    return CancelationRead.model_validate(cancelation, from_attributes=True)


async def complete_appointment(
    db: AsyncSession,
    appointment_id: int
) -> app.schemas.appointments.AppointmentRead:
    """
    Mark an appointment as completed. Only the admin or the staff can complete.
    - **Parameters:**
        - db: AsyncSession database session
        - appointment_id: ID of the appointment to complete
        - current_user: UserRead object of the current user
    - **Raises:**
        - 404 if appointment is not found
        - 403 if user is not authorized
        - 400 if appointment is already completed or cancelled
    - **Returns:**
        - AppointmentRead object with updated appointment data
    """
    result = await db.execute(
        select(app.models.Appointment)
        .options(
            selectinload(app.models.Appointment.client),
            selectinload(app.models.Appointment.services)
        )
        .where(app.models.Appointment.id == appointment_id)
    )

    appointment = result.scalar_one_or_none()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.status == "completed":
        raise HTTPException(
            status_code=400, detail="Appointment is already completed")

    if appointment.status == "cancelled":
        raise HTTPException(
            status_code=400, detail="Cannot complete a cancelled appointment")

    appointment.status = "completed"
    await db.commit()
    await db.refresh(appointment)

    return app.schemas.appointments.AppointmentRead.model_validate(appointment)
