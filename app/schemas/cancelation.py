from pydantic import BaseModel
from datetime import datetime


class CancelationBase(BaseModel):
    reason: str


class CancelationCreate(CancelationBase):
    pass


class CancelationRead(CancelationBase):
    id: int
    appointment_id: int
    created_at: datetime

    class Config:
        from_attributes = True
