from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.appointment_services import appointment_services


class Service(Base):
    __tablename__ = 'services'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False, unique=True)
    description = Column(Text, nullable=True)
    duration = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)

    appointments = relationship(
        "Appointment",
        secondary=appointment_services,
        back_populates="services"
    )
