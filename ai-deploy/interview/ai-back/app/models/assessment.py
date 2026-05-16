from datetime import datetime

from sqlalchemy import Column, Integer, Text, DateTime

from app.database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, unique=True, index=True)
    total_interviews = Column(Integer, default=0)

    avg_score = Column(Integer, default=0)
    total_duration = Column(Integer, default=0)

    radar_data = Column(Text, default="{}")
    trend_data = Column(Text, default="[]")
    ai_insight = Column(Text, default="")
    
    # 新增字段
    top_strengths = Column(Text, default="[]")
    priority_actions = Column(Text, default="[]")
    global_blank_tags = Column(Text, default="[]")

    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
