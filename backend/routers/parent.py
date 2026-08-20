from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_role
from ..models import Student, Attendance, Notification, User

router = APIRouter(prefix="/api/parent", tags=["parent"])
parent_only = require_role("Parent")


def _status_badge(checkin, checkout):
    if checkout in ("Present", "Manual Override"):
        return "🚌 Dismissed"
    if checkin in ("Present", "Manual Override"):
        return "🎒 In Class Now"
    return "🏡 Not Arrived Yet"


@router.get("/children")
def children(db: Session = Depends(get_db), user: User = Depends(parent_only)):
    kids = db.query(Student).filter(Student.parent_id == user.id).all()
    today = date.today()
    out = []
    for s in kids:
        recs = db.query(Attendance).filter(
            Attendance.student_id == s.id, Attendance.date == today).all()
        checkin = next((r for r in recs if r.session_type == "Check-In"), None)
        checkout = next((r for r in recs if r.session_type == "Check-Out"), None)
        out.append({
            "id": s.id, "name": s.name, "roll_number": s.roll_number,
            "class_section": s.class_section,
            "checkin_time": checkin.timestamp.strftime("%I:%M %p") if checkin else "-",
            "checkout_time": checkout.timestamp.strftime("%I:%M %p") if checkout else "-",
            "badge": _status_badge(checkin.status if checkin else "Absent",
                                   checkout.status if checkout else "Absent"),
        })
    return out


@router.get("/timeline/{student_id}")
def timeline(student_id: int, db: Session = Depends(get_db),
             user: User = Depends(parent_only)):
    recs = db.query(Attendance).filter(
        Attendance.student_id == student_id).order_by(
        Attendance.timestamp.desc()).limit(60).all()
    return [{"date": r.date.strftime("%d-%m-%Y"),
             "time": r.timestamp.strftime("%I:%M %p"),
             "session": r.session_type, "status": r.status,
             "marked_by": r.marked_by} for r in recs]


@router.get("/notifications")
def notifications(db: Session = Depends(get_db), user: User = Depends(parent_only)):
    notes = db.query(Notification).filter(
        Notification.parent_id == user.id).order_by(
        Notification.timestamp.desc()).limit(50).all()
    return [{"id": n.id, "message": n.message,
             "time": n.timestamp.strftime("%d-%b %I:%M %p"),
             "is_read": n.is_read} for n in notes]


@router.post("/notifications/read")
def mark_read(db: Session = Depends(get_db), user: User = Depends(parent_only)):
    db.query(Notification).filter(
        Notification.parent_id == user.id).update({"is_read": True})
    db.commit()
    return {"message": "marked read"}