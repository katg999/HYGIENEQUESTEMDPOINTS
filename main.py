from fastapi import FastAPI, Depends, HTTPException, status, APIRouter, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from typing import List
import re
from fastapi.middleware.cors import CORSMiddleware
from lessonplan import router as lessonplan_router
from dashboard_auth import router as dashboard_router
from models import SessionLocal, engine, Base, User, Attendance, UserRole
import crud
from schemas  import LessonPlanCreate
from models import LessonPlan 
from otp import send_otp, verify_otp
from auth import get_current_user
import os
import schemas
from spaces_storage import do_spaces
import logging
import uuid
from datetime import datetime
import boto3



logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Create database tables
Base.metadata.create_all(bind=engine)

# FastAPI app configuration
app = FastAPI(
    title="School Attendance API",
    description="API for managing user registration and attendance",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dettolhygienequest.com", "http://localhost:3000", "https://www.dettolhygienequest.com"],
    allow_credentials=True,  
    allow_methods=["*"],
    allow_headers=["*"],
)



# Dependency for database session
def get_db():
    """Get database session with proper cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


        # Load DigitalOcean Spaces credentials - Use the same names as in Render
DO_SPACES_ACCESS_KEY = os.getenv("DO_SPACES_ACCESS_KEY")
DO_SPACES_SECRET_KEY = os.getenv("DO_SPACES_SECRET_KEY")
DO_SPACES_REGION = os.getenv("DO_SPACES_REGION", "nyc3")
DO_SPACES_BUCKET = os.getenv("DO_SPACES_BUCKET", "hygienequest-lesson-plans")
DO_SPACES_ENDPOINT = f"https://{DO_SPACES_REGION}.digitaloceanspaces.com"

# Initialize S3 client
s3_client = boto3.client(
    "s3",
    endpoint_url=DO_SPACES_ENDPOINT,
    aws_access_key_id=DO_SPACES_ACCESS_KEY,
    aws_secret_access_key=DO_SPACES_SECRET_KEY,
    region_name=DO_SPACES_REGION
)

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
def list_users(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all registered users with role-based masking."""
    try:
        users = crud.get_users(db)
        
        # Apply role-based masking for fieldworkers and managers
        if current_user["role"] in [UserRole.FIELDWORKER, UserRole.MANAGER]:
            for user in users:
                # Mask school name with user ID
                user.school = f"SCH-{user.id:04d}"
                # Mask teacher name with masked identifier
                user.name = f"Teacher-{user.id:04d}"
                # Mask district name with masked identifier
                user.district = f"District-{(user.id % 100):02d}"
                
        return users
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

@app.get("/attendances", response_model=List[dict])
def list_attendance(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all attendance records with role-based masking."""
    try:
        # Join attendance with users table
        results = db.query(Attendance, User).join(User, Attendance.phone == User.phone).all()
        
        attendance_list = []
        for attendance, user in results:
            attendance_data = {
                "id": attendance.id,
                "phone": attendance.phone,
                "students_present": attendance.students_present,
                "students_absent": attendance.students_absent,
                "absence_reason": attendance.absence_reason,
                "subject": attendance.subject,
                "district": attendance.district,  # This comes from Attendance table
                "teacher_name": user.name,        # This comes from User table
                "school": user.school             # This comes from User table
            }
            
            # Role-based masking for fieldworkers and managers
            if current_user["role"] in [UserRole.FIELDWORKER, UserRole.MANAGER]:
                # Mask district from Attendance table
                attendance_data["district"] = f"DIST-{(attendance.id % 100):02d}"
                # Mask teacher name from User table
                attendance_data["teacher_name"] = f"Teacher-{user.id:04d}"
                # Mask school name from User table
                attendance_data["school"] = f"SCH-{user.id:04d}"
                
            attendance_list.append(attendance_data)
        
        return attendance_list
    except Exception as e:
        print(f"Error: {e}")
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



@app.get("/users/{user_id}", response_model=dict)
def get_specific_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific user by ID with role-based masking."""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prepare response data
        response_data = {
            "id": user.id,
            "name": user.name,
            "school": user.school,
            "district": user.district,
            "language": user.language,
            "phone": user.phone
        }
        
        # Role-based masking for fieldworkers
        if current_user["role"] == UserRole.FIELDWORKER:
            response_data["name"] = f"Teacher-{user.id:04d}"
            response_data["school"] = f"SCH-{user.id:04d}"
            response_data["district"] = f"District-{(user.id % 100):02d}"
        
        return response_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user"
        )
    
# Routes for export requests
export_router = APIRouter(prefix="/dashboard/export-requests", tags=["export-requests"])

