from datetime import datetime

from sqlalchemy import Column, Integer, Text, DateTime

from app.database import Base


class RecentDiagnosis(Base):
    __tablename__ = "recent_diagnoses"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, unique=True, index=True)

    total_interviews = Column(Integer, default=0)

    multi_line_data = Column(Text, default="[]")
    delta_data = Column(Text, default="{}")
    weakness_tags = Column(Text, default="[]")
    expert_advice = Column(Text, default="")
    
    # 新增字段
    blank_frequency = Column(Text, default="[]")

    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
