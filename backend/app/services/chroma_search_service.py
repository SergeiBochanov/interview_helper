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
