from pydantic import BaseModel

class UserCreate(BaseModel):
    phone: str
    name: str
    school: str
    district: str
    language: str

class AttendanceCreate(BaseModel):
    phone: str
    students_present: int
    students_absent: int
    absence_reason: str
    topic_covered: str
