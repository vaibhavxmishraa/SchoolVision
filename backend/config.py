import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
DB_PATH = os.path.join(BASE_DIR, "eduvision.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

FRONTEND_DIR = os.path.join(PROJECT_DIR, "frontend")

SECRET_KEY = os.getenv("EDUVISION_SECRET", "tensor-titans-eduvision-secret-2024")
TOKEN_EXPIRE_SECONDS = 60 * 60 * 24  # 24 hours

# Face recognition
FACE_MATCH_TOLERANCE = 0.5

# Session time windows (24h format)
CHECKIN_START = "08:00"
CHECKIN_END = "10:00"
CHECKOUT_START = "15:00"
CHECKOUT_END = "17:00"

# DEMO_MODE=True -> time-window ignore, testing anytime possible
DEMO_MODE = os.getenv("EDUVISION_DEMO", "1") == "1"

# Twilio (env se aayega, warna SMS console me print hoga)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_NUMBER = os.getenv("TWILIO_FROM_NUMBER", "")