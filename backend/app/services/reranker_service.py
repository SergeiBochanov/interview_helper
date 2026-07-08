from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")


def build_candidate_text(candidate: dict) -> str:
    return f"""
Вопрос: {candidate.get("question", "")}
Ответ: {candidate.get("answer", "")}
Направление: {candidate.get("direction", "")}
Тема: {candidate.get("topic", "")}
Сложность: {candidate.get("difficulty", "")}
""".strip()


def rerank_candidates(
    query: str,
    candidates: list[dict],
    top_k: int = 5,
) -> list[dict]:
    """
    Реранжирует кандидатов.
    На вход получает текст запроса и top-N кандидатов из Chroma.
    На выходе возвращает top-K лучших.
    """
    if not candidates:
        return []

    top_k = max(1, min(top_k, len(candidates)))

    pairs = [
        [query, build_candidate_text(candidate)]
        for candidate in candidates
    ]

    scores = reranker.predict(pairs)

    reranked = []

    for candidate, score in zip(candidates, scores):
        item = candidate.copy()
        item["rerank_score"] = float(score)
        reranked.append(item)

    return sorted(
        reranked,
        key=lambda item: item["rerank_score"],
        reverse=True
    )[:top_k]
