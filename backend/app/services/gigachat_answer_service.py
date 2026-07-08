import os
from gigachat import GigaChat
from dotenv import load_dotenv
load_dotenv()

GIGACHAT_CREDENTIALS = os.getenv("GIGACHAT_CREDENTIALS")


def build_context(candidates: list[dict]) -> str:
    chunks = []

    for index, candidate in enumerate(candidates, start=1):
        chunks.append(f"""
[{index}]
Вопрос из базы: {candidate.get("question", "")}
Эталонный ответ: {candidate.get("answer", "")}
Направление: {candidate.get("direction", "")}
Тема: {candidate.get("topic", "")}
Сложность: {candidate.get("difficulty", "")}
""".strip())

    return "\n\n".join(chunks)


def ask_gigachat_with_context(user_query: str, context: str) -> str:
    if not GIGACHAT_CREDENTIALS:
        raise RuntimeError("GIGACHAT_CREDENTIALS не задан")

    prompt = f"""
Ты ИИ-помощник для подготовки к техническим собеседованиям.

Отвечай на вопрос пользователя, используя контекст из базы знаний.
Если в контексте нет достаточной информации, честно скажи, что в базе знаний нет точного материала.

Контекст из базы знаний:
{context}

Вопрос пользователя:
{user_query}

Дай понятный ответ с объяснением.
""".strip()

    with GigaChat(
        credentials=GIGACHAT_CREDENTIALS,
        verify_ssl_certs=False,
    ) as giga:
        response = giga.chat({
            "model": "GigaChat-Pro",
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2
        })

    return response.choices[0].message.content
