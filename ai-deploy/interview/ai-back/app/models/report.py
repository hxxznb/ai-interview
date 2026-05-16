from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from app.database import Base


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(String(50), unique=True, index=True)
    owner_id = Column(Integer, index=True)
    target_job = Column(String(50))
    content = Column(Text)
    duration = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)
