import random

import streamlit as st


def initialize_game() -> None:
    st.session_state.secret_number = random.randint(1, 100)
    st.session_state.attempts = 0
    st.session_state.message = ""
    st.session_state.finished = False


def check_guess(guess: int) -> None:
    st.session_state.attempts += 1
    secret_number = st.session_state.secret_number

    if guess < secret_number:
        st.session_state.message = "업! 더 큰 숫자를 선택하세요."
    elif guess > secret_number:
        st.session_state.message = "다운! 더 작은 숫자를 선택하세요."
    else:
        st.session_state.message = f"정답입니다! {st.session_state.attempts}번 만에 맞추셨습니다."
        st.session_state.finished = True


def main() -> None:
    st.title("숫자 맞추기 게임")
    st.write("1부터 100 사이의 숫자를 맞춰보세요.")

    if "secret_number" not in st.session_state:
        initialize_game()

    if st.session_state.finished:
        st.success(st.session_state.message)
        if st.button("다시 시작"):
            initialize_game()
        return

    guess = st.number_input("숫자를 입력하세요", min_value=1, max_value=100, value=50, step=1)
    submitted = st.button("확인")

    if submitted:
        check_guess(guess)

    if st.session_state.message:
        st.info(st.session_state.message)

    st.write(f"현재 시도 횟수: {st.session_state.attempts}")


if __name__ == "__main__":
    main()
