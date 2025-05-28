from sqlalchemy import Column, Integer, ForeignKey, Table
from app.database import Base

appointment_services = Table(
    'appointment_services',
    Base.metadata,
    Column('appointment_id', Integer, ForeignKey(
        'appointments.id', ondelete="CASCADE"), primary_key=True),
    Column('service_id', Integer, ForeignKey(
        'services.id', ondelete="CASCADE"), primary_key=True)
)
