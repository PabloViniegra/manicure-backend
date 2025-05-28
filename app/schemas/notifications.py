from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime


class NotificationSendRequest(BaseModel):
    to: EmailStr = Field(..., description="Recipient's email address")
    subject: str = Field(..., description="Subject of the email")
    body: str = Field(..., description="HTML Body of the email")


class NotificationSendResponse(BaseModel):
    success: bool
    message: Optional[str] = None
    id: Optional[str] = None


class NotificationDB(BaseModel):
    id: int
    sent_at: datetime
    resend_id: Optional[str] = None
    status: str

    class Config:
        from_attributes = True
