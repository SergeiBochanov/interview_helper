from app.services.chroma_search_service import search_top_questions
from app.services.reranker_service import rerank_candidates
from app.services.gigachat_answer_service import build_context, ask_gigachat_with_context


def retrieve_questions(
    query: str,
    top_n: int = 20,
    top_k: int = 5,
    use_reranker: bool = True,
) -> list[dict]:
    candidates = search_top_questions(
        query=query,
        n_results=top_n,
    )

    if not use_reranker:
        return candidates[:top_k]

    return rerank_candidates(
        query=query,
        candidates=candidates,
        top_k=top_k,
    )


def generate_rag_answer(
    query: str,
    top_n: int = 20,
    top_k: int = 5,
) -> dict:
    sources = retrieve_questions(
        query=query,
        top_n=top_n,
        top_k=top_k,
        use_reranker=True,
    )

    context = build_context(sources)

    answer = ask_gigachat_with_context(
        user_query=query,
        context=context,
    )

    return {
        "answer": answer,
        "sources": sources,
    }
