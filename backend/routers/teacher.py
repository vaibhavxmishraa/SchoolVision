from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db
from ..deps import require_role
from ..models import Student, Attendance, User
from ..excel_export import build_report
from ..notifications import notify_parent

router = APIRouter(prefix="/api/teacher", tags=["teacher"])
teacher_only = require_role("Teacher", "Admin")


class ManualMark(BaseModel):
    student_id: int
    session_type: str    # Check-In / Check-Out
    status: str          # Present / Absent / Manual Override


@router.get("/roster")
def roster(class_section: str = None, db: Session = Depends(get_db),
           user: User = Depends(teacher_only)):
    q = db.query(Student)
    if class_section:
        q = q.filter(Student.class_section == class_section)
    today = date.today()
    result = []
    for s in q.all():
        recs = db.query(Attendance).filter(
            Attendance.student_id == s.id, Attendance.date == today).all()
        checkin = next((r.status for r in recs if r.session_type == "Check-In"), "Absent")
        checkout = next((r.status for r in recs if r.session_type == "Check-Out"), "Absent")
        result.append({"id": s.id, "name": s.name, "roll_number": s.roll_number,
                       "class_section": s.class_section,
                       "checkin": checkin, "checkout": checkout})
    return result


@router.post("/mark")
def mark(data: ManualMark, db: Session = Depends(get_db),
         user: User = Depends(teacher_only)):
    student = db.query(Student).filter(Student.id == data.student_id).first()
    if not student:
        raise HTTPException(404, "Student not found")
    today = date.today()
    existing = db.query(Attendance).filter(
        Attendance.student_id == data.student_id, Attendance.date == today,
        Attendance.session_type == data.session_type).first()
    now = datetime.now()
    if existing:
        existing.status = data.status
        existing.marked_by = f"Teacher_{user.full_name}"
        existing.timestamp = now
    else:
        existing = Attendance(student_id=data.student_id, date=today, timestamp=now,
                              session_type=data.session_type, status=data.status,
                              marked_by=f"Teacher_{user.full_name}")
        db.add(existing)
    db.commit()
    if data.status in ("Present", "Manual Override") and student.parent_id:
        notify_parent(db, student.parent_id, student.id, student.name,
                      data.session_type, now)
    return {"message": f"{student.name} marked {data.status} ({data.session_type})"}


@router.get("/logs")
def logs(db: Session = Depends(get_db), user: User = Depends(teacher_only)):
    recs = db.query(Attendance).order_by(Attendance.timestamp.desc()).limit(100).all()
    out = []
    for r in recs:
        out.append({"student": r.student.name if r.student else "?",
                    "roll": r.student.roll_number if r.student else "?",
                    "date": r.date.strftime("%d-%m-%Y"),
                    "time": r.timestamp.strftime("%I:%M %p"),
                    "session": r.session_type, "status": r.status,
                    "marked_by": r.marked_by})
    return out


@router.get("/export")
def export(db: Session = Depends(get_db), user: User = Depends(teacher_only)):
    buf = build_report(db)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=Class_Report.xlsx"})