import os
import json
import uuid
import chromadb
from gigachat import GigaChat
from dotenv import load_dotenv
load_dotenv()

GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")
PROMPT_FILE_PATH = os.path.join("prompts", "question_generation.txt")

CHROMA_DB_PATH = os.path.join(os.getcwd(), "chroma_db")
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

questions_collection = chroma_client.get_or_create_collection(
    name="interview_questions",
    metadata={"hnsw:space": "cosine"}
)

topics_collection = chroma_client.get_or_create_collection(name="reference_topics")

def load_system_prompt() -> str:
    with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()

def get_embedding(text: str) -> list[float]:
    """
    Генерирует эмбеддинг через GigaChat API.
    """
    with GigaChat(credentials=GIGACHAT_CREDENTIALS, verify_ssl_certs=False) as giga:
        response = giga.embeddings(texts=[text])
        return response.data[0].embedding

def resolve_and_normalize_topic(raw_topic: str, threshold: float = 0.30) -> str:
    """
    Берет сырой топик от ИИ, ищет похожий в базе эталонных топиков.
    """
    raw_topic = raw_topic.strip()
    topic_embedding = get_embedding(raw_topic)
    
    results = topics_collection.query(
        query_embeddings=[topic_embedding],
        n_results=1
    )
    
    if results and results["distances"] and len(results["distances"][0]) > 0:
        closest_distance = results["distances"][0][0]
        closest_topic = results["documents"][0][0]
        
        if closest_distance < threshold:
            return closest_topic
            
    topic_id = f"topic_{uuid.uuid4()}"
    topics_collection.add(
        embeddings=[topic_embedding],
        documents=[raw_topic],
        ids=[topic_id],
        metadatas=[{"type": "topic"}]
    )
    return raw_topic

def generate_questions_from_text(article_text: str) -> list[dict]:
    """
    Запрашивает у GigaChat генерацию вопросов по тексту статьи.
    """
    if not article_text or len(article_text.strip()) < 100:
        return []

    system_prompt = load_system_prompt()
    user_prompt = f"Вот текст статьи для анализа:\n\n{article_text}"
    
    with GigaChat(credentials=GIGACHAT_CREDENTIALS, verify_ssl_certs=False) as giga:
        response = giga.chat({
            "model": "GigaChat-Pro",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.15
        })
        
    raw_content = response.choices[0].message.content.strip()
    if raw_content.startswith("```"):
        raw_content = raw_content.strip("`").replace("json\n", "", 1).strip()
        
    try:
        return json.loads(raw_content)
    except json.JSONDecodeError:
        fixed_content = ""
        in_string = False
        for char in raw_content:
            if char == '"':
                in_string = not in_string
            if char == '\n' and in_string:
                fixed_content += '\\n'
            else:
                fixed_content += char
        return json.loads(fixed_content)

def check_and_save_question(question_data: dict, question_threshold: float = 0.12) -> str:
    """
    Проверяет вопрос на дубликаты (используя косинусное расстояние), 
    нормализует топик и сохраняет уникальный вопрос в ChromaDB.
    """
    question_text = question_data["question"]
    query_embedding = get_embedding(question_text)
    
    results = questions_collection.query(query_embeddings=[query_embedding], n_results=1)
    
    if results and results["distances"] and len(results["distances"][0]) > 0:
        closest_distance = results["distances"][0][0]
        
        if closest_distance < question_threshold:
            return "duplicate"
            
    raw_topic = question_data.get("topic", "Общее")
    normalized_topic = resolve_and_normalize_topic(raw_topic, threshold=0.30)
    
    question_id = f"q_{uuid.uuid4()}"
    questions_collection.add(
        embeddings=[query_embedding],
        documents=[question_text],
        metadatas=[{
            "type": "question",
            "answer": question_data["answer"],
            "direction": question_data["direction"],
            "topic": normalized_topic,
            "difficulty": question_data["difficulty"]
        }],
        ids=[question_id]
    )
    return "added"
