import streamlit as st
from scheduler import start_scheduler
import threading

st.title("Meesho → Facebook Marketplace Auto Poster (Scheduled)")

product_link = st.text_input("Enter Meesho product link:")
email = st.text_input("Facebook Email")
password = st.text_input("Facebook Password", type="password")
run_time = st.time_input("Choose daily post time:")

if st.button("Start Auto Posting"):
    if not product_link or not email or not password:
        st.warning("Please fill all fields!")
    else:
        st.success(f"Scheduler started! Will post daily at {run_time}.")
        threading.Thread(target=start_scheduler, args=(email, password, product_link, run_time.strftime("%H:%M")), daemon=True).start()
