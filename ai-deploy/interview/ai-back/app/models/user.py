from sqlalchemy import Column, Integer, String

from app.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    account = Column(String(50), unique=True, index=True)
    password_hash = Column(String(255))
