from typing import Optional, List
from pydantic import BaseModel, field_validator, computed_field
from datetime import datetime
from app.schemas.clients import ClientRead
from app.schemas.services import ServiceRead


class AppointmentBase(BaseModel):
    client_id: int
    date: datetime
    notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    service_ids: List[int]


class AppointmentRead(AppointmentBase):
    id: int
    client: ClientRead
    services: List[ServiceRead]
    date: datetime
    status: str
    created_at: datetime
    notes: Optional[str] = None

    @computed_field
    @property
    def service_ids(self) -> List[int]:
        return [s.id for s in self.services or []]

    class Config:
        from_attributes = True


class AppointmentUpdate(BaseModel):
    date: Optional[datetime] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    service_ids: Optional[List[int]] = None
    cancelled: Optional[bool] = None

    @field_validator('status')
    @classmethod
    def status_allowed(cls, v):
        allowed = ['pending', 'confirmed', 'completed', 'cancelled']
        if v is not None and v not in allowed:
            raise ValueError(f"Status must be one of {allowed}")
        return v

    class Config:
        from_attributes = True
