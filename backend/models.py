from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="staff") # admin, staff
    department = Column(String, nullable=True)
    
    # Path to the stored face image or embedding (simplified for now to just path)
    face_image_path = Column(String, nullable=True)

    attendance_records = relationship("Attendance", back_populates="user")

class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    status = Column(String) # Present, Late, Absent
    ip_address = Column(String)
    verification_method = Column(String) # Wifi, Face, Dual
    
    user = relationship("User", back_populates="attendance_records")