@export_router.post("/", response_model=schemas.ExportRequest)
def create_export_request(
    export_request: schemas.ExportRequestCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new export request"""
    try:
        # Debug: Print the incoming request
        print(f"Received export request: {export_request.dict()}")
        print(f"Current user: {current_user}")
        
        # Validate required fields
        if not export_request.requester_id:
            raise HTTPException(status_code=422, detail="requester_id is required")
        if not export_request.requester_name:
            raise HTTPException(status_code=422, detail="requester_name is required")
        if not export_request.data_type:
            raise HTTPException(status_code=422, detail="data_type is required")
        if not export_request.reason:
            raise HTTPException(status_code=422, detail="reason is required")
        
        # Verify the requester exists in dashboard_users
        from models import DashboardUser
        requester = db.query(DashboardUser).filter(DashboardUser.id == export_request.requester_id).first()
        
        if not requester:
            raise HTTPException(status_code=404, detail="Requester not found in dashboard users")
        
        # Create the export request
        result = crud.create_export_request(db, export_request)
        print(f"Export request created successfully: {result.id}")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating export request: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create export request: {str(e)}")

@export_router.get("/", response_model=List[schemas.ExportRequest])
def get_all_export_requests(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all export requests (superadmin only)"""
    if current_user["role"] != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Only superadmins can view export requests")
    
    return crud.get_export_requests(db)


@export_router.patch("/{request_id}", response_model=schemas.ExportRequest)
def update_export_request(
    request_id: int,
    update_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update export request status (superadmin only)"""
    # Debug: Print current user structure
    print(f"Current user object: {current_user}")
    print(f"Current user keys: {list(current_user.keys())}")
    
    if current_user["role"] != UserRole.SUPERADMIN:
        raise HTTPException(status_code=403, detail="Only superadmins can update export requests")
    
    request = crud.get_export_request_by_id(db, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Export request not found")
    
    status = update_data.get("status")
    
    if status == "approved":
        # Use a fallback if name is not available
        approved_by = current_user.get("name") or "Super Admin"
        print(f"Using approved_by: {approved_by}")
        return crud.update_export_request_status(
            db, request_id, "approved", approved_by
        )
    elif status == "rejected":
        return crud.update_export_request_status(db, request_id, "rejected")
    
    return request

# Add a new endpoint to get all requests for a user
@export_router.get("/user/{user_id}", response_model=List[schemas.ExportRequest])
def get_user_export_requests(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all export requests for a specific user"""
    if current_user["role"] != UserRole.SUPERADMIN and current_user["id"] != user_id:
        raise HTTPException(status_code=403, detail="Cannot access other users' requests")
    
    return crud.get_user_requests(db, user_id)


#LessonUploadFunctionalityToGoogleCloudSQLAnd

@app.post("/lessonplan/upload")
async def upload_lesson_plan(
    file: UploadFile = File(...),
    phone: str = Form(...),
    score: int = Form(...),
    subject: str = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"📥 Upload attempt: phone={phone}, score={score}, subject={subject}")

        # Read file content
        file_content = await file.read()
        
        # Use your DigitalOcean Spaces utility
        upload_result = do_spaces.upload_file(
            file_content, 
            file.filename,
            content_type=file.content_type
        )
        
        if not upload_result["success"]:
            raise HTTPException(
                status_code=500, 
                detail=f"Upload failed: {upload_result.get('error', 'Unknown error')}"
            )

        logger.info(f"✅ File uploaded: {upload_result['public_url']}")

        # Save to DB
        lesson_plan = LessonPlan(
            phone=phone,
            score=score,
            subject=subject,
            feedback=feedback,
            spaces_file_path=upload_result["file_path"],
            original_filename=file.filename,
            public_url=upload_result["public_url"],
            created_at=datetime.utcnow()
        )
        
        db.add(lesson_plan)
        db.commit()
        db.refresh(lesson_plan)

        return {
            "success": True, 
            "id": lesson_plan.id,
            "image_url": upload_result["public_url"],
            "message": "Lesson plan uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("❌ Upload failed")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
async def upload_lesson_plan(
    file: UploadFile = File(...),
    phone: str = Form(...),
    score: int = Form(...),
    subject: str = Form(...),
    feedback: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"📥 Upload attempt: phone={phone}, score={score}, subject={subject}")

        # Read file content
        file_content = await file.read()
        
        # Use your DigitalOcean Spaces utility
        upload_result = do_spaces.upload_file(
            file_content, 
            file.filename,
            content_type=file.content_type
        )
        
        if not upload_result["success"]:
            raise HTTPException(
                status_code=500, 
                detail=f"Upload failed: {upload_result.get('error', 'Unknown error')}"
            )

        logger.info(f"✅ File uploaded: {upload_result['public_url']}")

        # Save to DB
        lesson_plan = LessonPlan(
            phone=phone,
            score=score,
            subject=subject,
            feedback=feedback,
            spaces_file_path=upload_result["file_path"],
            original_filename=file.filename,
            public_url=upload_result["public_url"],
            created_at=datetime.utcnow()
        )
        
        db.add(lesson_plan)
        db.commit()
        db.refresh(lesson_plan)

        return {
            "success": True, 
            "id": lesson_plan.id,
            "image_url": upload_result["public_url"],
            "message": "Lesson plan uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("❌ Upload failed")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")
    

@app.get("/lessonplan/image/{lesson_plan_id}")
async def get_lesson_plan_image(
    lesson_plan_id: int,
    db: Session = Depends(get_db)
    # Remove: current_user: dict = Depends(get_current_user)
):
    """Get the lesson plan image URL"""
    try:
        lesson_plan = db.query(LessonPlan).filter(LessonPlan.id == lesson_plan_id).first()
        
        if not lesson_plan:
            raise HTTPException(status_code=404, detail="Lesson plan not found")
        
        return {
            "image_url": lesson_plan.public_url,
            "filename": lesson_plan.original_filename
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve lesson plan image: {str(e)}"
        )

@app.delete("/lessonplan/{lesson_plan_id}")
async def delete_lesson_plan(
    lesson_plan_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a lesson plan and its associated file"""
    try:
        if current_user["role"] != UserRole.SUPERADMIN:
            raise HTTPException(status_code=403, detail="Not authorized")
        
        lesson_plan = db.query(LessonPlan).filter(LessonPlan.id == lesson_plan_id).first()
        
        if not lesson_plan:
            raise HTTPException(status_code=404, detail="Lesson plan not found")
        
        # Delete file from Digital Ocean Spaces
        do_spaces.delete_file(lesson_plan.spaces_file_path)
        
        # Delete database record
        db.delete(lesson_plan)
        db.commit()
        
        return {"success": True, "message": "Lesson plan deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete lesson plan: {str(e)}"
        )



# Include routers
app.include_router(export_router)
app.include_router(lessonplan_router)
app.include_router(dashboard_router)

