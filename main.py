from fastapi import FastAPI
from pydantic import BaseModel
from otp import send_otp

app = FastAPI()

class RegistrationData(BaseModel):
    phone: str
    name: str
    school: str
    district: str
    language: str

class AttendanceData(BaseModel):
    phone: str
    students_present: int
    students_absent: int
    absence_reason: str
    topic_covered: str

class OTPRequest(BaseModel):
    phone: str

class OTPVerify(BaseModel):
    phone: str
    otp: str

@app.post("/register")
def register_user(data: RegistrationData):
    # Save to DB (optional)
    return {"message": f"Registered {data.name} successfully"}

@app.post("/attendance")
def submit_attendance(data: AttendanceData):
    return {"message": "Attendance submitted"}

@app.post("/send-otp")
def send_otp_route(data: OTPRequest):
    result = send_otp(data.phone)
    return {"message": result}

@app.post("/verify-otp")
def verify_otp(data: OTPVerify):
    # Dummy check — replace with real verification
    if data.otp == "123456":
        return {"message": "OTP verified"}
    return {"error": "Invalid OTP"}
