from datetime import date, datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ..database import get_db
from ..deps import require_role
from ..models import Student, Attendance, User
from ..face_engine import get_encodings_from_image, match_face
from ..notifications import notify_parent
from ..config import (FACE_MATCH_TOLERANCE, DEMO_MODE, CHECKIN_START,
                      CHECKIN_END, CHECKOUT_START, CHECKOUT_END)

router = APIRouter(prefix="/api/attendance", tags=["attendance"])
cctv_access = require_role("Admin")


class RecognizeIn(BaseModel):
    image: str   # base64 data URL


def _current_session():
    now = datetime.now().strftime("%H:%M")
    if DEMO_MODE:
        # Before 12:30 -> Check-In, else Check-Out (easy testing)
        return "Check-In" if now < "12:30" else "Check-Out"
    if CHECKIN_START <= now <= CHECKIN_END:
        return "Check-In"
    if CHECKOUT_START <= now <= CHECKOUT_END:
        return "Check-Out"
    return None


# @router.post("/recognize")
# def recognize(data: RecognizeIn, db: Session = Depends(get_db),
#               _=Depends(cctv_access)):
#     session_type = _current_session()
#     if not session_type:
#         return {"status": "closed",
#                 "message": "Attendance window band hai abhi (session time ke bahar)."}

#     encs = get_encodings_from_image(data.image)
#     if not encs:
#         return {"status": "no_face", "message": "Koi chehra detect nahi hua."}

#     students = [(s.id, s.name, s.face_encodings) for s in db.query(Student).all()]
#     match = match_face(encs[0], students, FACE_MATCH_TOLERANCE)
#     if not match:
#         return {"status": "unknown", "message": "Chehra pehchana nahi gaya."}

#     student = db.query(Student).filter(Student.id == match["student_id"]).first()
#     today = date.today()

#     # Duplicate check within same session window
#     existing = db.query(Attendance).filter(
#         Attendance.student_id == student.id, Attendance.date == today,
#         Attendance.session_type == session_type).first()
#     if existing:
#         return {"status": "duplicate",
#                 "message": f"{student.name} already marked for {session_type}.",
#                 "student": student.name}

#     now = datetime.now()
#     rec = Attendance(student_id=student.id, date=today, timestamp=now,
#                      session_type=session_type, status="Present", marked_by="CCTV")
#     db.add(rec); db.commit()

#     if student.parent_id:
#         notify_parent(db, student.parent_id, student.id, student.name,
#                       session_type, now)

#     return {"status": "success",
#             "message": f"✅ {student.name} marked {session_type} at "
#                        f"{now.strftime('%I:%M %p')}",
#             "student": student.name, "session": session_type,
#             "time": now.strftime("%I:%M %p")}
@router.post("/recognize")
def recognize(data: RecognizeIn, db: Session = Depends(get_db),
              _=Depends(cctv_access)):
    session_type = _current_session()
    if not session_type:
        return {"status": "closed", "results": [],
                "message": "Attendance window band hai abhi (session time ke bahar)."}

    # Ek frame me SAARE faces nikalo
    encs = get_encodings_from_image(data.image)
    if not encs:
        return {"status": "no_face", "results": [],
                "message": "Koi chehra detect nahi hua."}

    students = [(s.id, s.name, s.face_encodings) for s in db.query(Student).all()]
    today = date.today()
    now = datetime.now()

    results = []
    marked_names = []

    # Har detected face ke liye alag match
    for enc in encs:
        match = match_face(enc, students, FACE_MATCH_TOLERANCE)
        if not match:
            results.append({"status": "unknown", "name": None,
                            "message": "Ek chehra pehchana nahi gaya."})
            continue

        student = db.query(Student).filter(Student.id == match["student_id"]).first()

        # Duplicate check (same session)
        existing = db.query(Attendance).filter(
            Attendance.student_id == student.id, Attendance.date == today,
            Attendance.session_type == session_type).first()
        if existing:
            results.append({"status": "duplicate", "name": student.name,
                            "message": f"{student.name} already marked ({session_type})."})
            continue

        # Naya attendance record
        rec = Attendance(student_id=student.id, date=today, timestamp=now,
                         session_type=session_type, status="Present", marked_by="CCTV")
        db.add(rec)
        db.commit()

        if student.parent_id:
            notify_parent(db, student.parent_id, student.id, student.name,
                          session_type, now)

        marked_names.append(student.name)
        results.append({"status": "success", "name": student.name,
                        "session": session_type, "time": now.strftime("%I:%M %p"),
                        "message": f"✅ {student.name} marked {session_type} "
                                   f"at {now.strftime('%I:%M %p')}"})

    # Overall summary
    faces_found = len(encs)
    marked_count = len(marked_names)
    summary = f"👥 {faces_found} face(s) detected · {marked_count} newly marked"

    return {"status": "batch", "results": results,
            "faces_found": faces_found, "marked_count": marked_count,
            "marked_names": marked_names, "message": summary}