from sqlalchemy import create_engine, Column, Integer, String, Text, Enum, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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



class DashboardUser(Base):
    __tablename__ = "dashboard_users"
    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(15), unique=True, index=True)
    name = Column(String(100))
    role = Column(Enum(UserRole), default=UserRole.FIELDWORKER)
    is_verified = Column(Boolean, default=False)
    otp = Column(String(6), nullable=True)
    otp_expiry = Column(Integer, nullable=True)  # Store as timestamp

# Create tables (run once)
Base.metadata.create_all(bind=engine)