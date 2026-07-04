from fastapi import APIRouter, HTTPException, status
from app.schemas.parser import ParseUrlRequest, BatchAddQuestionsRequest, ProcessStatusResponse
from app.services.parser_utils import extract_text_from_url
from app.services.chroma_service import generate_questions_from_text, check_and_save_question

router = APIRouter()

@router.post("/process-url", response_model=ProcessStatusResponse)
async def process_url_endpoint(payload: ParseUrlRequest):
    """
    Эндпоинт полного цикла: скачивает статью по URL, извлекает текст,
    генерирует вопросы через GigaChat, проверяет на дубликаты и сохраняет в ChromaDB.
    Устойчив к ошибкам парсинга и нецелевым темам контента.
    """
    try:
        try:
            text = extract_text_from_url(payload.url)
        except Exception as url_err:
            return ProcessStatusResponse(
                status="error", 
                details={"message": f"Не удалось извлечь текст из ссылки: {str(url_err)}"}
            )
        
        questions = generate_questions_from_text(text)
        
        if not questions:
            return ProcessStatusResponse(
                status="rejected", 
                details={"message": "Тематика статьи не подходит под целевые направления (Backend, Frontend, Data Science, Data Analyst)."}
            )
        
        stats = {"added": 0, "duplicate": 0}
        for q in questions:
            status_res = check_and_save_question(q)
            stats[status_res] += 1
            
        return ProcessStatusResponse(status="success", details=stats)
        
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/batch-add", response_model=ProcessStatusResponse)
async def batch_add_endpoint(payload: BatchAddQuestionsRequest):
    """
    Эндпоинт для прямой загрузки уже готовых вопросов (массивом JSON) с проверкой на дубликаты.
    """
    try:
        stats = {"added": 0, "duplicate": 0}
        for q in payload.questions:
            status_res = check_and_save_question(q.model_dump())
            stats[status_res] += 1
            
        return ProcessStatusResponse(status="success", details=stats)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))