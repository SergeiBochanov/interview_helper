from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.rag_service import retrieve_questions, generate_rag_answer


router = APIRouter()


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3)
    top_n: int = Field(default=20, ge=1, le=50)
    top_k: int = Field(default=5, ge=1, le=20)
    use_reranker: bool = True


class RagAnswerRequest(BaseModel):
    query: str = Field(..., min_length=3)
    top_n: int = Field(default=20, ge=1, le=50)
    top_k: int = Field(default=5, ge=1, le=20)


@router.post("/search")
async def search_endpoint(payload: SearchRequest):
    """
    Возвращает найденные вопросы из Chroma.
    Может работать с реранкером или без него.
    """
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
    """
    Полный RAG:
    query → Chroma top-N → reranker top-K → context → GigaChat answer.
    """
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
