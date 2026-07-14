import streamlit as st
from api_client import start_interview, send_interview_message, finish_interview, get_question_options, APIError
from auth import ensure_user
from mock_api import DIRECTIONS

st.set_page_config(page_title="Интервью", page_icon=None)
user_id = ensure_user()

st.title("Режим интервью")

if not user_id:
    st.warning("Введи своё имя в меню слева, чтобы продолжить.")
    st.stop()

# --- старт сессии ---
if "interview" not in st.session_state:
    try:
        question_options = get_question_options()
    except APIError as e:
        st.error(f"Не удалось загрузить список вопросов с сервера: {e}")
        question_options = {
            "directions": DIRECTIONS,
            "topics_by_direction": {},
        }

    directions = question_options.get("directions") or []
    topics_by_direction = question_options.get("topics_by_direction") or {}

    if st.session_state.get("interview_direction") not in directions:
        st.session_state.pop("interview_direction", None)
        st.session_state.pop("interview_topic", None)

    selected_direction = st.session_state.get("interview_direction")
    available_topics = topics_by_direction.get(selected_direction, []) if selected_direction else []

    if st.session_state.get("interview_topic") not in available_topics:
        st.session_state.pop("interview_topic", None)
        
    col1, col2 = st.columns(2)
    with col1:
        direction = st.selectbox(
            "Направление",
            directions,
            index=None,
            placeholder="Выберите направление",
            key="interview_direction",
        )
    with col2:
        topic = st.selectbox(
            "Тема для старта",
            available_topics,
            index=None,
            placeholder=(
                "Выберите тему"
                if available_topics
                else "Сначала выберите направление"
                if not direction
                else "Нет тем для направления"
            ),
            key="interview_topic",
            disabled=not direction or not available_topics,
        )

    can_start_interview = bool(direction and topic)

    if st.button("Начать интервью", type="primary", disabled=not can_start_interview):
        try:
            with st.spinner("Готовим интервьюера..."):
                data = start_interview(direction, topic)
        except APIError as e:
            st.error(str(e))
            st.stop()
            
        st.session_state["interview"] = {
            "session_id": data["session_id"],
            "direction": direction,
            "topic": topic,
            "current_difficulty": data["current_difficulty"],
            "question_number": data["question_number"],
            "scores": [],
        }
        st.session_state["chat_history"] = [
            {"role": "assistant", "content": data["message"]}
        ]
        st.rerun()
    st.stop()

interview = st.session_state["interview"]

# --- шапка с текущим уровнем сложности (демонстрация адаптации) ---
st.caption(
    f"Направление: **{interview['direction']}** · Тема: **{interview['topic']}** · "
    f"Текущий уровень сложности: "
    f"**{interview['current_difficulty']}** · Вопрос №{interview['question_number']}"
)

# --- история диалога ---
for msg in st.session_state["chat_history"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# --- ввод ответа пользователя ---
user_input = st.chat_input("Введи ответ на вопрос интервьюера...")
if user_input:
    with st.chat_message("user"):
        st.write(user_input)
    try:
        with st.spinner("Интервьюер оценивает ответ..."):
            result = send_interview_message(
                user_id, interview["session_id"], interview["direction"], interview["topic"],
                user_input, interview["question_number"], interview["current_difficulty"],
            )
    except APIError as e:
        st.error(str(e))
        st.info("Ответ не сохранён из-за ошибки связи — можно ввести его ещё раз.")
        st.stop()
        
    interview["scores"].append(result["score"])
    interview["question_number"] = result["question_number"]
    interview["topic"] = result.get("next_topic", interview["topic"])
    
    # Контур интервью не присылает флаг "изменилась ли сложность" —
    # сравниваем сами старое значение с calculated_next_difficulty
    new_difficulty = result["calculated_next_difficulty"]
    difficulty_changed = new_difficulty != interview["current_difficulty"]
    
    feedback_text = f"**Оценка: {result['score']}/5.** {result['feedback']}"
    if difficulty_changed:
        feedback_text += f"\n\nУровень сложности изменён на **{new_difficulty}**."
    feedback_text += f"\n\n---\n\n{result['next_question']}"
    
    interview["current_difficulty"] = new_difficulty
    st.session_state["chat_history"].append({"role": "user", "content": user_input})
    st.session_state["chat_history"].append({"role": "assistant", "content": feedback_text})
    st.rerun()

st.divider()
if st.button("Завершить интервью и сохранить результат"):
    if not interview["scores"]:
        st.info("Ты пока не ответил ни на один вопрос — сохранять нечего.")
        del st.session_state["interview"]
        del st.session_state["chat_history"]
        st.rerun()
    try:
        finish_interview(
            user_id, interview["session_id"], interview["direction"],
            interview["topic"], interview["scores"],
        )
        st.success("Интервью сохранено в истории.")
        del st.session_state["interview"]
        del st.session_state["chat_history"]
        st.switch_page("pages/3_History.py")
    except APIError as e:
        st.error(str(e))