from sqlalchemy import Column, Integer, String

from app.database import Base


class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50), index=True)
    category = Column(String(50))
    desc = Column(String(255))
    icon = Column(String(20))
    bgColor = Column(String(20))
    job_key = Column(String(50), default="general")
