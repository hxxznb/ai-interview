import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime

from app.database import Base

class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, index=True)
    interview_id = Column(String(100), unique=True, index=True)
    job = Column(String(100))
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    is_active = Column(Boolean, default=True)
    final_duration = Column(Integer, nullable=True)
