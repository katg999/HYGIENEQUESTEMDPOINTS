import os
import random
import logging
from datetime import datetime, timedelta
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Configuration
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE = os.getenv("TWILIO_PHONE")  # Your +256 Twilio number
OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
MAX_OTP_ATTEMPTS = 3
COUNTRY_CODE = "+256"

# In-memory storage (use Redis in production)
otp_storage = {}

def generate_otp() -> str:
    """Generate 6-digit OTP"""
    return str(random.randint(100000, 999999))

def format_ugandan_phone(phone: str) -> str:
    """
    Convert 10-digit Ugandan number to E.164 format
    Input: '772207616' (10 digits without leading 0)
    Output: '+256772207616'
    """
    # Remove all non-digit characters
    cleaned = ''.join(c for c in phone if c.isdigit())
    
    # Handle 10-digit numbers (without 0)
    if len(cleaned) == 9 and cleaned[0] == '7':  # Ugandan numbers start with 7
        return f"{COUNTRY_CODE}{cleaned}"
    
    # Handle 10-digit numbers (with 0)
    if len(cleaned) == 10 and cleaned.startswith('0'):
        return f"{COUNTRY_CODE}{cleaned[1:]}"
    
    # Return as-is if already formatted
    return cleaned if cleaned.startswith('+') else f"+{cleaned}"

def store_otp(phone: str, otp: str):
    otp_storage[phone] = {
        'otp': otp,
        'expires_at': datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        'attempts': 0,
        'verified': False
    }

def send_otp(phone: str) -> str:
    """Send OTP to Ugandan number"""
    try:
        formatted_phone = format_ugandan_phone(phone)
        
        # Validate phone structure
        if not formatted_phone.startswith("+2567") or len(formatted_phone) != 13:
            raise ValueError("Invalid Ugandan phone format")
        
        otp = generate_otp()
        store_otp(formatted_phone, otp)
        
        client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=f"Your Dettol Hygiene Quest OTP is {otp}. Valid for {OTP_EXPIRY_MINUTES} mins.",
            from_=TWILIO_PHONE,
            to=formatted_phone
        )
        
        logger.info(f"OTP sent to {formatted_phone}")
        return "OTP sent successfully"
    
    except ValueError as e:
        logger.warning(f"Invalid phone {phone}: {str(e)}")
        return "Invalid phone number format"
    except TwilioRestException as e:
        logger.error(f"Twilio error: {str(e)}")
        return f"SMS sending failed: {e.msg}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return "OTP service temporarily unavailable"

def verify_otp(phone: str, user_otp: str) -> bool:
    """Verify user's OTP"""
    formatted_phone = format_ugandan_phone(phone)
    
    if formatted_phone not in otp_storage:
        return False
    
    record = otp_storage[formatted_phone]
    
    # Check expiry
    if datetime.now() > record['expires_at']:
        del otp_storage[formatted_phone]
        return False
    
    # Check attempts
    if record['attempts'] >= MAX_OTP_ATTEMPTS:
        del otp_storage[formatted_phone]
        return False
    
    record['attempts'] += 1
    
    if user_otp == record['otp']:
        record['verified'] = True
        return True
    
    return False

def is_verified(phone: str) -> bool:
    """Check verification status"""
    formatted_phone = format_ugandan_phone(phone)
    return otp_storage.get(formatted_phone, {}).get('verified', False)