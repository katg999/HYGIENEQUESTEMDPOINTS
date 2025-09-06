from pydantic import BaseModel
from typing import Optional

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




    class Config:
        from_attributes = True