import streamlit as st
from api_client import get_question, submit_answer, get_real_topics, APIError
from auth import ensure_user
from mock_api import DIRECTIONS, DIFFICULTIES

st.set_page_config(page_title="Режим вопросов", page_icon=None)
user_id = ensure_user()

st.title("Режим вопросов")

if not user_id:
    st.warning("Введи своё имя в меню слева, чтобы продолжить.")
    st.stop()

@st.cache_data(ttl=300, show_spinner=False)
def _load_topics_for_direction(direction: str):
    return get_real_topics(direction)


# --- выбор направления/темы/уровня и получение вопроса ---
col1, col2, col3 = st.columns(3)
with col1:
    direction = st.selectbox("Направление", DIRECTIONS, key="q_direction")

try:
    available_topics = _load_topics_for_direction(direction)
    if not available_topics:
        st.info(f"Для направления «{direction}» в базе пока нет вопросов ни по одной теме.")
        available_topics = ["Тем пока нет"]
except APIError as e:
    st.error(f"Не удалось загрузить темы с сервера: {e}")
    available_topics = ["Алгоритмы", "SQL", "Machine Learning"]

with col2:
    topic = st.selectbox("Тема", available_topics, key=f"q_topic_{direction}")
with col3:
    difficulty = st.selectbox("Уровень", DIFFICULTIES, index=1, key="q_difficulty")

if st.button("Получить вопрос", type="primary", disabled=(topic == "Тем пока нет")):
    try:
        with st.spinner("Подбираем вопрос..."):
            st.session_state["current_question"] = get_question(direction, topic, difficulty)
        st.session_state.pop("last_result", None)
    except APIError as e:
        st.error(str(e))

# --- показ вопроса и формы ответа ---
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
