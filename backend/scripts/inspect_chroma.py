import os
import chromadb


CHROMA_DB_PATH = os.path.join(os.getcwd(), "chroma_db")

chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

questions_collection = chroma_client.get_or_create_collection(
    name="interview_questions",
    metadata={"hnsw:space": "cosine"}
)

topics_collection = chroma_client.get_or_create_collection(
    name="reference_topics",
    metadata={"hnsw:space": "cosine"}
)


def print_questions(limit: int = 10):
    print("\nКоллекция: interview_questions")
    print(f"Количество записей: {questions_collection.count()}")

    if questions_collection.count() == 0:
        print("Коллекция пустая")
        return

    data = questions_collection.get(
        limit=limit,
        include=["documents", "metadatas"]
    )

    for index, (item_id, question, metadata) in enumerate(
        zip(data["ids"], data["documents"], data["metadatas"]),
        start=1
    ):
        print("\n" + "=" * 80)
        print(f"{index}. ID: {item_id}")
        print("-" * 80)
        print(f"Вопрос: {question}")
        print()
        print(f"Ответ: {metadata.get('answer')}")
        print()
        print(f"Направление: {metadata.get('direction')}")
        print(f"Тема: {metadata.get('topic')}")
        print(f"Сложность: {metadata.get('difficulty')}")
        print(f"Тип: {metadata.get('type')}")


def print_topics(limit: int = 10):
    print("\nКоллекция: reference_topics")
    print(f"Количество записей: {topics_collection.count()}")

    if topics_collection.count() == 0:
        print("Коллекция пустая")
        return

    data = topics_collection.get(
        limit=limit,
        include=["documents", "metadatas"]
    )

    for index, (item_id, topic, metadata) in enumerate(
        zip(data["ids"], data["documents"], data["metadatas"]),
        start=1
    ):
        print("\n" + "=" * 80)
        print(f"{index}. ID: {item_id}")
        print("-" * 80)
        print(f"Тема: {topic}")
        print(f"Metadata: {metadata}")


if __name__ == "__main__":
    print_questions(limit=100)
    print_topics(limit=100)
