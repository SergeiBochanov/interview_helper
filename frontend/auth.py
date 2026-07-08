"""
Простая идентификация пользователя для демо/защиты практики.

В реальной системе здесь будет полноценный логин (или Telegram user_id,
если интерфейс — бот). Пока бэкенда с авторизацией нет, используем имя,
которое пользователь один раз вводит в сайдбаре — оно хранится в
st.session_state и используется как user_id для истории/статистики.
"""

import streamlit as st


def ensure_user() -> str:
    """Показать в сайдбаре поле имени пользователя, вернуть текущий user_id.

    Возвращает пустую строку, если имя ещё не введено — страницы должны
    сами решить, блокировать ли контент до ввода имени.
    """
    with st.sidebar:
        st.subheader("Пользователь")
        default = st.session_state.get("user_id", "")
        name = st.text_input("Имя (для сохранения истории)", value=default, key="user_id_input")
        st.session_state["user_id"] = name.strip()
        if name.strip():
            st.caption(f"Ты вошёл как **{name.strip()}**")
        else:
            st.caption("Введи имя, чтобы твоя история сохранялась отдельно от других.")
    return st.session_state["user_id"]
