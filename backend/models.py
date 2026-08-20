from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Date
)
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)          # Admin / Teacher / Parent
    full_name = Column(String, default="")
    phone_number = Column(String, default="")

    students = relationship("Student", back_populates="parent")


class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    roll_number = Column(String, unique=True, nullable=False)
    class_section = Column(String, default="")
    parent_id = Column(Integer, ForeignKey("users.id"))
    face_encodings = Column(Text, default="[]")     # JSON array of 128-d vectors

    parent = relationship("User", back_populates="students")
    attendance = relationship("Attendance", back_populates="student")


class Attendance(Base):
    __tablename__ = "attendance"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    date = Column(Date, default=datetime.utcnow().date)
    timestamp = Column(DateTime, default=datetime.now)
    session_type = Column(String)                   # Check-In / Check-Out
    status = Column(String, default="Present")       # Present / Absent / Manual Override
    marked_by = Column(String, default="CCTV")       # CCTV / Teacher_Name

    student = relationship("Student", back_populates="attendance")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("users.id"))
    student_id = Column(Integer, ForeignKey("students.id"))
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.now)
    is_read = Column(Boolean, default=False)