import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """统一配置管理：所有敏感信息和可调参数集中于此"""

    # 数据库
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:246810hxx@localhost:3306/ai_interview"
    )

    # JWT 鉴权
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_super_secret_key_for_interview")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXPIRE_DAYS: int = int(os.getenv("JWT_EXPIRE_DAYS", "7"))

    # 阿里云 DashScope
    DASHSCOPE_API_KEY: str = os.getenv("DASHSCOPE_API_KEY", "")

    # LLM 模型
    LLM_MODEL: str = os.getenv("LLM_MODEL", "qwen-turbo")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-v1")


settings = Settings()
