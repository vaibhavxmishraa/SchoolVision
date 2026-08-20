import json, random
from datetime import datetime, timedelta
from .database import SessionLocal
from .models import User, Student, Attendance, Notification
from .auth import hash_password


def _mock_encoding():
    rng = np.random.default_rng(random.randint(0, 10**6))
    return [rng.random(128).tolist()]


import numpy as np


def seed():
    db = SessionLocal()
    if db.query(User).first():
        db.close()
        return  # already seeded

    print("[Seed] 🌱 Inserting mock data...")

    # Admin
    admin = User(username="admin", password_hash=hash_password("admin123"),
                 role="Admin", full_name="System Admin", phone_number="+910000000000")
    db.add(admin)

    # Teachers
    teacher = User(username="teacher", password_hash=hash_password("teacher123"),
                   role="Teacher", full_name="Mrs. Anjali Sharma",
                   phone_number="+910000000001")
    db.add(teacher)

    # Parents
    parents = []
    parent_data = [
        ("parent", "parent123", "Rajesh Kumar", "+919999900001"),
        ("parent2", "parent123", "Sunita Verma", "+919999900002"),
        ("parent3", "parent123", "Amit Singh", "+919999900003"),
    ]
    for uname, pw, name, phone in parent_data:
        p = User(username=uname, password_hash=hash_password(pw),
                 role="Parent", full_name=name, phone_number=phone)
        db.add(p)
        parents.append(p)
    db.commit()

    # Students
    student_data = [
        ("Aarav Kumar", "R001", "5-A", parents[0].id),
        ("Diya Verma", "R002", "5-A", parents[1].id),
        ("Kabir Singh", "R003", "5-B", parents[2].id),
        ("Ishaan Kumar", "R004", "6-A", parents[0].id),
    ]
    students = []
    for name, roll, cls, pid in student_data:
        s = Student(name=name, roll_number=roll, class_section=cls,
                    parent_id=pid, face_encodings=json.dumps(_mock_encoding()))
        db.add(s)
        students.append(s)
    db.commit()

    # Attendance history (last 5 days)
    for s in students:
        for d in range(1, 6):
            day = datetime.now() - timedelta(days=d)
            if random.random() > 0.15:
                db.add(Attendance(student_id=s.id, date=day.date(),
                                  timestamp=day.replace(hour=8, minute=45),
                                  session_type="Check-In", status="Present",
                                  marked_by="CCTV"))
            if random.random() > 0.2:
                db.add(Attendance(student_id=s.id, date=day.date(),
                                  timestamp=day.replace(hour=15, minute=30),
                                  session_type="Check-Out", status="Present",
                                  marked_by="CCTV"))
    db.commit()
    db.close()
    print("[Seed] ✅ Mock data ready.")
    print("       Admin  -> admin / admin123")
    print("       Teacher-> teacher / teacher123")
    print("       Parent -> parent / parent123")