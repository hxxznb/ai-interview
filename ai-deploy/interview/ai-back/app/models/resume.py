from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, Enum
from app.database import Base


class ResumeAnalysis(Base):
    """一次完整的简历分析任务（主表）"""
    __tablename__ = "resume_analyses"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, index=True, nullable=False)
    job_target = Column(String(100), nullable=False, default="通用岗位")

    # 文件存储路径（均为服务器本地磁盘路径）
    original_file_path = Column(String(500))    # 用户上传的原始简历
    original_filename = Column(String(255))     # 原始文件名（显示给用户）
    output_file_path = Column(String(500))      # 构建完成后生成的新简历路径

    # 整体评估（LLM 最终总结，存 JSON 字符串）
    overall_strengths = Column(Text)            # 优点列表 JSON (e.g., '["...","..."]')
    overall_weaknesses = Column(Text)           # 缺点列表 JSON
    job_match_score = Column(Float)             # 岗位匹配度 0.0-100.0

    # 状态机: pending → analyzing → reviewed → building → done | failed
    status = Column(String(20), default="pending")

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ResumeBlock(Base):
    """按段落拆分的简历块（子表），每行代表一个可单独审阅的内容块"""
    __tablename__ = "resume_blocks"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("resume_analyses.id", ondelete="CASCADE"), nullable=False, index=True)

    block_index = Column(Integer, nullable=False)       # 排序序号
    section_title = Column(String(100), default="")     # 所属章节标题（如"工作经历"）

    original_text = Column(Text, nullable=False)        # 原文
    suggested_text = Column(Text)                       # AI 建议修改后的版本
    suggestion_reason = Column(Text)                    # AI 给出的修改原因简述

    # None = 待审阅, True = 用户接受, False = 用户忽略
    is_accepted = Column(Boolean, nullable=True, default=None)

    # 分析状态: pending | done | failed
    block_status = Column(String(20), default="pending")
