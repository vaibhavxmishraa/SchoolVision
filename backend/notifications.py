from datetime import datetime
from sqlalchemy.orm import Session
from .models import Notification, User
from . import config

TWILIO_OK = True
try:
    from twilio.rest import Client  # type: ignore
except Exception:
    TWILIO_OK = False


def send_sms(to_number: str, body: str):
    """Send via Twilio if configured, else log to console (self-healing)."""
    if TWILIO_OK and config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN \
            and config.TWILIO_FROM_NUMBER and to_number:
        try:
            client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=body, from_=config.TWILIO_FROM_NUMBER, to=to_number
            )
            print(f"[SMS] ✅ Sent to {to_number}")
            return True
        except Exception as e:
            print(f"[SMS] ❌ Twilio error: {e} | (fallback console) -> {body}")
            return False
    print(f"[SMS-SIMULATED] to={to_number} :: {body}")
    return False


def notify_parent(db: Session, parent_id: int, student_id: int,
                  student_name: str, session_type: str, ts: datetime):
    time_str = ts.strftime("%d-%b-%Y %I:%M %p")
    action = "arrived at school 🎒" if session_type == "Check-In" else "left school 🚌"
    message = f"EduvisionAI: {student_name} has {action} at {time_str}."

    note = Notification(parent_id=parent_id, student_id=student_id,
                        message=message, timestamp=ts, is_read=False)
    db.add(note)
    db.commit()

    parent = db.query(User).filter(User.id == parent_id).first()
    if parent and parent.phone_number:
        send_sms(parent.phone_number, message)
    return note