import requests
import mock_api

USE_MOCK = False
BASE_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 10


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
    return _request("GET", "/api/question", params={"direction": direction, "topic": topic, "difficulty": difficulty})


def submit_answer(user_id: str, question_id: str, topic: str, answer_text: str):
    if USE_MOCK:
        return mock_api.submit_answer(user_id, question_id, topic, answer_text)
    return _request("POST", "/api/answer", json={
        "user_id": user_id, "question_id": question_id, "topic": topic, "answer": answer_text,
    })


def start_interview(direction: str, topic: str):
    if USE_MOCK:
        return mock_api.start_interview(direction, topic)
    return _request("POST", "/api/interview/start", json={"direction": direction, "topic": topic})


def send_interview_message(user_id, session_id, direction, topic, user_message, question_number, current_difficulty):
    if USE_MOCK:
        return mock_api.send_interview_message(
            user_id, session_id, direction, topic, user_message, question_number, current_difficulty
        )
    return _request("POST", "/api/interview/message", json={
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
    return _request("POST", "/api/interview/finish", json={
        "user_id": user_id, "session_id": session_id,
        "direction": direction, "topic": topic, "scores": scores,
    })


def get_history(user_id: str):
    if USE_MOCK:
        return mock_api.get_history(user_id)
    return _request("GET", "/api/history", params={"user_id": user_id})


def get_weak_topics(user_id: str):
    if USE_MOCK:
        return mock_api.get_weak_topics(user_id)
    return _request("GET", "/api/stats/weak-topics", params={"user_id": user_id})


def get_real_topics():
    return _request("GET", "/api/topics")
