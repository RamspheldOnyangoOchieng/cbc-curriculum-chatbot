import streamlit as st
import sys
import os
from datetime import datetime

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from cbc_bot import CBCEngine, KnowledgeBase, Config

# Initialize Engine
@st.cache_resource
def get_engine():
    return CBCEngine()

engine = get_engine()

# --- PAGE CONFIG ---
st.set_page_config(
    page_title=Config.APP_TITLE,
    page_icon=Config.APP_ICON,
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- STYLING (Premium Kenyan Theme) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');

    * {
        font-family: 'Outfit', sans-serif;
    }

    /* Main Container */
    .stApp {
        background: radial-gradient(circle at top right, #0a0a0a, #000000);
        color: #e0e0e0;
    }

    /* Glassmorphism Header */
    .header-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }

    h1 {
        background: linear-gradient(90deg, #FFFFFF, #BB0000, #006600);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3.5rem !important;
        margin-bottom: 0.5rem !important;
    }

    .badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 50px;
        background: rgba(187, 0, 0, 0.2);
        color: #FF4D4D;
        font-weight: 600;
        font-size: 0.9rem;
        border: 1px solid rgba(187, 0, 0, 0.3);
        margin-bottom: 1rem;
    }

    /* Chat Bubbles */
    .chat-bubble {
        padding: 1.5rem;
        border-radius: 20px;
        margin-bottom: 1.5rem;
        line-height: 1.6;
        max-width: 85%;
        position: relative;
        animation: fadeIn 0.5s ease-out;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .user-bubble {
        background: linear-gradient(135deg, #1a1a1a, #262626);
        color: #eee;
        border-left: 5px solid #BB0000;
        margin-left: auto;
        border-bottom-right-radius: 4px;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.3);
    }

    .bot-bubble {
        background: linear-gradient(135deg, #003300, #005500);
        color: #fff;
        border-right: 5px solid #00AA00;
        margin-right: auto;
        border-bottom-left-radius: 4px;
        box-shadow: -5px 5px 15px rgba(0,0,0,0.3);
    }

    /* Quick Info Cards */
    .info-card {
        background: rgba(255, 255, 255, 0.03);
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        margin-bottom: 1rem;
    }

    .info-card strong {
        color: #00AA00;
    }

    /* Custom Input */
    .stChatInputContainer {
        border-top: none !important;
        background: transparent !important;
    }

    .stChatInput div {
        background: rgba(255, 255, 255, 0.05) !important;
        border-radius: 15px !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    /* Hide default streamlit branding */
    div[data-testid="stStatusWidget"] { visibility: hidden; }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.markdown(f"""
<div class="header-container">
    <div class="badge">PRO VERSION 2.0</div>
    <h1>{Config.APP_ICON} {Config.APP_TITLE}</h1>
    <p style="color: #888; font-size: 1.1rem;">Official CBC Transition Guide & Pathway Expert</p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR (Context & Fast Facts) ---
with st.sidebar:
    st.markdown("### 📋 Fast Facts")
    st.markdown("""
    <div class="info-card">
        <strong>Reporting Date:</strong><br>
        Jan 12, 2026
    </div>
    <div class="info-card">
        <strong>Learners Placed:</strong><br>
        1.13 Million
    </div>
    <div class="info-card">
        <strong>Pathways:</strong><br>
        STEM, Social Sciences, Arts
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = [{"role": "system", "content": KnowledgeBase.get_system_prompt()}]
        st.rerun()

# --- CHAT LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": KnowledgeBase.get_system_prompt()}]

# Display messages
for message in st.session_state.messages[1:]:  # Skip system prompt
    role_class = "user-bubble" if message["role"] == "user" else "bot-bubble"
    st.markdown(f"""
    <div class="chat-bubble {role_class}">
        {message["content"]}
    </div>
    """, unsafe_allow_html=True)

# Chat Input
if prompt := st.chat_input("How can I help you with Grade 10 transition today?"):
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Show user bubble
    st.markdown(f'<div class="chat-bubble user-bubble">{prompt}</div>', unsafe_allow_html=True)
    
    # Generate bot response
    with st.spinner("Analyzing CBC database..."):
        try:
            response = engine.get_chat_response(st.session_state.messages)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.markdown(f'<div class="chat-bubble bot-bubble">{response}</div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Something went wrong: {e}")

# Footer attribution
st.markdown(f"""
<p style="text-align: center; color: #555; font-size: 0.8rem; margin-top: 3rem;">
    &copy; {datetime.now().year} CBE Expert System | Data accurate as of Jan 2026
</p>
""", unsafe_allow_html=True)
