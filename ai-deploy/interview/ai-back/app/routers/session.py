import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.dependencies import get_db, get_current_user_id
from app.models.session import InterviewSession

router = APIRouter()

class StartSessionRequest(BaseModel):
    interview_id: str
    job: str

class EndSessionRequest(BaseModel):
    interview_id: str
    final_duration: int = 0

@router.post("/api/session/start")
def start_session(req: StartSessionRequest, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    session = db.query(InterviewSession).filter(
        InterviewSession.interview_id == req.interview_id,
        InterviewSession.owner_id == user_id
    ).first()
    
    current_time = datetime.datetime.utcnow()
    
    if not session:
        session = InterviewSession(
            owner_id=user_id,
            interview_id=req.interview_id,
            job=req.job,
            start_time=current_time,
            is_active=True
        )
        db.add(session)
        db.commit()
        db.refresh(session)
    elif not session.is_active:
        # If the frontend re-requests start on an inactive session, 
        # it should just return the state (though logically this shouldn't happen for new interviews)
        pass

    return {
        "interview_id": session.interview_id,
        "start_time": int(session.start_time.replace(tzinfo=datetime.timezone.utc).timestamp() * 1000),
        "is_active": session.is_active
    }

@router.get("/api/session/active")
def get_active_session(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    session = db.query(InterviewSession).filter(
        InterviewSession.owner_id == user_id,
        InterviewSession.is_active == True
    ).order_by(InterviewSession.id.desc()).first()
    
    if session:
        return {
            "interview_id": session.interview_id,
            "job": session.job,
            "start_time": int(session.start_time.replace(tzinfo=datetime.timezone.utc).timestamp() * 1000)
        }
    return None

@router.post("/api/session/end")
def end_session(req: EndSessionRequest, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    session = db.query(InterviewSession).filter(
        InterviewSession.interview_id == req.interview_id,
        InterviewSession.owner_id == user_id
    ).first()
    
    if session and session.is_active:
        session.is_active = False
        session.final_duration = req.final_duration
        db.commit()
        
    return {"success": True}
