from sqlalchemy.orm import Session
from app.models.interview_state import InterviewState

def get_or_create_state(db: Session, interview_id: str, owner_id: int) -> InterviewState:
    state = db.query(InterviewState).filter_by(interview_id=interview_id).first()
    if not state:
        state = InterviewState(
            interview_id=interview_id, 
            owner_id=owner_id, 
            current_phase="GREETING",
            turn_count=0,
            mastered_skills=[],
            knowledge_blanks=[]
        )
        db.add(state)
        db.commit()
        db.refresh(state)
    return state

def advance_interview_state(db: Session, state: InterviewState, eval_result: dict = None):
    """
    状态机向前演进：更新技能点并推断下一个状态阶段
    """
    state.turn_count += 1

    if eval_result:
        # Array mutability workaround for SQLAlchemy JSON column
        current_mastered = list(state.mastered_skills) if state.mastered_skills else []
        if eval_result.get("mastered_skills"):
            for s in eval_result["mastered_skills"]:
                if s not in current_mastered:
                    current_mastered.append(s)
        state.mastered_skills = current_mastered

        current_blanks = list(state.knowledge_blanks) if state.knowledge_blanks else []
        if eval_result.get("knowledge_blank"):
            for s in eval_result["knowledge_blank"]:
                if s not in current_blanks:
                    current_blanks.append(s)
        state.knowledge_blanks = current_blanks

    # ==========================
    # 状态路由转移逻辑 (Transition Rules)
    # ==========================
    if state.current_phase == "GREETING":
        state.current_phase = "SKILL_DRILL"

    elif state.current_phase == "SKILL_DRILL":
        if state.turn_count >= 15:
            state.current_phase = "CODE_TEST"
            
    elif state.current_phase == "CODE_TEST":
        state.current_phase = "ENDING"

    # Save changes
    db.commit()
    db.refresh(state)
    return state
