from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
from app.models.appointment_services import appointment_services


class Appointment(Base):
    __tablename__ = 'appointments'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    date = Column(DateTime, nullable=False)
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    notes = Column(Text, nullable=True)
    client = relationship("Client", back_populates="appointments")
    services = relationship(
        "Service",
        secondary=appointment_services,
        back_populates="appointments"
    )
    cancelation = relationship(
        "Cancelation", uselist=False, back_populates="appointment")
