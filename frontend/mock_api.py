"""
Заглушка API бэкенда (Контур поиска / Контур интервью).

Формат данных здесь синхронизирован с уже написанным кодом сокомандников:
- backend/app/schemas/parser.py (Контур сбора данных) — поле direction/topic/difficulty
- interviewer.py (Контур интервью) — шкала оценки 1..5, поля score/feedback/
  calculated_next_difficulty, правило смены сложности (4-5 повышает, 3 без
  изменений, 1-2 понижает).

Когда реальный FastAPI будет готов, нужно заменить функции в api_client.py
на настоящие HTTP-запросы, сохранив те же имена полей в ответах.
"""

import random
import time
import uuid
from collections import defaultdict
from datetime import datetime, timedelta

DIRECTIONS = ["Backend", "Frontend", "Data Science", "Data Analyst"]
TOPICS = ["Алгоритмы", "SQL", "Системный дизайн", "Machine Learning", "Поведенческие"]
DIFFICULTIES = ["Junior", "Middle", "Senior"]

_QUESTIONS_BANK = {
    "Алгоритмы": [
        "Как устроен алгоритм быстрой сортировки и какова его сложность в среднем и худшем случае?",
        "Что такое двоичное дерево поиска и как в нём происходит вставка элемента?",
    ],
    "SQL": [
        "В чём разница между INNER JOIN и LEFT JOIN? Приведи пример.",
        "Что такое индекс в базе данных и когда он может замедлить, а не ускорить запрос?",
    ],
    "Системный дизайн": [
        "Спроектируй укрупнённо систему сокращения URL. Какие компоненты нужны?",
        "Как бы ты организовал кэширование для высоконагруженного API?",
    ],
    "Machine Learning": [
        "В чём разница между bagging и boosting?",
        "Что такое переобучение и какими способами с ним борются?",
    ],
    "Поведенческие": [
        "Расскажи о ситуации, когда тебе пришлось отстаивать своё техническое решение перед командой.",
    ],
}

# история сессий и оценки по темам — раздельно по пользователям (user_id -> список)
# это имитирует то, что в реальной системе будет строкой в PostgreSQL с user_id
_SESSIONS_BY_USER: dict = defaultdict(list)
_TOPIC_SCORES_BY_USER: dict = defaultdict(lambda: defaultdict(list))


def get_question(direction: str, topic: str, difficulty: str = "Middle"):
    """Вернуть вопрос по направлению/теме (режим 'Вопросы')."""
    time.sleep(0.3)  # имитация сетевой задержки
    pool = _QUESTIONS_BANK.get(topic, _QUESTIONS_BANK["Алгоритмы"])
    return {
        "question_id": str(uuid.uuid4()),
        "direction": direction,
        "topic": topic,
        "difficulty": difficulty,
        "text": random.choice(pool),
    }


def submit_answer(user_id: str, question_id: str, topic: str, answer_text: str):
    """Отправить ответ пользователя, получить разбор (режим 'Вопросы').

    Шкала оценки — 1..5, как в InterviewAssessment (Контур интервью),
    а не 1..10. Поле verdict не возвращается бэкендом — цвет/тон вывода
    вычисляется на стороне интерфейса по числовому score (см. страницу).
    """
    time.sleep(0.5)
    score = random.randint(1, 5)
    _TOPIC_SCORES_BY_USER[user_id][topic].append(score)
    return {
        "question_id": question_id,
        "score": score,
        "feedback": (
            "Ответ полностью верный, отражает суть эталона."
            if score >= 4
            else "Ответ частично верный, но упущены важные детали из эталона."
            if score == 3
            else "Ответ значительно расходится с эталоном, нужно повторить тему."
        ),
    }


def start_interview(direction: str, topic: str):
    """Начать сессию мок-интервью."""
    time.sleep(0.3)
    session_id = str(uuid.uuid4())
    first_q = get_question(direction, topic, "Middle")
    return {
        "session_id": session_id,
        "direction": direction,
        "topic": topic,
        "message": first_q["text"],
        "current_difficulty": "Middle",
        "question_number": 1,
    }


