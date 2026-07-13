import streamlit as st
from api_client import get_question, get_question_options, submit_answer, APIError
from auth import ensure_user
from mock_api import DIRECTIONS

st.set_page_config(page_title="Режим вопросов", page_icon=None)
user_id = ensure_user()

st.title("Режим вопросов")

if not user_id:
    st.warning("Введи своё имя в меню слева, чтобы продолжить.")
    st.stop()

try:
    question_options = get_question_options()
except APIError as e:
    st.error(f"Не удалось загрузить список вопросов с сервера: {e}")
    question_options = {
        "directions": DIRECTIONS,
        "topics_by_direction": {},
        "difficulties_by_direction_topic": {},
    }

directions = question_options.get("directions") or []
topics_by_direction = question_options.get("topics_by_direction") or {}
difficulties_by_direction_topic = question_options.get("difficulties_by_direction_topic") or {}

if st.session_state.get("q_direction") not in directions:
    st.session_state.pop("q_direction", None)
    st.session_state.pop("q_topic", None)
    st.session_state.pop("q_difficulty", None)

selected_direction = st.session_state.get("q_direction")
available_topics = topics_by_direction.get(selected_direction, []) if selected_direction else []

if st.session_state.get("q_topic") not in available_topics:
    st.session_state.pop("q_topic", None)
    st.session_state.pop("q_difficulty", None)

selected_topic = st.session_state.get("q_topic")
available_difficulties = (
    difficulties_by_direction_topic
    .get(selected_direction, {})
    .get(selected_topic, [])
    if selected_direction and selected_topic
    else []
)

if st.session_state.get("q_difficulty") not in available_difficulties:
    st.session_state.pop("q_difficulty", None)

# --- выбор направления/темы/уровня и получение вопроса ---
col1, col2, col3 = st.columns(3)
with col1:
    direction = st.selectbox(
        "Направление",
        directions,
        index=None,
        placeholder="Выберите направление",
        key="q_direction",
    )
with col2:
    topic = st.selectbox(
        "Тема",
        available_topics,
        index=None,
        placeholder=(
            "Выберите тему"
            if available_topics
            else "Сначала выберите направление"
            if not direction
            else "Нет тем для направления"
        ),
        key="q_topic",
        disabled=not direction or not available_topics,
    )
with col3:
    difficulty = st.selectbox(
        "Уровень",
        available_difficulties,
        index=None,
        placeholder=(
            "Выберите уровень"
            if available_difficulties
            else "Сначала выберите тему"
            if not topic
            else "Нет уровней для темы"
        ),
        key="q_difficulty",
        disabled=not topic or not available_difficulties,
    )

can_request_question = bool(direction and topic and difficulty)

if st.button("Получить вопрос", type="primary", disabled=not can_request_question):
    st.session_state.pop("last_result", None)
    try:
        with st.spinner("Подбираем вопрос..."):
            question = get_question(direction, topic, difficulty)
        st.session_state["current_question"] = question
    except APIError as e:
        st.session_state.pop("current_question", None)
        st.session_state.pop("last_result", None)
        st.error(str(e))
        st.stop()

# --- показ вопроса и формы ответа ---
if "current_question" in st.session_state:
    q = st.session_state["current_question"]

    is_current_question = (
        q.get("question_id") != "default_id"
        and q.get("direction") == direction
        and q.get("topic") == topic
        and q.get("difficulty") == difficulty
    )

    if not is_current_question:
        st.session_state.pop("current_question", None)
        st.session_state.pop("last_result", None)
        q = None

if "current_question" in st.session_state:
    q = st.session_state["current_question"]

    st.info(f"**[{q['direction']} · {q['topic']} · {q['difficulty']}]**\n\n{q['text']}")
    
    with st.form(f"answer_form_{q['question_id']}", clear_on_submit=False):
        answer = st.text_area("Твой ответ", height=150, key=f"q_answer_{q['question_id']}")
        submitted = st.form_submit_button("Отправить ответ")
        
    if submitted:
        if not answer.strip():
            st.warning("Сначала введи ответ.")
        else:
            try:
                with st.spinner("Проверяем ответ..."):
                    result = submit_answer(user_id, q["question_id"], q["topic"], answer)
                st.session_state["last_result"] = result
            except APIError as e:
                st.error(str(e))
                
    # --- разбор ---
    if "last_result" in st.session_state:
        r = st.session_state["last_result"]
        st.divider()
        st.metric("Оценка", f"{r['score']} / 5")

        if r["score"] >= 4:
            st.success(r["feedback"])
        elif r["score"] == 3:
            st.warning(r["feedback"])
        else:
            st.error(r["feedback"])
else:
    st.caption("Выбери направление, тему и уровень, затем нажми «Получить вопрос».")
