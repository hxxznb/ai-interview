from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
# 导入所有模型以确保 Base.metadata 包含全部表定义
from app.models import User, Message, Job, Report, Assessment, RecentDiagnosis, ResumeAnalysis, ResumeBlock, InterviewState  # noqa: F401

from app.routers import auth, chat, jobs, reports, assessment, recent_diagnosis, session
from app.routers import resume

# 自动建表
Base.metadata.create_all(bind=engine)

# 创建 FastAPI 应用
app = FastAPI(title="AI 模拟面试系统", version="2.0")

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载全部路由
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(jobs.router)
app.include_router(reports.router)
app.include_router(assessment.router)
app.include_router(recent_diagnosis.router)
app.include_router(session.router)
app.include_router(resume.router)
