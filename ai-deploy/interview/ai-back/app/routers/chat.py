from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_current_user_id
from app.models.message import Message
from app.models.job import Job
from app.models.report import Report
from app.schemas.chat import ChatRequest
from app.prompts.chat import get_interviewer_prompt
from app.services.chat_engine import get_rag_response
from app.services.evaluator import evaluate_user_response
from app.services.interview_fsm import get_or_create_state, advance_interview_state
from app.services.llm import llm

router = APIRouter()


# ==========================================
# 接口：根据房间号获取历史记录
# ==========================================
@router.get("/api/history/{interview_id}")
def get_history(interview_id: str, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    # 1. 查聊天记录
    messages = db.query(Message).filter(
        Message.interview_id == interview_id,
        Message.owner_id == user_id
    ).order_by(Message.id).all()

    history_list = []
    for msg in messages:
        history_list.append({
            "role": msg.role,
            "content": msg.content,
            "created_at": msg.created_at.isoformat() + "Z" if msg.created_at else None
        })

    # 2. 去 Report 表里捞出这把面试的最终耗时
    report = db.query(Report).filter(
        Report.interview_id == interview_id,
        Report.owner_id == user_id
    ).first()

    final_duration = report.duration if report and report.duration else 0

    return {
        "messages": history_list,
        "duration": final_duration,
        "job": report.target_job if report else None
    }


# ==========================================
# 接口：聊天存储 (加入结束标志识别与状态机)
# ==========================================
@router.post("/api/chat")
def chat_with_ai(
        request: ChatRequest,
        db: Session = Depends(get_db),
        user_id: int = Depends(get_current_user_id)
):
    user_msg = request.message
    target_job = request.job
    chat_history = request.history
    room_id = request.interview_id

    db_job = db.query(Job).filter(Job.title == target_job).first()
    category_dir = db_job.job_key if db_job else "general"

    # 1. 存候选人的消息入库
    if user_msg != "__INIT__":
        new_user_msg = Message(owner_id=user_id, interview_id=room_id, role="user", content=user_msg)
        db.add(new_user_msg)
        db.commit()

    # 2. 梳理历史记录
    history_str = ""
    recent_history = chat_history[-20:] if len(chat_history) > 20 else chat_history
    for msg in recent_history:
        role_name = "考官" if msg["role"] == "ai" else "候选人"
        history_str += f"{role_name}: {msg['content']}\n"
    if not history_str:
        history_str = "无"

    # 3. 获取或创建 FSM 状态
    state = get_or_create_state(db, room_id, user_id)

    # 4. 确定下一步行动
    if user_msg == "__INIT__":
        actual_user_msg = "候选人已进入，请开场。"
        dynamic_search_query = "SKIP_SEARCH"
        target_doc_type = None
        fsm_context = "无"
        # 更新状态机（从创建直接步进一次，尽管第一次可能是特殊的，但在此时还是保留GREETING）
    else:
        actual_user_msg = user_msg
        
        # --- A. Evaluator 阶段：评估回答质量与意图 ---
        last_ai_question = chat_history[-1]['content'] if chat_history else ""
        eval_result = evaluate_user_response(llm, target_job, last_ai_question, user_msg)
        print(f"\n====== [ROUTER] 面试评估中心脑: {eval_result} ======")
        
        # --- B. State Machine 阶段：更新进度与技能 ---
        state = advance_interview_state(db, state, eval_result)
        
        # --- C. 路由控制参数生成 ---
        target_doc_type = None
        
        if state.current_phase == "CODE_TEST":
            dynamic_search_query = f"{target_job} 核心代码题"
            target_doc_type = "code"
            fsm_context = "【强制指令】：直接向他抛出代码题！不用管他的寒暄。"
            
        elif state.current_phase == "ENDING":
            dynamic_search_query = "SKIP_SEARCH"
            fsm_context = "【强制指令】：客套一下，立刻附带[END]暗号结束面试。"
            
        elif state.current_phase == "SKILL_DRILL":
            if eval_result.get("topic_exhausted") or eval_result.get("suggested_next_action") == "SWITCH_TOPIC":
                fsm_context = "【强制指令】：前一个话题已耗尽或出现他不会的盲区，立刻更换全新考核领域并基于提供的知识提问！"
                q = eval_result.get("search_query")
                dynamic_search_query = q if q else f"{target_job} 核心进阶面试题"
            else:
                fsm_context = "【强制指令】：候选人正在回答，请根据提供的资料进行自然追问与深挖。"
                q = eval_result.get("search_query")
                dynamic_search_query = q if q else "SKIP_SEARCH"
                
        else:
            dynamic_search_query = "SKIP_SEARCH"
            fsm_context = "自由发水"

    # 生成微小的 Prompt
    system_prompt = get_interviewer_prompt(target_job, state.current_phase, fsm_context)

    try:
        ai_reply = get_rag_response(
            user_message=actual_user_msg,
            chat_history_str=history_str,
            system_prompt=system_prompt,
            category_filter=category_dir,
            search_query=dynamic_search_query,
            doc_type=target_doc_type
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI 考官大脑异常 (RAG失败): {str(e)}")

    # 6. 检查结束暗号
    is_finished = False
    if "[END]" in ai_reply:
        is_finished = True
        ai_reply = ai_reply.replace("[END]", "").strip()

    # 7. 存 AI 消息入库
    new_ai_msg = Message(owner_id=user_id, interview_id=room_id, role="ai", content=ai_reply)
    db.add(new_ai_msg)
    db.commit()

    return {"reply": ai_reply, "is_finished": is_finished}
