import os
import chromadb

from app.services.chroma_service import get_embedding


CHROMA_DB_PATH = os.path.join(os.getcwd(), "chroma_db")

chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

questions_collection = chroma_client.get_or_create_collection(
    name="interview_questions",
    metadata={"hnsw:space": "cosine"}
)


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
