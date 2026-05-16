import streamlit as st
import datetime

st.title("Counter Example")

if "count" not in st.session_state:
    st.session_state.count = 0
    st.session_state.last_updated = datetime.datetime.now().strftime("%H:%M:%S")

def update_counter():
    st.session_state.count += st.session_state.increment_value
    st.session_state.last_updated = datetime.datetime.now().strftime("%H:%M:%S")

with st.form(key="my_form"):
    st.number_input(
        "Enter a value",
        value=0,
        step=1,
        key="increment_value"
    )

    st.form_submit_button(
        label="Update",
        on_click=update_counter
    )

st.write("Current Count =", st.session_state.count)
st.write("Last Updated =", st.session_state.last_updated)