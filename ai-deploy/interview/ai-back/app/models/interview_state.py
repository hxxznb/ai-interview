import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON

from app.database import Base

class InterviewState(Base):
    __tablename__ = "interview_states"
    
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, index=True)
    interview_id = Column(String(50), unique=True, index=True)
    
    current_phase = Column(String(50), default="GREETING")  # GREETING, SKILL_DRILL, CODE_TEST, ENDING
    turn_count = Column(Integer, default=0)
    
    # Store skills as JSON like: ["vue", "react"]
    mastered_skills = Column(JSON, default=list)
    knowledge_blanks = Column(JSON, default=list)
    
    # Track the current active topic
    current_topic = Column(String(200), nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
