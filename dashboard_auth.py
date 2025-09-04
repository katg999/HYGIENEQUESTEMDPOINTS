import random
import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import SessionLocal, DashboardUser as DashboardUserModel, UserRole
from dashboard_schemas import (
    PhoneRequest, OTPRequest, DashboardUserCreate, 
    DashboardUser as DashboardUserSchema, LoginRequest, LoginVerifyRequest
)
from otp import send_otp, verify_otp



router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/send-registration-otp")
async def send_registration_otp(
    phone_request: PhoneRequest, 
    db: Session = Depends(get_db)
):
    """Send OTP for registration"""
    # Check if user already exists
    existing_user = db.query(DashboardUserModel).filter(
        DashboardUserModel.phone == phone_request.phone
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this phone number already exists"
        )
    
    # Send OTP
    result = send_otp(phone_request.phone)
    if "successfully" not in result.lower():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result
        )
    
    return {"message": "OTP sent successfully"}

@router.post("/verify-registration-otp")
async def verify_registration_otp(otp_request: OTPRequest, db: Session = Depends(get_db)):
    """Verify OTP for registration"""
    # Verify OTP
    if not verify_otp(otp_request.phone, otp_request.otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    
    return {"verified": True}

@router.post("/register", response_model=DashboardUserSchema)
async def register_user(user_data: DashboardUserCreate, db: Session = Depends(get_db)):
    """Register a new dashboard user"""
    # Check if user already exists
    existing_user = db.query(DashboardUserSchema).filter(DashboardUserSchema.phone == user_data.phone).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this phone number already exists"
        )
    
    # Create new user
    db_user = DashboardUserSchema(
        phone=user_data.phone,
        name=user_data.name,
        role=user_data.role,
        is_verified=True  # Mark as verified since OTP was verified
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@router.post("/send-login-otp")
async def send_login_otp(login_request: LoginRequest, db: Session = Depends(get_db)):
    """Send OTP for login"""
    # Check if user exists
    user = db.query(DashboardUserSchema).filter(DashboardUserSchema.phone == login_request.phone).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found. Please register first."
        )
    
    # Send OTP
    result = send_otp(login_request.phone)
    if "successfully" not in result.lower():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result
        )
    
    return {"message": "OTP sent successfully"}

@router.post("/login")
async def login(login_verify: LoginVerifyRequest, db: Session = Depends(get_db)):
    """Login user with OTP verification"""
    # Check if user exists
    user = db.query(DashboardUserSchema).filter(DashboardUserSchema.phone == login_verify.phone).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Verify OTP
    if not verify_otp(login_verify.phone, login_verify.otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP"
        )
    
    # Return user data (in a real app, you'd return a JWT token)
    return {
        "id": user.id,
        "phone": user.phone,
        "name": user.name,
        "role": user.role.value
    }