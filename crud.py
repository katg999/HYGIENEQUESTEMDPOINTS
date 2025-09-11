from sqlalchemy.orm import Session
from models import User, Attendance
from schemas import UserCreate, AttendanceCreate
from models import ExportRequest
from schemas import ExportRequestCreate

def create_user(db: Session, user: UserCreate):
    db_user = db.query(User).filter(User.phone == user.phone).first()
    if db_user:
        raise ValueError("User already exists with this phone number")
    
    new_user = User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def create_attendance(db: Session, attendance: AttendanceCreate):
    db_att = Attendance(**attendance.dict())
    db.add(db_att)
    db.commit()
    db.refresh(db_att)
    return db_att

def get_users(db: Session):
    return db.query(User).all()

def get_attendance(db: Session):
    return db.query(Attendance).all()



def get_user_by_phone(db: Session, phone: str):
    return db.query(User).filter(User.phone == phone).first()




def create_export_request(db: Session, export_request: ExportRequestCreate):
    db_export_request = ExportRequest(**export_request.dict())
    db.add(db_export_request)
    db.commit()
    db.refresh(db_export_request)
    return db_export_request

def get_export_requests(db: Session, skip: int = 0, limit: int = 100):
    return db.query(ExportRequest).order_by(ExportRequest.created_at.desc()).offset(skip).limit(limit).all()

def get_export_request_by_id(db: Session, request_id: int):
    return db.query(ExportRequest).filter(ExportRequest.id == request_id).first()

def update_export_request_status(db: Session, request_id: int, status: str, approved_by: str = None):
    db_request = db.query(ExportRequest).filter(ExportRequest.id == request_id).first()
    if db_request:
        db_request.status = status
        if status == "approved":
            db_request.approved_by = approved_by
            db_request.approved_at = datetime.utcnow()
        db.commit()
        db.refresh(db_request)
    return db_request

def get_user_approved_requests(db: Session, user_id: int):
    return db.query(ExportRequest).filter(
        ExportRequest.requester_id == user_id,
        ExportRequest.status == "approved"
    ).all()