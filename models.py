from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")  # Fallback to SQLite for local dev

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

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
    topic_covered = Column(Text)

# Create tables (run once)
Base.metadata.create_all(bind=engine)