import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from app.database import Base


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, index=True)
    interview_id = Column(String(50), index=True)
    role = Column(String(20))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
