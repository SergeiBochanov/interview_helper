from fastapi import APIRouter, HTTPException, Query
import uuid
from datetime import datetime

from app.services.rag_service import retrieve_questions, generate_rag_answer
from app.services.interviewer import evaluate_interview_answer, get_question_from_chroma, evaluate_mentor_question, generate_welcome_message
from app.services.chroma_service import questions_collection
from app.services.chroma_search_service import questions_collection, get_all_saved_topics

from app.schemas.search_schemas import (
    SearchRequest, 
    RagAnswerRequest, 
    AnswerSubmitRequest, 
    InterviewStartRequest, 
    InterviewMessageRequest,
    HistoryResponse
)

router = APIRouter()

DIFFICULTIES = ["Junior", "Middle", "Senior"]


@router.post("/search")
async def search_endpoint(payload: SearchRequest):
    try:
        results = retrieve_questions(
            query=payload.query,
            top_n=payload.top_n,
            top_k=payload.top_k,
            use_reranker=payload.use_reranker,
        )
        return {
            "query": payload.query,
            "count": len(results),
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/answer")
async def rag_answer_endpoint(payload: RagAnswerRequest):
    try:
        result = generate_rag_answer(
            query=payload.query,
            top_n=payload.top_n,
            top_k=payload.top_k,
        )
        return {
            "query": payload.query,
            **result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/topics")
def read_topics():
    topics = get_all_saved_topics()
    if not topics:
        return ["Алгоритмы", "SQL", "Системный дизайн", "Machine Learning", "Поведенческие"]
    return topics


@router.get("/question")
async def get_single_question(
    direction: str = Query(...),
    topic: str = Query(...),
    difficulty: str = Query("Middle")
):
    try:
        question_data = get_question_from_chroma(direction=direction, topic=topic, difficulty=difficulty)
        return {
            "question_id": question_data["id"],
            "direction": direction,
            "topic": topic,
            "difficulty": difficulty,
            "text": question_data["text"]
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Вопрос не найден в ChromaDB: {str(e)}")


@router.post("/answer")
async def submit_single_answer(payload: AnswerSubmitRequest):
    try:
        res = questions_collection.get(ids=[payload.question_id])
        if not res["documents"]:
            raise HTTPException(status_code=404, detail="Вопрос не найден в ChromaDB")
            
        question_text = res["documents"][0]
        model_answer = res["metadatas"][0].get("answer", "")
        difficulty = res["metadatas"][0].get("difficulty", "Middle")

        assessment = evaluate_mentor_question(
            question=question_text,
            model_answer=model_answer,
            user_answer=payload.answer,
            current_difficulty=difficulty
        )
        return {
            "question_id": payload.question_id,
            "score": assessment["score"],
            "feedback": assessment["feedback"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interview/start")
async def start_interview_session(payload: InterviewStartRequest):
    try:
        session_id = str(uuid.uuid4())
        first_q = get_question_from_chroma(direction=payload.direction, topic=payload.topic, difficulty="Middle")
        
        welcome_msg = generate_welcome_message(
            position_name=f"{payload.direction} ({payload.topic})", 
            first_question=first_q["text"]
        )
        
        return {
            "session_id": session_id,
            "direction": payload.direction,
            "topic": payload.topic,
            "message": welcome_msg,
            "current_difficulty": "Middle",
            "question_number": 1
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interview/message")
async def handle_interview_message(payload: InterviewMessageRequest):
    try:
        current_q = get_question_from_chroma(
            direction=payload.direction, 
            topic=payload.topic, 
            difficulty=payload.current_difficulty
        )

        assessment = evaluate_interview_answer(
            question=current_q["text"],
            model_answer=current_q["answer"],
            user_answer=payload.message,
            current_difficulty=payload.current_difficulty
        )
        
        next_difficulty = assessment.get("calculated_next_difficulty", payload.current_difficulty)
        
        next_q = get_question_from_chroma(
            direction=payload.direction, 
            topic=payload.topic, 
            difficulty=next_difficulty
        )
        
        return {
            "session_id": payload.session_id,
            "score": assessment["score"],
            "feedback": assessment["feedback"],
            "next_question": next_q["text"],
            "next_topic": payload.topic,
            "calculated_next_difficulty": next_difficulty,
            "question_number": payload.question_number + 1
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=HistoryResponse)
async def get_interview_history(user_id: str = Query(...)):
    """
    Возвращает историю. Пока база данных PostgreSQL для сессий находится в процессе 
    подключения, отдаем пустой список [], чтобы у фронтенда не было 404 ошибки.
    """
    return {"history": []}