def send_interview_message(user_id: str, session_id: str, direction: str, topic: str, user_message: str,
                            question_number: int, current_difficulty: str):
    """Отправить ответ в диалоге мок-интервью, получить оценку + следующий вопрос.

    Оценка и правило смены сложности повторяют логику evaluate_interview_answer
    из interviewer.py (Контур интервью): шкала 1..5, повышение при 4-5,
    без изменений при 3, понижение при 1-2. Поле называется
    calculated_next_difficulty, а не current_difficulty — так называет его
    реальный бэкенд. difficulty_changed бэкенд не возвращает — интерфейс
    сам сравнивает старое и новое значение (см. страницу).

    next_question/next_topic — это НЕ часть ответа Контура интервью (там
    только оценка). Подбор следующего вопроса — задача Контура поиска.
    Здесь они склеены вместе только для целостности мока; при реальной
    интеграции может понадобиться отдельный вызов за следующим вопросом.
    """
    time.sleep(0.6)
    score = random.randint(1, 5)
    _TOPIC_SCORES_BY_USER[user_id][topic].append(score)

    difficulty_order = ["Junior", "Middle", "Senior"]
    idx = difficulty_order.index(current_difficulty)
    if score >= 4 and idx < len(difficulty_order) - 1:
        idx += 1
    elif score <= 2 and idx > 0:
        idx -= 1
    calculated_next_difficulty = difficulty_order[idx]

    next_topic = random.choice(TOPICS)
    next_q = get_question(direction, next_topic, calculated_next_difficulty)

    return {
        "session_id": session_id,
        "score": score,
        "feedback": (
            "Ответ полностью совпадает по смыслу с эталоном, чёткий и без ошибок."
            if score == 5
            else "Ответ верный, отражает суть, но упущены некоторые важные детали."
            if score == 4
            else "Ответ слишком поверхностный, частично верный, содержит неточности."
            if score == 3
            else "Ответ практически неверный либо содержит посторонний текст."
        ),
        "next_question": next_q["text"],
        "next_topic": next_topic,
        "calculated_next_difficulty": calculated_next_difficulty,
        "question_number": question_number + 1,
    }


def finish_interview(user_id: str, session_id: str, direction: str, topic: str, scores: list):
    """Сохранить завершённую сессию (для истории)."""
    avg = sum(scores) / len(scores) if scores else 0
    _SESSIONS_BY_USER[user_id].append({
        "session_id": session_id,
        "date": datetime.now(),
        "direction": direction,
        "topic": topic,
        "questions_count": len(scores),
        "avg_score": round(avg, 1),
    })
    return {"status": "saved"}


def get_history(user_id: str):
    """История сессий конкретного пользователя."""
    time.sleep(0.2)
    sessions = _SESSIONS_BY_USER[user_id]
    if not sessions:
        # немного демо-данных, чтобы страница истории не была пустой при первом заходе
        base = datetime.now() - timedelta(days=10)
        return [
            {"session_id": "demo-1", "date": base + timedelta(days=i * 2),
             "direction": random.choice(DIRECTIONS), "topic": random.choice(TOPICS),
             "questions_count": random.randint(3, 8), "avg_score": round(random.uniform(2, 5), 1)}
            for i in range(5)
        ]
    return sessions


def get_weak_topics(user_id: str):
    """Статистика слабых тем пользователя — усреднённая оценка по каждой теме."""
    time.sleep(0.2)
    scores_by_topic = _TOPIC_SCORES_BY_USER[user_id]
    if not scores_by_topic:
        # демо-данные для пустой истории
        return [{"topic": t, "avg_score": round(random.uniform(1.5, 5), 1)} for t in TOPICS]
    return [
        {"topic": t, "avg_score": round(sum(scores) / len(scores), 1)}
        for t, scores in scores_by_topic.items()
    ]
