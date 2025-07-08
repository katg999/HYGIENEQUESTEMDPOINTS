import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")

def send_otp(phone: str) -> str:
    client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
    otp = "123456"  # Use random OTP in production
    try:
        message = client.messages.create(
            body=f"Your Dettol Hygiene Quest OTP is {otp}",
            from_=TWILIO_PHONE,
            to=phone
        )
        return f"OTP sent to {phone}"
    except Exception as e:
        return f"Failed to send OTP(Try Again): {e}"
