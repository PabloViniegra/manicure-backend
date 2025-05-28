from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime


class Cancelation(Base):
    __tablename__ = 'cancelations'

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey(
        'appointments.id', ondelete='CASCADE'), nullable=False)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    appointment = relationship('Appointment', back_populates='cancelation')
