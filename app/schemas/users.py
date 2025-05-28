from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str
    role: Optional[str] = 'client'  # Default role is 'client'


class UserRead(UserBase):
    id: int
    is_active: bool
    role: str  # 'client', 'staff', 'admin'
    created_at: datetime

    class Config:
        orm_mode = True


class RegisterRequest(BaseModel):
    email: str
    full_name: str
    password: str
    role: Optional[str] = 'client'  # Default role is 'client'
    name: str
    phone: str
    address: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None  # 'client', 'staff', 'admin'
