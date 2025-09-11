import random
import time
import os
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt
from models import SessionLocal, DashboardUser as DashboardUserModel, UserRole
from dashboard_schemas import (
    PhoneRequest, OTPRequest, DashboardUserCreate, 
    DashboardUser as DashboardUserSchema, LoginRequest, LoginVerifyRequest
)
from otp import send_otp, verify_otp
from auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-key-for-development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="dashboard/login")
# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/send-registration-otp")
async def send_registration_otp(phone_request: PhoneRequest, db: Session = Depends(get_db)):
    """Send OTP for registration"""
    existing_user = db.query(DashboardUserModel).filter(
        DashboardUserModel.phone == phone_request.phone
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User with this phone number already exists")

    result = send_otp(phone_request.phone)
    if "successfully" not in result.lower():
        raise HTTPException(status_code=500, detail=result)

    return {"message": "OTP sent successfully"}

@router.post("/verify-registration-otp")
async def verify_registration_otp(otp_request: OTPRequest, db: Session = Depends(get_db)):
    """Verify OTP for registration"""
    if not verify_otp(otp_request.phone, otp_request.otp):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    return {"verified": True}

# --------------------- User Registration ---------------------
@router.post("/register", response_model=DashboardUserSchema)
async def register_user(user_data: DashboardUserCreate, db: Session = Depends(get_db)):
    """Register a new dashboard user"""
    existing_user = db.query(DashboardUserModel).filter(
        DashboardUserModel.phone == user_data.phone
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this phone number already exists")

    # Convert role string to UserRole Enum
    try:
        user_role = UserRole(user_data.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role provided")

    db_user = DashboardUserModel(
        phone=user_data.phone,
        name=user_data.name,
        role=user_role,
        is_verified=True  # OTP verified
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@router.post("/send-login-otp")
async def send_login_otp(login_request: LoginRequest, db: Session = Depends(get_db)):
    """Send OTP for login"""
    user = db.query(DashboardUserModel).filter(
        DashboardUserModel.phone == login_request.phone
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please register first.")

    result = send_otp(login_request.phone)
    if "successfully" not in result.lower():
        raise HTTPException(status_code=500, detail=result)

    return {"message": "OTP sent successfully"}

@router.post("/login")
async def login(login_verify: LoginVerifyRequest, db: Session = Depends(get_db)):
    """Login user with OTP verification"""
    user = db.query(DashboardUserModel).filter(
        DashboardUserModel.phone == login_verify.phone
    ).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_otp(login_verify.phone, login_verify.otp):
        raise HTTPException(status_code=400, detail="Invalid OTP")

    # Create JWT token with user info
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role.value}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role.value
    }



# Add this endpoint to get dashboard user details
@router.get("/users/{user_id}", response_model=DashboardUserSchema)
def get_dashboard_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get dashboard user details by ID"""
    try:
        user = db.query(DashboardUserModel).filter(DashboardUserModel.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Only allow users to view their own details or superadmins to view anyone
        if current_user["role"] != UserRole.SUPERADMIN and current_user["id"] != user_id:
            raise HTTPException(status_code=403, detail="Cannot access other users' details")
        
        return user
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user details: {str(e)}")