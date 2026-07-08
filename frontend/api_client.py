"""
Единая точка входа для обращений к бэкенду.

Сейчас USE_MOCK = True — все функции ходят в mock_api.py.
Когда бэкенд-команда выкатит реальный FastAPI, нужно:
  1. Поставить USE_MOCK = False
  2. Указать BASE_URL
  3. Проверить, что реальные эндпоинты возвращают те же поля, что и mock_api

Это единственный файл, который нужно менять при переходе на настоящий API —
код страниц (pages/*.py) трогать не придётся, если бэкенд вернёт те же поля,
что и mock_api.

Все функции при сетевой ошибке или ошибке сервера бросают APIError —
страницы ловят её и показывают понятное сообщение вместо падения приложения.
"""

import requests
import mock_api

USE_MOCK = True
BASE_URL = "http://localhost:8000"  # адрес бэкенда, когда будет готов
REQUEST_TIMEOUT = 10  # секунд


class APIError(Exception):
    """Единая ошибка для UI — не важно, что именно пошло не так на сети/сервере."""
    pass


def _request(method: str, path: str, **kwargs):
    try:
        resp = requests.request(method, f"{BASE_URL}{path}", timeout=REQUEST_TIMEOUT, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        raise APIError("Сервер не отвечает слишком долго. Попробуй ещё раз чуть позже.")
    except requests.exceptions.ConnectionError:
        raise APIError("Не удаётся подключиться к серверу. Проверь, что бэкенд запущен.")
    except requests.exceptions.HTTPError as e:
        raise APIError(f"Сервер вернул ошибку: {e.response.status_code}.")
    except ValueError:
        raise APIError("Сервер вернул некорректный ответ (не JSON).")


def get_question(direction: str, topic: str, difficulty: str = "Middle"):
    if USE_MOCK:
        return mock_api.get_question(direction, topic, difficulty)
    return _request("GET", "/question", params={"direction": direction, "topic": topic, "difficulty": difficulty})


def submit_answer(user_id: str, question_id: str, topic: str, answer_text: str):
    if USE_MOCK:
        return mock_api.submit_answer(user_id, question_id, topic, answer_text)
    return _request("POST", "/answer", json={
        "user_id": user_id, "question_id": question_id, "topic": topic, "answer": answer_text,
    })


def start_interview(direction: str, topic: str):
    if USE_MOCK:
        return mock_api.start_interview(direction, topic)
    return _request("POST", "/interview/start", json={"direction": direction, "topic": topic})


def send_interview_message(user_id, session_id, direction, topic, user_message, question_number, current_difficulty):
    if USE_MOCK:
        return mock_api.send_interview_message(
            user_id, session_id, direction, topic, user_message, question_number, current_difficulty
        )
    return _request("POST", "/interview/message", json={
        "user_id": user_id,
        "session_id": session_id,
        "direction": direction,
        "topic": topic,
        "message": user_message,
        "question_number": question_number,
        "current_difficulty": current_difficulty,
    })


def finish_interview(user_id, session_id, direction, topic, scores):
    if USE_MOCK:
        return mock_api.finish_interview(user_id, session_id, direction, topic, scores)
    return _request("POST", "/interview/finish", json={
        "user_id": user_id, "session_id": session_id,
        "direction": direction, "topic": topic, "scores": scores,
    })


def get_history(user_id: str):
    if USE_MOCK:
        return mock_api.get_history(user_id)
    return _request("GET", "/history", params={"user_id": user_id})


def get_weak_topics(user_id: str):
    if USE_MOCK:
        return mock_api.get_weak_topics(user_id)
    return _request("GET", "/stats/weak-topics", params={"user_id": user_id})
