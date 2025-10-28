import streamlit as st
import requests

st.set_page_config(page_title="AI Interviewer", page_icon="🧠")

BACKEND_START = "http://localhost:8000/start_interview"
BACKEND_CONTINUE = "http://localhost:8000/continue_interview"

if "interview_started" not in st.session_state:
    st.session_state.interview_started = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if not st.session_state.interview_started:
    st.title("🧠 AI Interviewer Setup")

    job_title = st.text_input("💼 Job Title", placeholder="e.g. Python Developer")
    cv_file = st.file_uploader("📄 Upload your CV (optional)", type=["pdf"])

    st.subheader("🧩 Choose Question Style")
    question_style = st.radio(
        "Select how the AI should ask questions:",
        [
            "1️⃣ Broad, follow-up (general, builds on previous answers)",
            "2️⃣ Narrow, follow-up (specific, probes details from previous answers)",
            "3️⃣ Broad, non-follow-up (general, new topic aspects)",
            "4️⃣ Narrow, non-follow-up (specific, new topic aspects)",
        ],
    )

    question_type_map = {
        "1️⃣ Broad, follow-up (general, builds on previous answers)": "broad_followup",
        "2️⃣ Narrow, follow-up (specific, probes details from previous answers)": "narrow_followup",
        "3️⃣ Broad, non-follow-up (general, new topic aspects)": "broad_nonfollowup",
        "4️⃣ Narrow, non-follow-up (specific, new topic aspects)": "narrow_nonfollowup",
    }
    selected_question_type = question_type_map[question_style]

    if st.button("🚀 Start Interview"):
        if not job_title:
            st.warning("Please enter a job title.")
        else:
            files = {"cv": ("cv.pdf", cv_file, "application/pdf")} if cv_file else None
            data = {"job_title": job_title, "question_type": selected_question_type}

            try:
                response = requests.post(BACKEND_START, data=data, files=files)
                if response.status_code == 200:
                    backend_response = response.json()
                    st.session_state.interview_started = True
                    st.session_state.thread_id = backend_response.get("thread_id")
                    first_question = backend_response.get(
                        "message", "Let's begin the interview!"
                    )
                    st.session_state.messages = [
                        {"role": "assistant", "content": first_question}
                    ]
                    st.rerun()
                else:
                    st.error(f"❌ Error: {response.status_code} — {response.text}")
            except Exception as e:
                st.error(f"🚨 Backend not reachable: {e}")

else:
    st.title("💬 AI Interviewer")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Type your answer..."):
        st.session_state.messages.append({"role": "user", "content": user_input})

        try:
            response = requests.post(
                BACKEND_CONTINUE,
                json={
                    "user_response": user_input,
                    "thread_id": st.session_state.thread_id,
                },
            )
            if response.status_code == 200:
                backend_data = response.json()
                assistant_reply = backend_data.get("message", "Got it ✅")
                if isinstance(assistant_reply, list):
                    assistant_reply = "\n\n".join(
                        [str(item) for item in assistant_reply]
                    )
                st.session_state.messages.append(
                    {"role": "assistant", "content": assistant_reply}
                )
            else:
                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": f"⚠️ Backend error: {response.status_code}\n{response.text}",
                    }
                )
        except Exception as e:
            st.session_state.messages.append(
                {"role": "assistant", "content": f"🚨 Backend not reachable: {e}"}
            )

        st.rerun()
