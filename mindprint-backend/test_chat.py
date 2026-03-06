import streamlit as st
import requests
import json
import uuid

# --- CONFIGURATION ---
BASE_URL = "http://127.0.0.1:8000/api" # Using 127.0.0.1 to avoid localhost resolution issues

st.set_page_config(page_title="MindPrint: Digital Twin Tester", page_icon="🧠", layout="centered")

# --- STYLING ---
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        background-color: #4a90e2;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "rental_token" not in st.session_state:
    st.session_state.rental_token = ""

if "backend_url" not in st.session_state:
    st.session_state.backend_url = "http://127.0.0.1:8000/api"

# --- SIDEBAR ---
with st.sidebar:
    st.title("🧠 MindPrint Setup")
    
    # Custom Backend URL
    backend_input = st.text_input("Backend API URL", value=st.session_state.backend_url)
    if backend_input != st.session_state.backend_url:
        st.session_state.backend_url = backend_input
    
    # Simple Health Check
    try:
        # Check health endpoint (assuming it's at /health relative to the base URL)
        # Our main health is at /api/health
        health_url = st.session_state.backend_url.replace("/api", "/api/health") if "/api" in st.session_state.backend_url else f"{st.session_state.backend_url}/health"
        health_resp = requests.get(health_url, timeout=2)
        if health_resp.status_code == 200:
            st.success("✅ Backend Online")
        else:
            st.warning(f"⚠️ Status: {health_resp.status_code}")
    except:
        st.error("❌ Backend Offline")

    st.write("Enter your Rental Token to begin chatting.")
    
    token_input = st.text_input("Rental Token", value=st.session_state.rental_token, type="password")
    if token_input != st.session_state.rental_token:
        st.session_state.rental_token = token_input
        st.session_state.messages = [] # Reset chat when token changes
    
    st.divider()
    if st.button("Clear Chat Memory"):
        st.session_state.messages = []
        st.rerun()

    st.info("""
    **Multi-Turn Enabled**: This UI uses Mem0 for semantic context. 
    **Universal Skills**: Try asking "How do I do X?" to trigger skill discovery.
    """)

# --- MAIN CHAT INTERFACE ---
st.title("🤝 Chat with your Digital Twin")

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("Ask your persona anything..."):
    # Display user message in chat message container
    st.chat_message("user").markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    if not st.session_state.rental_token:
        st.error("Please enter a Rental Token in the sidebar first!")
    else:
        with st.spinner("Twin is thinking..."):
            try:
                # Prepare payload for MindPrint Backend
                payload = {
                    "token": st.session_state.rental_token,
                    "query": prompt
                }
                
                # Call Consult Endpoint
                response = requests.post(f"{st.session_state.backend_url}/consult", json=payload, timeout=60)
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "No response received.")
                    
                    # Display assistant response
                    with st.chat_message("assistant"):
                        st.markdown(answer)
                    
                    # Add assistant response to history
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                else:
                    error_detail = response.json().get("detail", "Unknown error")
                    st.error(f"Error ({response.status_code}): {error_detail}")
                    
            except requests.exceptions.ConnectionError:
                st.error(f"Could not connect to the backend at {st.session_state.backend_url}. Is FastAPI running?")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
