from fastapi import APIRouter, HTTPException, Query
import uuid
import random
from datetime import datetime

from app.services.rag_service import retrieve_questions, generate_rag_answer
from app.services.interviewer import (
    DEFAULT_QUESTION_ID,
    evaluate_interview_answer,
    get_question_from_chroma,
    evaluate_mentor_question,
    generate_welcome_message,
)
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


def unavailable_assessment(current_difficulty: str = "Middle") -> dict:
    return {
        "score": 0,
        "feedback": "Ментор временно недоступен: не удалось получить оценку от GigaChat. Проверьте GIGACHAT_CREDENTIALS и попробуйте снова.",
        "calculated_next_difficulty": current_difficulty,
    }


def get_question_options_data() -> dict:
    try:
        results = questions_collection.get(include=["metadatas"])
        metadatas = results.get("metadatas") or []
    except Exception:
        metadatas = []

    options: dict[str, dict[str, set[str]]] = {}

    for item in metadatas:
        if not item:
            continue

        direction = item.get("direction")
        topic = item.get("topic")
        difficulty = item.get("difficulty")

        if not direction or not topic or not difficulty:
            continue

        options.setdefault(direction, {}).setdefault(topic, set()).add(difficulty)

    return {
        "directions": sorted(options),
        "topics_by_direction": {
            direction: sorted(topics)
            for direction, topics in options.items()
        },
        "difficulties_by_direction_topic": {
            direction: {
                topic: sorted(difficulties)
                for topic, difficulties in topics.items()
            }
            for direction, topics in options.items()
        },
    }


def get_available_difficulties(direction: str, topic: str) -> list[str]:
    return (
        get_question_options_data()
        .get("difficulties_by_direction_topic", {})
        .get(direction, {})
        .get(topic, [])
    )


def resolve_available_difficulty(direction: str, topic: str, preferred: str) -> str | None:
    available = get_available_difficulties(direction, topic)

    if not available:
        return None
    if preferred in available:
        return preferred

    difficulty_order = {"Junior": 0, "Middle": 1, "Senior": 2}
    preferred_rank = difficulty_order.get(preferred, 1)

    return min(
        available,
        key=lambda item: abs(difficulty_order.get(item, preferred_rank) - preferred_rank),
    )


def get_question_by_filters(direction: str, topic: str, difficulty: str) -> dict | None:
    results = questions_collection.get(
        where={
            "$and": [
                {"direction": direction},
                {"topic": topic},
                {"difficulty": difficulty},
            ]
        }
    )

    if not results or not results["documents"]:
        return None

    random_idx = random.randint(0, len(results["documents"]) - 1)
    metadata = results["metadatas"][random_idx]

    return {
        "id": results["ids"][random_idx],
        "text": results["documents"][random_idx],
        "answer": metadata.get("answer", ""),
        "direction": metadata.get("direction", direction),
        "topic": metadata.get("topic", topic),
        "difficulty": metadata.get("difficulty", difficulty),
    }


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


@router.get("/question/options")
def read_question_options():
    return get_question_options_data()


@router.get("/question")
async def get_single_question(
    direction: str = Query(...),
    topic: str = Query(...),
    difficulty: str = Query("Middle")
):
    try:
        question_data = get_question_by_filters(direction, topic, difficulty)

        if not question_data:
            raise HTTPException(
                status_code=404,
                detail="Вопрос не найден для выбранной комбинации.",
            )

        return {
            "question_id": question_data["id"],
            "direction": question_data["direction"],
            "topic": question_data["topic"],
            "difficulty": question_data["difficulty"],
            "text": question_data["text"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Вопрос не найден в ChromaDB: {str(e)}")


@router.post("/answer")
async def submit_single_answer(payload: AnswerSubmitRequest):
    try:
        if payload.question_id == DEFAULT_QUESTION_ID:
            return {
                "question_id": payload.question_id,
                "score": 0,
                "feedback": "В базе пока нет эталонного вопроса и ответа для этой темы, поэтому автоматическая проверка недоступна. Добавьте вопросы в базу и попробуйте снова."
            }

        res = questions_collection.get(ids=[payload.question_id])
        if not res["documents"]:
            raise HTTPException(status_code=404, detail="Вопрос не найден в ChromaDB")
            
        question_text = res["documents"][0]
        model_answer = res["metadatas"][0].get("answer", "")
        difficulty = res["metadatas"][0].get("difficulty", "Middle")

        try:
            assessment = evaluate_mentor_question(
                question=question_text,
                model_answer=model_answer,
                user_answer=payload.answer,
                current_difficulty=difficulty
            )
        except Exception:
            assessment = unavailable_assessment(difficulty)

        return {
            "question_id": payload.question_id,
            "score": assessment["score"],
            "feedback": assessment["feedback"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interview/start")
async def start_interview_session(payload: InterviewStartRequest):
    try:
        session_id = str(uuid.uuid4())
        start_difficulty = resolve_available_difficulty(payload.direction, payload.topic, "Middle")
        if not start_difficulty:
            raise HTTPException(
                status_code=404,
                detail="Нет вопросов для выбранного направления и темы.",
            )

        first_q = get_question_by_filters(
            direction=payload.direction,
            topic=payload.topic,
            difficulty=start_difficulty,
        )
        if not first_q:
            raise HTTPException(
                status_code=404,
                detail="Нет вопросов для выбранного направления и темы.",
            )
        
        try:
            welcome_msg = generate_welcome_message(
                position_name=f"{payload.direction} ({payload.topic})",
                first_question=first_q["text"]
            )
        except Exception:
            welcome_msg = (
                f"Здравствуйте. Начнём интервью по направлению {payload.direction}, "
                f"тема: {payload.topic}.\n\n{first_q['text']}"
            )
        
        return {
            "session_id": session_id,
            "direction": payload.direction,
            "topic": payload.topic,
            "message": welcome_msg,
            "current_difficulty": first_q["difficulty"],
            "question_number": 1
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/interview/message")
async def handle_interview_message(payload: InterviewMessageRequest):
    try:
        current_difficulty = resolve_available_difficulty(
            payload.direction,
            payload.topic,
            payload.current_difficulty,
        )
        if not current_difficulty:
            raise HTTPException(
                status_code=404,
                detail="Нет вопросов для выбранного направления и темы.",
            )

        current_q = get_question_by_filters(
            direction=payload.direction,
            topic=payload.topic,
            difficulty=current_difficulty,
        )
        if not current_q:
            raise HTTPException(
                status_code=404,
                detail="Нет вопросов для выбранного направления и темы.",
            )

        try:
            assessment = evaluate_interview_answer(
                question=current_q["text"],
                model_answer=current_q["answer"],
                user_answer=payload.message,
                current_difficulty=current_difficulty
            )
        except Exception:
            assessment = unavailable_assessment(current_difficulty)
        
        next_difficulty = resolve_available_difficulty(
            payload.direction,
            payload.topic,
            assessment.get("calculated_next_difficulty", current_difficulty),
        )
        if not next_difficulty:
            raise HTTPException(
                status_code=404,
                detail="Нет вопросов для выбранного направления и темы.",
            )
        
        next_q = get_question_by_filters(
            direction=payload.direction,
            topic=payload.topic,
            difficulty=next_difficulty,
        )
        if not next_q:
            raise HTTPException(
                status_code=404,
                detail="Нет вопросов для выбранного направления и темы.",
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
