import streamlit as st
import sqlite3
import pandas as pd
import os

# Config
DB_FILE = "mindprint.db"
DATA_DIR = "data"

st.set_page_config(
    page_title="MindPrint Marketplace",
    layout="wide"
)

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    return conn

def load_personas():
    if not os.path.exists(DB_FILE):
        return pd.DataFrame()
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT id, created_at FROM personas ORDER BY created_at DESC", conn)
    conn.close()
    return df

def get_persona_content(persona_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT filepath FROM personas WHERE id = ?", (persona_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row and os.path.exists(row[0]):
        with open(row[0], "r", encoding="utf-8") as f:
            return f.read()
    return "Persona content not found."

# --- Sidebar ---
with st.sidebar:
    st.title("Settings & Help")
    st.markdown("""
    ### 🚀 How to use
    1. **Share**: Type `tecorb` in your nanobot to upload your persona.
    2. **Take**: Find a persona ID you like here.
    3. **Apply**: Type `tecorb pull <ID>` in your nanobot.
    """)
    st.divider()
    st.info("Your personas are stored privately and safely stripped of all PII.")

# --- Main App ---
st.title("MindPrint Persona Marketplace")
st.subheader("Discover and adopt expert cognitive patterns")

# Add a mock login/signup for the concept
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'role' not in st.session_state:
    st.session_state.role = "Renter"
if 'username' not in st.session_state:
    st.session_state.username = "User"

if not st.session_state.logged_in:
    with st.container(border=True):
        st.write("### Sign Up / Log In to the Marketplace")
        user_name = st.text_input("Username", placeholder="Enter your name")
        role = st.radio("I want to:", ["Rent out my persona (Sharer)", "Find a persona to use (Renter)"])
        
        if st.button("Enter Marketplace"):
            if user_name:
                st.session_state.username = user_name
                st.session_state.role = role
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Please enter a username.")
else:
    st.write(f"Welcome back, **{st.session_state.username}**! Role: `{st.session_state.role}`")
    
    if "Sharer" in st.session_state.role:
        with st.expander("🛠️ How to start sharing your nanobot", expanded=True):
            st.info("Copy the prompt below and paste it into your existing nanobot agent to start syncing.")
            sharer_prompt = """I want to join the MindPrint marketplace. Please install the MindPrint skill and its dependencies into my workspace at `~/.nanobot/workspace/skills/mindprint/`. 

Once installed, immediately activate the skill by acknowledging that I have provided the subscription key: `tecorb`. Start the first sync and schedule the daily background cron task."""
            st.code(sharer_prompt, language="text")
            st.button("Copy Prompt", key="copy_sharer")
    
    # Marketplace Layout
    df = load_personas()
    
    if df.empty:
        st.warning("No personas have been shared yet. Be the first!")
    else:
        # Search / Filter
        search_query = st.text_input("🔍 Search Personas", placeholder="Enter ID...")
        if search_query:
            df = df[df['id'].str.contains(search_query, case=False)]
        
        # Display Grid
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write("### Available Personas")
            # Create a selection list
            selected_id = st.selectbox("Select a Persona to preview", df['id'].tolist())
            
        with col2:
            if selected_id:
                st.write(f"### Persona: `{selected_id}`")
                
                # Command display
                st.write("#### 🚀 How to adopt this persona")
                st.info("Paste this into your nanobot to immediately adopt these cognitive patterns:")
                renter_prompt = f"""I want to adopt a new cognitive persona from the MindPrint marketplace. 1. If I don't have it, install the MindPrint skill and scripts into `~/.nanobot/workspace/skills/mindprint/`. 2. Then, run the pull command: `tecorb pull {selected_id}`. 3. After pulling, ingest the thinking patterns from that file and use them to guide our future conversations."""
                st.code(renter_prompt, language="text")
                
                # Content Preview
                content = get_persona_content(selected_id)
                with st.expander("Preview Cognitive Patterns", expanded=True):
                    st.markdown(content)
                
                if st.button("Adopt this Persona"):
                    st.success(f"Command copied to clipboard (simulated)! Now go tell your nanobot: `tecorb pull {selected_id}`")

st.divider()
st.caption("Powered by nanobot & MindPrint-Backend")
