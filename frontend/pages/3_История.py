import pandas as pd
import streamlit as st
from api_client import get_history, get_weak_topics, APIError
from auth import ensure_user

st.set_page_config(page_title="История", page_icon=None)

user_id = ensure_user()
st.title("История и статистика")

if not user_id:
    st.warning("Введи своё имя в меню слева, чтобы продолжить.")
    st.stop()

try:
    with st.spinner("Загружаем историю..."):
        history = get_history(user_id)
        weak_topics = get_weak_topics(user_id)
except APIError as e:
    st.error(str(e))
    st.stop()

if not history:
    st.info("Пока нет пройденных сессий. Пройди режим вопросов или интервью.")
    st.stop()

df = pd.DataFrame(history).sort_values("date")

# --- динамика оценок по времени ---
st.subheader("Динамика оценок")
chart_df = df.set_index("date")[["avg_score"]].rename(columns={"avg_score": "Средняя оценка"})
st.line_chart(chart_df)

# --- слабые темы ---
st.subheader("Слабые темы")
if weak_topics:
    weak_df = pd.DataFrame(weak_topics).sort_values("avg_score")
    st.bar_chart(weak_df.set_index("topic")["avg_score"])
    weakest = weak_df.iloc[0]
    st.caption(f"Самая слабая тема сейчас: **{weakest['topic']}** (средняя оценка {weakest['avg_score']}/5).")
else:
    st.caption("Пока недостаточно данных, чтобы выделить слабые темы.")

# --- таблица сессий ---
st.subheader("Пройденные сессии")
display_df = df[["date", "direction", "topic", "questions_count", "avg_score"]].rename(columns={
    "date": "Дата", "direction": "Направление", "topic": "Тема",
    "questions_count": "Вопросов", "avg_score": "Средняя оценка",
})
st.dataframe(display_df.sort_values("Дата", ascending=False), width="stretch", hide_index=True)
