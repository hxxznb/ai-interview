import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from app.dependencies import get_db, get_current_user_id
from app.models.message import Message
from app.models.report import Report
from app.models.session import InterviewSession
from app.models.interview_state import InterviewState
from app.schemas.report import AssessmentReport
from app.prompts.report import get_report_system_prompt, get_report_user_prompt
from app.services.llm import llm

router = APIRouter()


# ==========================================
# 核心接口：生成并获取报告
# ==========================================
@router.post("/api/report/generate/{interview_id}")
async def generate_report(
        interview_id: str,
        target_job: str,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    # 1. 查缓存（如果有老数据，直接返回）
    existing_report = db.query(Report).filter(
        Report.interview_id == interview_id,
        Report.owner_id == user_id
    ).first()

    if existing_report:
        return json.loads(existing_report.content)

    # 2. 捞取聊天记录
    messages = db.query(Message).filter(
        Message.interview_id == interview_id,
        Message.owner_id == user_id
    ).order_by(Message.id).all()

    if not messages:
        raise HTTPException(status_code=404, detail="找不到该面试的聊天记录")

    duration_sec = 0
    if len(messages) >= 2:
        time_diff = messages[-1].created_at - messages[0].created_at
        duration_sec = int(time_diff.total_seconds())

    # 检查候选人到底有没有实质性发言
    user_msgs = [msg for msg in messages if msg.role == "user" and msg.content != "__INIT__"]
    total_user_words = sum(len(msg.content) for msg in user_msgs)

    if not user_msgs or total_user_words < 5:
        blank_report = {
            "score": 0,
            "evaluation": "候选人未进行实质性作答（交白卷），无法进行有效评估。本次面试视为放弃。",
            "tech_ability": "无数据支持。",
            "communication": "无数据支持。",
            "strengths": ["无"],
            "weaknesses": ["未作答/早退"],
            "radar_data": {"tech": 0, "logic": 0, "communication": 0, "experience": 0, "potential": 0},
            "skill_breakdown": [],
            "knowledge_blank_tags": [],
            "improvement_advice": "候选人未参与作答，建议先梳理核心技术基础后再尝试面试。"
        }
        _save_report_and_close_session(db, interview_id, user_id, target_job, blank_report, duration_sec)
        return blank_report

    # 3. 从 InterviewState 中获取 FSM 积累的结构化证据
    interview_state = db.query(InterviewState).filter(
        InterviewState.interview_id == interview_id
    ).first()

    mastered_skills = []
    knowledge_blanks = []
    turn_count = len(user_msgs)

    if interview_state:
        mastered_skills = interview_state.mastered_skills or []
        knowledge_blanks = interview_state.knowledge_blanks or []
        turn_count = interview_state.turn_count or turn_count

    print(f"\n====== [REPORT] FSM 证据注入 ======")
    print(f"  已掌握技能: {mastered_skills}")
    print(f"  技能盲区:   {knowledge_blanks}")
    print(f"  总回合数:   {turn_count}")
    print(f"===================================\n")

    # 4. 正常拼接对话记录
    chat_history_text = ""
    for msg in messages:
        role_name = "AI面试官" if msg.role == "ai" else "候选人"
        chat_history_text += f"【{role_name}】: {msg.content}\n"

    # 5. 呼叫大模型：注入证据 + 结构化输出
    system_prompt = get_report_system_prompt(target_job)
    user_prompt = get_report_user_prompt(
        chat_history=chat_history_text,
        mastered_skills=mastered_skills,
        knowledge_blanks=knowledge_blanks,
        turn_count=turn_count
    )

    parser = JsonOutputParser(pydantic_object=AssessmentReport)

    prompt = ChatPromptTemplate.from_messages([
        ("system", "{system_prompt}\n\n【输出格式要求】\n{format_instructions}"),
        ("user", "{user_prompt}")
    ])

    chain = prompt | llm | parser

    try:
        report_data = await chain.ainvoke({
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "format_instructions": parser.get_format_instructions()
        })

        _save_report_and_close_session(db, interview_id, user_id, target_job, report_data, duration_sec)

        return report_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 生成报告失败，请重试。错误日志: {str(e)}")


def _save_report_and_close_session(
    db: Session, interview_id: str, user_id: int,
    target_job: str, report_data: dict, duration_sec: int
):
    """复用：存报告 + 关闭会话"""
    content_str = json.dumps(report_data, ensure_ascii=False)
    new_report = Report(
        interview_id=interview_id,
        owner_id=user_id,
        target_job=target_job,
        content=content_str,
        duration=duration_sec
    )
    db.add(new_report)

    session = db.query(InterviewSession).filter(InterviewSession.interview_id == interview_id).first()
    if session:
        session.is_active = False
        session.final_duration = duration_sec

    db.commit()


# ==========================================
# 获取当前用户的所有面试历史记录
# ==========================================
@router.get("/api/reports/history")
async def get_report_history(
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    reports = db.query(Report).filter(Report.owner_id == user_id).order_by(Report.id.desc()).all()

    history_list = []
    for r in reports:
        try:
            content_dict = json.loads(r.content)
            time_str = r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "未知时间"
            history_list.append({
                "interview_id": r.interview_id,
                "target_job": r.target_job,
                "score": content_dict.get("score", 0),
                "evaluation": content_dict.get("evaluation", "暂无评价"),
                "knowledge_blank_tags": content_dict.get("knowledge_blank_tags", []),
                "created_at": time_str
            })
        except Exception:
            continue

    return history_list
