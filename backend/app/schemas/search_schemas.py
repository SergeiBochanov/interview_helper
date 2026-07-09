from pydantic import BaseModel, Field
from typing import List, Optional

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3)
    top_n: int = Field(default=20, ge=1, le=50)
    top_k: int = Field(default=5, ge=1, le=20)
    use_reranker: bool = True

class RagAnswerRequest(BaseModel):
    query: str = Field(..., min_length=3)
    top_n: int = Field(default=20, ge=1, le=50)
    top_k: int = Field(default=5, ge=1, le=20)

class AnswerSubmitRequest(BaseModel):
    user_id: str
    question_id: str
    topic: str
    answer: str

class InterviewStartRequest(BaseModel):
    direction: str
    topic: str

class InterviewMessageRequest(BaseModel):
    user_id: str
    session_id: str
    direction: str
    topic: str
    message: str
    question_number: int
    current_difficulty: str

class HistoryItem(BaseModel):
    session_id: str
    date: str
    direction: str
    topic: str
    score: float
    status: str

class HistoryResponse(BaseModel):
    history: List[HistoryItem]