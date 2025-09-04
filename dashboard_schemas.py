from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum

class UserRole(str, Enum):
    SUPERADMIN = "superadmin"
    MANAGER = "manager"
    FIELDWORKER = "fieldworker"

class PhoneRequest(BaseModel):
    phone: str

class OTPRequest(BaseModel):
    phone: str
    otp: str

class DashboardUserCreate(BaseModel):
    phone: str
    name: str
    role: UserRole

class DashboardUser(BaseModel):
    id: int
    phone: str
    name: str
    role: UserRole
    is_verified: bool

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    phone: str

class LoginVerifyRequest(BaseModel):
    phone: str
    otp: str