import streamlit as st
from auth import ensure_user

st.set_page_config(page_title="ИИ-помощник для собеседований", layout="centered")

user_id = ensure_user()

st.title("ИИ-помощник для подготовки к собеседованиям")

if not user_id:
    st.warning("Сначала введи своё имя в меню слева — это нужно, чтобы сохранять твою историю отдельно от других.")
    st.stop()

st.write(
    "Выбери режим работы слева в меню (страницы «Вопросы», «Интервью», «История») "
    "или воспользуйся кнопками ниже."
)

col1, col2 = st.columns(2)
with col1:
    with st.container(height=110, border=False):
        st.subheader("Режим вопросов")
        st.write("Получи вопрос по теме и разбор своего ответа.")
    if st.button("Перейти к вопросам", width="stretch"):
        st.switch_page("pages/1_Questions.py")

with col2:
    with st.container(height=110, border=False):
        st.subheader("Интервью")
        st.write("Пройди диалог с интервьюером с адаптивной сложностью.")
    if st.button("Начать интервью", width="stretch"):
        st.switch_page("pages/2_Interview.py")

st.divider()
st.subheader("История и статистика")
st.write("Посмотри динамику своих оценок и слабые темы.")
if st.button("Открыть историю"):
    st.switch_page("pages/3_History.py")