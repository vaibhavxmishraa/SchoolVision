import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from ..database import get_db
from ..deps import require_role
from ..models import User, Student, Attendance
from ..auth import hash_password
from ..face_engine import get_encodings_from_image
from ..excel_export import build_report

router = APIRouter(prefix="/api/admin", tags=["admin"])
admin_only = require_role("Admin")


class StudentIn(BaseModel):
    name: str
    roll_number: str
    class_section: str
    parent_id: int
    face_images: List[str] = []   # base64 data URLs


class TeacherIn(BaseModel):
    username: str
    password: str
    full_name: str
    phone_number: str = ""


class ParentIn(BaseModel):
    username: str
    password: str
    full_name: str
    phone_number: str = ""


@router.get("/stats")
def stats(db: Session = Depends(get_db), _=Depends(admin_only)):
    from datetime import date
    today = date.today()
    return {
        "students": db.query(Student).count(),
        "teachers": db.query(User).filter(User.role == "Teacher").count(),
        "parents": db.query(User).filter(User.role == "Parent").count(),
        "today_present": db.query(Attendance).filter(
            Attendance.date == today, Attendance.session_type == "Check-In").count(),
    }


@router.get("/parents")
def list_parents(db: Session = Depends(get_db), _=Depends(admin_only)):
    return [{"id": u.id, "full_name": u.full_name, "username": u.username,
             "phone_number": u.phone_number}
            for u in db.query(User).filter(User.role == "Parent").all()]


@router.post("/parents")
def add_parent(data: ParentIn, db: Session = Depends(get_db), _=Depends(admin_only)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, "Username already exists")
    u = User(username=data.username, password_hash=hash_password(data.password),
             role="Parent", full_name=data.full_name, phone_number=data.phone_number)
    db.add(u); db.commit(); db.refresh(u)
    return {"id": u.id, "message": "Parent added"}


@router.get("/teachers")
def list_teachers(db: Session = Depends(get_db), _=Depends(admin_only)):
    return [{"id": u.id, "full_name": u.full_name, "username": u.username,
             "phone_number": u.phone_number}
            for u in db.query(User).filter(User.role == "Teacher").all()]


@router.post("/teachers")
def add_teacher(data: TeacherIn, db: Session = Depends(get_db), _=Depends(admin_only)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, "Username already exists")
    u = User(username=data.username, password_hash=hash_password(data.password),
             role="Teacher", full_name=data.full_name, phone_number=data.phone_number)
    db.add(u); db.commit(); db.refresh(u)
    return {"id": u.id, "message": "Teacher added"}


@router.get("/students")
def list_students(db: Session = Depends(get_db), _=Depends(admin_only)):
    out = []
    for s in db.query(Student).all():
        enc_count = len(json.loads(s.face_encodings or "[]"))
        out.append({"id": s.id, "name": s.name, "roll_number": s.roll_number,
                    "class_section": s.class_section, "parent_id": s.parent_id,
                    "parent_name": s.parent.full_name if s.parent else "-",
                    "face_samples": enc_count})
    return out


@router.post("/students")
def add_student(data: StudentIn, db: Session = Depends(get_db), _=Depends(admin_only)):
    if db.query(Student).filter(Student.roll_number == data.roll_number).first():
        raise HTTPException(400, "Roll number already exists")
    encodings = []
    for img in data.face_images:
        encodings.extend(get_encodings_from_image(img))
    s = Student(name=data.name, roll_number=data.roll_number,
                class_section=data.class_section, parent_id=data.parent_id,
                face_encodings=json.dumps(encodings))
    db.add(s); db.commit(); db.refresh(s)
    return {"id": s.id, "message": f"Student added with {len(encodings)} face sample(s)"}


@router.delete("/students/{sid}")
def delete_student(sid: int, db: Session = Depends(get_db), _=Depends(admin_only)):
    s = db.query(Student).filter(Student.id == sid).first()
    if not s:
        raise HTTPException(404, "Not found")
    db.query(Attendance).filter(Attendance.student_id == sid).delete()
    db.delete(s); db.commit()
    return {"message": "Deleted"}


@router.get("/export")
def export_excel(class_section: Optional[str] = None,
                 db: Session = Depends(get_db), _=Depends(admin_only)):
    buf = build_report(db, class_section)
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=EduvisionAI_Report.xlsx"})