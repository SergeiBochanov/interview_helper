import os
import chromadb

from app.services.chroma_service import get_embedding
from app.services.chroma_service import questions_collection, topics_collection

CHROMA_DB_PATH = os.path.join(os.getcwd(), "chroma_db")

chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

def search_top_questions(query: str, n_results: int = 20) -> list[dict]:
    """
    Ищет top-N похожих вопросов в ChromaDB по embedding пользовательского запроса.
    """
    query = query.strip()

    if not query:
        return []

    query_embedding = get_embedding(query)

    results = questions_collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
        include=["documents", "metadatas", "distances"]
    )

    if not results["documents"] or not results["documents"][0]:
        return []

    found = []

    for question, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        found.append({
            "question": question,
            "answer": metadata.get("answer"),
            "direction": metadata.get("direction"),
            "topic": metadata.get("topic"),
            "difficulty": metadata.get("difficulty"),
            "distance": distance,
        })

    return found

def get_all_saved_topics() -> list[str]:
    """
    Возвращает список всех уникальных эталонных топиков, сохраненных в ChromaDB.
    """
    try:
        results = topics_collection.get()
        if results and "documents" in results and results["documents"]:
            return sorted(list(set(results["documents"])))
        return []
    except Exception:
        return []


DIRECTION_ALIASES = {
    "Data Analysis": "Data Analyst",
}


def _direction_variants(direction: str) -> list[str]:
    variants = {direction}
    for raw, canonical in DIRECTION_ALIASES.items():
        if canonical == direction:
            variants.add(raw)
        if raw == direction:
            variants.add(canonical)
    return list(variants)


def get_topics_for_direction(direction: str) -> list[str]:
    if not direction:
        return []
    try:
        variants = _direction_variants(direction)
        where_clause = (
            {"direction": variants[0]}
            if len(variants) == 1
            else {"direction": {"$in": variants}}
        )
        results = questions_collection.get(
            where=where_clause,
            include=["metadatas"],
        )
        if not results or not results.get("metadatas"):
            return []
        topics = {m.get("topic") for m in results["metadatas"] if m.get("topic")}
        return sorted(topics)
    except Exception:
        return []
