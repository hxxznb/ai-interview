from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=10,          # 常驻连接数
    max_overflow=20,       # 突发情况允许额外建立的连接
    pool_recycle=3600,     # 一个小时回收一次，防止 MySQL 默认的 8 小时断线
    pool_pre_ping=True     # 每次使用前先 ping 一下保活，极其重要
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
