from sqlalchemy.orm import Session
from models import User, Attendance
from schemas import UserCreate, AttendanceCreate

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
