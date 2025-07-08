from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from models import SessionLocal, engine, Base
import crud, schemas

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/register")
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db, user)

@app.post("/attendance")
def submit_attendance(data: schemas.AttendanceCreate, db: Session = Depends(get_db)):
    return crud.create_attendance(db, data)

@app.get("/registrations")
def list_users(db: Session = Depends(get_db)):
    return crud.get_users(db)

@app.get("/attendances")
def list_attendance(db: Session = Depends(get_db)):
    return crud.get_attendance(db)
