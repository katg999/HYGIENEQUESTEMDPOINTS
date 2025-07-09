import os
import logging
from dotenv import load_dotenv
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Twilio config
TWILIO_SID = os.getenv("TWILIO_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
VERIFY_SERVICE_SID = os.getenv("VERIFY_SERVICE_SID")  # New SID from Verify Service
COUNTRY_CODE = "+256"

# Initialize client
client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

def format_ugandan_phone(phone: str) -> str:
    """
    Formats a local Ugandan phone number to E.164 format.
    Accepts formats like:
    - '0772207616'
    - '772207616'
    - '+256772207616'
    - '256772207616'
    Always returns: '+256772207616'
    """
    # Strip all non-digit characters
    cleaned = ''.join(c for c in phone if c.isdigit())

    # Handle local 10-digit with leading 0 (e.g., 0772...)
    if len(cleaned) == 10 and cleaned.startswith("0"):
        return f"{COUNTRY_CODE}{cleaned[1:]}"

    # Handle 9-digit without leading 0 (e.g., 772...)
    if len(cleaned) == 9 and cleaned.startswith("7"):
        return f"{COUNTRY_CODE}{cleaned}"

    # Handle if they entered 256772... (national format)
    if len(cleaned) == 12 and cleaned.startswith("256"):
        return f"+{cleaned}"

    # Handle already in +256 format
    if len(cleaned) == 12 and cleaned.startswith("256"):
        return f"+{cleaned}"

    if cleaned.startswith("256") and len(cleaned) > 12:
        return f"+{cleaned[:12]}"  # trim extras

    raise ValueError("Unsupported phone number format")


def send_otp(phone: str) -> str:
    """Send OTP using Twilio Verify API"""
    try:
        formatted_phone = format_ugandan_phone(phone)

        # Validate
        if not formatted_phone.startswith("+2567") or len(formatted_phone) != 13:
            raise ValueError("Invalid Ugandan phone format")
        
        verification = client.verify.services(VERIFY_SERVICE_SID).verifications.create(
            to=formatted_phone,
            channel='sms'
        )

        logger.info(f"OTP sent to {formatted_phone}, SID: {verification.sid}")
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
    """Verify OTP using Twilio Verify API"""
    try:
        formatted_phone = format_ugandan_phone(phone)

        check = client.verify.services(VERIFY_SERVICE_SID).verification_checks.create(
            to=formatted_phone,
            code=user_otp
        )

        logger.info(f"Verification check status: {check.status}")
        return check.status == "approved"

    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
        return False
