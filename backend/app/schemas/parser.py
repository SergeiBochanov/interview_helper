from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any

class ParseUrlRequest(BaseModel):
    url: str

class QuestionItem(BaseModel):
    question: str
    answer: str
    direction: str
    topic: str
    difficulty: str

class BatchAddQuestionsRequest(BaseModel):
    questions: List[QuestionItem]

class ProcessStatusResponse(BaseModel):
    status: str
    details: Dict[str, Any]