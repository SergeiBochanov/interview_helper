from pydantic import BaseModel
from typing import List
from datetime import datetime
from typing import Optional

class InterviewFinishRequest(BaseModel):
    user_id: str
    session_id: str
    direction: str
    topic: str
    scores: List[int]

class SessionHistoryResponse(BaseModel):
    session_id: str
    user_id: str
    direction: str
    topic: str
    questions_count: int
    avg_score: float
    date: datetime

    class Config:
        from_attributes = True

class WeakTopicResponse(BaseModel):
    topic: str
    avg_score: float