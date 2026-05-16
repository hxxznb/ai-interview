from pydantic import BaseModel
from typing import List, Dict


class ChatRequest(BaseModel):
    message: str
    job: str
    history: List[Dict[str, str]] = []
    interview_id: str
