# 汇总导出所有 ORM 模型，方便 create_all 一次性建表
from app.models.user import User
from app.models.message import Message
from app.models.job import Job
from app.models.report import Report
from app.models.assessment import Assessment
from app.models.recent_diagnosis import RecentDiagnosis
from app.models.session import InterviewSession
from app.models.resume import ResumeAnalysis, ResumeBlock
from app.models.interview_state import InterviewState

__all__ = [
    "User",
    "Message",
    "Job",
    "Report",
    "Assessment",
    "RecentDiagnosis",
    "InterviewSession",
    "ResumeAnalysis",
    "ResumeBlock",
    "InterviewState",
]
