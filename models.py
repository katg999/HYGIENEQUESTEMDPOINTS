from sqlalchemy import create_engine, Column, Integer, String, Text, Enum, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
import enum
from dotenv import load_dotenv


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")  # Fallback to SQLite for local dev

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


    # Enum for user roles
class UserRole(enum.Enum): 

    SUPERADMIN = "superadmin"
    MANAGER = "manager"
    FIELDWORKER = "fieldworker"


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(15), unique=True, index=True)
    name = Column(String(100))
    school = Column(String(100))
    district = Column(String(100))
    language = Column(String(50))

class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(15), index=True)  
    students_present = Column(Integer)
    students_absent = Column(Integer)
    absence_reason = Column(Text)
    subject = Column(Text)   # renamed from topic_covered
    district = Column(String(100))  # new column added



    # Add to your existing models.py
class LessonPlan(Base):
    __tablename__ = "lesson_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(15), index=True)
    score = Column(Integer)
    subject = Column(String(100))
    feedback = Column(Text)  # Store key feedback points
    image_path = Column(String(255))  # Store path to the uploaded image
    original_filename = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)



class DashboardUser(Base):
    __tablename__ = "dashboard_users"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(15), unique=True, index=True)
    name = Column(String(100))
    role = Column(Enum(UserRole), default=UserRole.FIELDWORKER)
    is_verified = Column(Boolean, default=False)
    otp = Column(String(6), nullable=True)
    otp_expiry = Column(Integer, nullable=True)  # Store as timestamp


class ExportRequest(Base):
    __tablename__ = "export_requests"
    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("dashboard_users.id"))
    requester_name = Column(String(100))
    requester_phone = Column(String(15))
    data_type = Column(String(100))  # e.g., "Attendance Analysis", "User Data"
    record_count = Column(Integer)
    reason = Column(Text)
    status = Column(String(20), default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    
    # Relationship
    requester = relationship("DashboardUser")

# Create tables (run once)
Base.metadata.create_all(bind=engine)