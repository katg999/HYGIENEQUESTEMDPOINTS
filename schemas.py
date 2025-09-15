from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# User Schemas
class UserCreate(BaseModel):
    """Schema for creating a new user"""
    phone: str
    name: str
    school: str
    district: str
    language: str

class User(BaseModel):
    """Schema for returning user data (response model)"""
    id: int
    phone: str
    name: str
    school: str
    district: str
    language: str

    class Config:
        from_attributes = True  # Enables ORM mode (previously orm_mode=True)

# Attendance Schemas
class AttendanceCreate(BaseModel):
    """Schema for creating attendance records"""
    phone: str
    students_present: int
    students_absent: int
    absence_reason: str
    subject: str
    district: str

class Attendance(BaseModel):
    """Schema for returning attendance records (response model)"""
    id: int
    phone: str
    students_present: int
    students_absent: int
    absence_reason: str
    subject: str
    district: str


# New schema for attendance with joined user data
class AttendanceWithUser(BaseModel):
    """Schema for attendance records with user information"""
    id: int
    phone: str
    students_present: int
    students_absent: int
    absence_reason: str
    subject: str
    district: str
    teacher_name: str
    school: str


# Add to schemas.py or create new file export_schemas.py
class ExportRequestCreate(BaseModel):
    requester_id: int
    requester_name: str
    requester_phone: str
    data_type: str
    record_count: int
    reason: str
    status: str = "pending"

class ExportRequest(BaseModel):
    id: int
    requester_id: int
    requester_name: str
    requester_phone: str
    data_type: str
    record_count: int
    reason: str
    status: str
    created_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

    class Config:
        from_attributes = True