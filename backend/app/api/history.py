from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.database import get_db
from app.database.models import InterviewSession, QuestionAttempt
from app.schemas.history import InterviewFinishRequest, SessionHistoryResponse, WeakTopicResponse

router = APIRouter()

@router.post("/interview/finish")
def finish_interview(payload: InterviewFinishRequest, db: Session = Depends(get_db)):
    if not payload.scores:
        raise HTTPException(status_code=400, detail="Список оценок пуст")
        
    avg_score = round(sum(payload.scores) / len(payload.scores), 1)
    
    new_session = InterviewSession(
        session_id=payload.session_id,
        user_id=payload.user_id,
        direction=payload.direction,
        topic=payload.topic,
        questions_count=len(payload.scores),
        avg_score=avg_score
    )
    db.add(new_session)
    
    for score in payload.scores:
        attempt = QuestionAttempt(
            user_id=payload.user_id,
            session_id=payload.session_id,
            topic=payload.topic,
            score=score
        )
        db.add(attempt)
        
    try:
        db.commit()
        return {"status": "saved", "session_id": payload.session_id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка сохранения в БД: {str(e)}")


@router.get("/history", response_model=list[SessionHistoryResponse])
def get_history(user_id: str = Query(...), db: Session = Depends(get_db)):
    sessions = db.query(InterviewSession).filter(InterviewSession.user_id == user_id).order_by(InterviewSession.date.desc()).all()
    return sessions


@router.get("/stats/weak-topics", response_model=list[WeakTopicResponse])
def get_weak_topics(user_id: str = Query(...), db: Session = Depends(get_db)):
    results = (
        db.query(
            QuestionAttempt.topic,
            func.avg(QuestionAttempt.score).label("avg_score")
        )
        .filter(QuestionAttempt.user_id == user_id)
        .group_by(QuestionAttempt.topic)
        .order_by("avg_score")
        .all()
    )
    
    return [{"topic": row.topic, "avg_score": round(row.avg_score, 1)} for row in results]