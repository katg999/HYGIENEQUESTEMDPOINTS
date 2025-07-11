from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from typing import List
import re
from fastapi.middleware.cors import CORSMiddleware
from lessonplan import router as lessonplan_router
from models import SessionLocal, engine, Base
import crud
import schemas
from otp import send_otp, verify_otp

# Create database tables
Base.metadata.create_all(bind=engine)

# FastAPI app configuration
app = FastAPI(
    title="School Attendance API",
    description="API for managing user registration and attendance",
    version="0.1.0"
)

# Dependency for database session
def get_db():
    """Get database session with proper cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Updated PhoneRequest class
class PhoneRequest(BaseModel):
    phone: str = Field(..., min_length=9, max_length=10)
    
    @field_validator('phone')
    def validate_phone(cls, v):
        if not re.match(r'^(0|7)\d{8,9}$', v):
            raise ValueError('Phone must be 9-10 digits starting with 0 or 7')
        return v
    

class OTPRequest(BaseModel):
    phone: str
    otp: str

# User management endpoints
@app.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_user(db, user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"❌ Register Error: {e}")  # Log the actual error
        raise HTTPException(status_code=500, detail=str(e))  # Send real reason back to frontend


@app.get("/registrations", response_model=List[schemas.User])
def list_users(db: Session = Depends(get_db)):
    """Get all registered users."""
    try:
        return crud.get_users(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

# Attendance management endpoints
@app.post("/attendance", response_model=schemas.Attendance, status_code=status.HTTP_201_CREATED)
def submit_attendance(data: schemas.AttendanceCreate, db: Session = Depends(get_db)):
    """Submit attendance record."""
    try:
        return crud.create_attendance(db, data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create attendance record"
        )

@app.get("/attendances", response_model=List[schemas.Attendance])
def list_attendance(db: Session = Depends(get_db)):
    """Get all attendance records."""
    try:
        return crud.get_attendance(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve attendance records"
        )

# OTP management endpoints
@app.post("/send-otp")
def send_otp_endpoint(phone_request: PhoneRequest):
    """Send OTP to the specified phone number."""
    try:
        result = send_otp(phone_request.phone)
        return {"message": result, "success": True}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP"
        )

@app.post("/verify-otp")
def verify_otp_endpoint(otp_request: OTPRequest):
    """Verify OTP for the specified phone number."""
    try:
        if verify_otp(otp_request.phone, otp_request.otp):
            return {"verified": True, "success": True}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify OTP"
        )

# Health check endpoint
@app.get("/health")
def health_check():
    """Health check endpoint to verify API status."""
    return {"status": "healthy", "service": "School Attendance API"}

# Optional: Add API documentation tags for better organization
@app.get("/", include_in_schema=False)
def root():
    """Root endpoint - redirects to API documentation."""
    return {"message": "Welcome to School Attendance API. Visit /docs for API documentation."}


@app.get("/check-registration/{phone}")
def check_registration(phone: str, db: Session = Depends(get_db)):
    """Check if the phone number is already registered."""
    try:
        user = crud.get_user_by_phone(db, phone)
        if user:
            return {
                "registered": True,
                "name": user.name,
                "school": user.school,
                "district": user.district,
                "language": user.language
            }
        else:
            return {"registered": False}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check registration status"
        )





app.include_router(lessonplan_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
