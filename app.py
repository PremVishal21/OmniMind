import streamlit as st
import os
import time
import base64
import io
from pathlib import Path
from PIL import Image
from agents import IntelligenceEngine
from database import init_db, create_user, verify_user, get_chat_history, save_chat_history

# Initialize the DB tables
init_db()

# Load Luffy icon as base64 for inline HTML usage
_luffy_path = Path(__file__).parent / "luffy_icon.png"
_luffy_b64 = base64.b64encode(_luffy_path.read_bytes()).decode() if _luffy_path.exists() else ""
# No border, no radius — clean transparent PNG side-by-side with Yo!
LUFFY_IMG = f'<img src="data:image/png;base64,{_luffy_b64}" style="width:90px;height:auto;object-fit:contain;vertical-align:middle;background:transparent;">'

# Configure the Streamlit page — PIL Image for proper favicon support
_pil_icon = Image.open(_luffy_path) if _luffy_path.exists() else "🤖"
st.set_page_config(
    page_title="OmniMind: Autonomous Multi-Agent Intelligence System",
    page_icon=_pil_icon,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
if os.path.exists("styles.css"):
    with open("styles.css", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    # Minimal fallback CSS if file missing
    st.markdown("<style>body { font-family: 'Inter', sans-serif; }</style>", unsafe_allow_html=True)

# --- Authentication ---
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'auth_mode' not in st.session_state:
    st.session_state.auth_mode = 'login'

if not st.session_state.user_id:
    # Centered single-column login — no scroll
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Macondo+Swash+Caps&family=Gravitas+One&family=Fascinate+Inline&family=Quintessential&display=swap');
        header[data-testid="stHeader"] {
            display: none !important;
        }
        [data-testid="stAppViewContainer"] > .main .block-container {
            padding-top: 4vh !important;
            padding-bottom: 2vh !important;
        }
        .login-wrapper {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 80vh;
        }
        .login-box {
            background: transparent;
            border: none;
            border-radius: 20px;
            padding: 40px 48px;
            width: 100%;
            max-width: 420px;
            margin: 0 auto;
        }
        .login-brand {
            text-align: center;
            margin-bottom: 8px;
            font-family: 'Macondo Swash Caps', cursive;
            font-size: 2.8rem;
            letter-spacing: 1px;
            background: transparent;
        }
        .login-brand .omni { color: #60a5fa; }
        .login-brand .mind { color: #c084fc; }
        .login-sub {
            text-align: center;
            font-family: 'Quintessential', serif;
            color: #9ca3af;
            font-size: 0.9rem;
            margin-bottom: 28px;
        }
        </style>
    """, unsafe_allow_html=True)

    _, center_col, _ = st.columns([1, 2, 1])
    with center_col:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown('<div class="login-brand"><span class="omni">Omni</span><span class="mind">Mind</span></div>', unsafe_allow_html=True)

        if st.session_state.auth_mode == 'login':
            st.markdown('<div class="login-sub">Sign in to your account</div>', unsafe_allow_html=True)
            user = st.text_input("Username", key="log_user", placeholder="Username / Email", label_visibility="collapsed")
            pw = st.text_input("Password", type="password", key="log_pass", placeholder="Password", label_visibility="collapsed")
            st.markdown('<p style="text-align:right;color:#B2A3A4;font-size:0.85rem;cursor:pointer;margin-top:-8px;margin-bottom:20px;">Forgot Password?</p>', unsafe_allow_html=True)

            b_c1, b_c2 = st.columns(2)
            with b_c1:
                st.markdown('<div class="primary-auth-btn">', unsafe_allow_html=True)
                if st.button("SIGN IN", use_container_width=True, key="signin_btn"):
                    if user and pw:
                        success, uid = verify_user(user, pw)
                        if success:
                            st.session_state.user_id = uid
                            st.session_state.username = user
                            st.rerun()
                        else:
                            st.error("Invalid credentials.")
                    else:
                        st.warning("Please fill all fields.")
                st.markdown('</div>', unsafe_allow_html=True)
            with b_c2:
                st.markdown('<div class="secondary-auth-btn">', unsafe_allow_html=True)
                if st.button("SIGN UP", use_container_width=True, key="signup_toggle"):
                    st.session_state.auth_mode = 'signup'
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="login-sub">Create your intelligence profile</div>', unsafe_allow_html=True)
            new_u = st.text_input("New Username", key="reg_user", placeholder="Set Username", label_visibility="collapsed")
            new_p = st.text_input("New Password", type="password", key="reg_pass", placeholder="Set Password", label_visibility="collapsed")
            st.markdown('<div style="height:14px;"></div>', unsafe_allow_html=True)

            b_c1, b_c2 = st.columns(2)
            with b_c1:
                st.markdown('<div class="primary-auth-btn">', unsafe_allow_html=True)
                if st.button("CREATE", use_container_width=True, key="create_btn"):
                    if new_u and new_p:
                        success, msg = create_user(new_u, new_p)
                        if success:
                            st.success(msg)
                            st.session_state.auth_mode = 'login'
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please fill all fields.")
                st.markdown('</div>', unsafe_allow_html=True)
            with b_c2:
                st.markdown('<div class="secondary-auth-btn">', unsafe_allow_html=True)
                if st.button("LOGIN", use_container_width=True, key="login_toggle"):
                    st.session_state.auth_mode = 'login'
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        # Social Section
        st.markdown('''
            <div class="social-login-container">
                <div class="social-line">OR LOGIN WITH</div>
                <div class="social-icons">
                    <div class="social-icon"><img src="https://img.icons8.com/color/24/000000/facebook-new.png"/></div>
                    <div class="social-icon"><img src="https://img.icons8.com/color/24/000000/google-logo.png"/></div>
                    <div class="social-icon"><img src="https://img.icons8.com/color/24/000000/linkedin.png"/></div>
                </div>
            </div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()


# --- Main App State ---
if 'history' not in st.session_state:
    st.session_state.history = get_chat_history(st.session_state.user_id)
if 'api_key' not in st.session_state:
    st.session_state.api_key = ''
if 'input_key' not in st.session_state:
    st.session_state.input_key = 0

def persist_chat():
    save_chat_history(st.session_state.user_id, st.session_state.history)

with st.sidebar:
    st.markdown("""
        <h2 style="margin:0; font-family:'Macondo Swash Caps', cursive; font-size: 2.2rem; letter-spacing: 1px;">
            <span style="color: #60a5fa;">Omni</span><span style="color: #c084fc;">Mind</span>
        </h2>
    """, unsafe_allow_html=True)
    st.markdown(f"**🟢 Currently Logged In as: {st.session_state.username}**")
    if st.button("Logout", use_container_width=True):
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.history = []
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    api_key_input = st.text_input("🔑 Gemini API Key:", type="password", value=st.session_state.api_key)
    if st.button("Save Key", use_container_width=True):
        st.session_state.api_key = api_key_input
        os.environ["GOOGLE_API_KEY"] = api_key_input
        st.success("Saved!")
        
    st.markdown("---")
    st.button("➕ New Chat", use_container_width=True, on_click=lambda: (st.session_state.history.clear(), persist_chat()))

# --- Always-visible Yo! + icon side-by-side header ---
st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Fascinate+Inline&family=Quintessential&display=swap');
        header[data-testid="stHeader"] {{ display: none !important; }}
    </style>
    <div style="
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 18px;
        padding: 36px 20px 6px 20px;
    ">
        <div style="flex-shrink:0; line-height:0;">{LUFFY_IMG}</div>
        <div style="
            font-family: 'Fascinate Inline', cursive;
            font-size: 4.8rem;
            background: linear-gradient(135deg, #e11d48, #eab308);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1;
            filter: drop-shadow(0 2px 8px rgba(96,165,250,0.3));
        ">Yo!</div>
    </div>
    <div style="
        font-family: 'Quintessential', serif;
        font-size: 1.75rem;
        color: #374151;
        text-align: center;
        margin-bottom: 6px;
        letter-spacing: 0.5px;
        padding: 4px 20px 0 20px;
    ">Welcome to OmniMind</div>
""", unsafe_allow_html=True)

# Description only on empty chat
if len(st.session_state.history) == 0:
    st.markdown("""
        <div style="text-align: center; padding: 10px 20px 24px 20px;">
            <div style="
                max-width: 580px;
                margin: 0 auto;
                font-family: 'Cormorant', serif;
                color: #6b7280;
                font-size: 1.08rem;
                line-height: 1.8;
            ">
                OmniMind is your <strong style='color:#c084fc;'>autonomous multi-agent intelligence system</strong> &mdash; 
                powered by a crew of specialized AI agents that debate, reason, and collaborate to give you 
                the sharpest answers possible.<br><br>
                Whether you're deep-diving into complex topics with <strong style='color:#60a5fa;'>Agent Debate</strong>, 
                analysing images, generating production-ready code, converting UI mockups to HTML, 
                or searching the web &mdash; OmniMind has a dedicated agent for it.<br><br>
                <span style='color:#9ca3af; font-style:italic;'>Set your destination and let the voyage begin &#x2693;</span>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Create the main container for chat messages
chat_container = st.container()

with chat_container:
    # Chat Messages
    for idx, item in enumerate(st.session_state.history):
        _avatar = "🕵️‍♂️" if item["role"] == "user" else (str(_luffy_path) if _luffy_path.exists() else "🤖")
        with st.chat_message(item["role"], avatar=_avatar):
            if item.get("image"):
                if isinstance(item["image"], str):
                    st.image(base64.b64decode(item["image"]), width=300)
                else:
                    st.image(item["image"], width=300)
            
            if item.get("content"):
                st.markdown(item["content"], unsafe_allow_html=True)
                
            if item.get("audio"):
                if isinstance(item["audio"], str):
                    st.audio(base64.b64decode(item["audio"]), format='audio/mp3')
                else:
                    st.audio(item["audio"], format='audio/mp3')

st.markdown("<br><br><br><br><br><br>", unsafe_allow_html=True)

# --- Chat Input Area (Exactly matching DeepThink Image) ---
with st.container(border=True): # Gives the gray bordered box wrapper matching the image
    query = st.text_area("Message", placeholder="Message", label_visibility="collapsed", key=f"user_input_{st.session_state.input_key}")
    
    # Bottom Layout inside the unified box: Modes (Left) | Attach & Mic & Clear & Submit (Right)
    # The columns will align seamlessly without gaps just like the reference UI!
    c_mode, c_space, c_clip, c_mic, c_clear, c_send = st.columns([2.5, 3.9, 0.6, 0.6, 0.6, 0.5])
    
    with c_mode:
        opts = ["⚖️ Agent Debate (DeepThink)", "🌐 Search", "💻 Gen Code", "🖼️ Analyze Visually", "🎨 UI to HTML"]
        selected_mode = st.selectbox("Mode", opts, label_visibility="collapsed")
        
    with c_clip:
        with st.popover("📎"):
            uploaded_file = st.file_uploader("Attach Files", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
            
    with c_mic:
        with st.popover("🎙️"):
            audio_file = st.audio_input("Record Voice", label_visibility="collapsed")
            
    with c_clear:
        if st.button("✖️", help="Clear Input", use_container_width=True):
            st.session_state.input_key += 1
            st.rerun()
            
    with c_send:
        submit_placeholder = st.empty()
        send_btn = submit_placeholder.button("↑", type="primary", use_container_width=True)

if send_btn:
    # Immediately replace button with stop/loading icon. Clicking this during run will abort the Streamlit process.
    submit_placeholder.button("⏹️", type="secondary", use_container_width=True)
    
    if not st.session_state.api_key:
        st.error("Please enter your Google Gemini API Key in the sidebar.")
    elif not query and not uploaded_file and not audio_file:
        st.warning("Please enter a query, upload an image, or record a voice note.")
    else:
        # User Message handling
        image_data_base64 = base64.b64encode(uploaded_file.getvalue()).decode('utf-8') if uploaded_file else None
        
        user_msg = {"role": "user", "content": query, "image": image_data_base64}
        st.session_state.history.append(user_msg)
        persist_chat()
        
        # Display immediately inside the main chat container above the input
        with chat_container:
            with st.chat_message("user", avatar="🕵️‍♂️"):
                if image_data_base64:
                    st.image(base64.b64decode(image_data_base64), width=300)
                if audio_file:
                    st.audio(audio_file)
                if query:
                    st.markdown(query, unsafe_allow_html=True)
                
        engine = IntelligenceEngine(api_key=st.session_state.api_key)
        
        with chat_container:
            with st.chat_message("assistant", avatar=str(_luffy_path) if _luffy_path.exists() else "🤖"):
                # If Microphone is used, Voice Processing entirely overrides Text Option
                if audio_file is not None:
                    with st.spinner("Processing Voice..."):
                        try:
                            results = engine.run_voice_pipeline(query, audio_file.getvalue(), audio_file.type)
                            resp_text = results['Voice']['output']
                            header = f"### 🗣️ Voice AI Analyst ({results['Voice']['time']}s)\n\n"
                            st.markdown(header + resp_text)
                            
                            audio_b64 = None
                            st.session_state.history.append({"role": "assistant", "content": header + resp_text, "audio": audio_b64, "image": None})
                            persist_chat()
                        except Exception as e:
                            st.error(f"Voice Error: {e}")

                elif selected_mode == "💻 Gen Code":
                    with st.spinner("Generating beautiful, highly-optimized code..."):
                        try:
                            bot_history = []
                            for m in st.session_state.history:
                                if m["role"] == "user":
                                    bot_history.append({"query": m.get("content", "")})
                                else:
                                    if len(bot_history) > 0:
                                        bot_history[-1]["results"] = {"Code": {"output": m.get("content", "")}}
                                        
                            results = engine.run_code_generation(query, bot_history)
                            code_html = results['Code']['output']
                            
                            header = f"### 💻 Expert Code Architect ({results['Code']['time']}s)\n\n"
                            st.markdown(header + code_html)
                            
                            audio_b64 = None
                            st.session_state.history.append({"role": "assistant", "content": header + code_html, "audio": audio_b64, "image": None})
                            persist_chat()
                        except Exception as e:
                            st.error(f"Error: {e}")

                elif selected_mode == "🖼️ Analyze Visually":
                    if not uploaded_file:
                        st.warning("Please upload an image first to use the Vision Analyzer.")
                    else:
                        with st.spinner("Analyzing image details..."):
                            try:
                                results = engine.run_image_analysis(query, uploaded_file.getvalue(), uploaded_file.type)
                                vision_html = results['Vision']['output']
                                
                                header = f"### 🖼️ Gemini Vision Analyst ({results['Vision']['time']}s)\n\n"
                                st.markdown(header + vision_html)
                                
                                audio_b64 = None
                                st.session_state.history.append({"role": "assistant", "content": header + vision_html, "audio": audio_b64, "image": None})
                                persist_chat()
                            except Exception as e:
                                st.error(f"Error: {e}")
                                
                elif selected_mode == "🎨 UI to HTML":
                    if not uploaded_file:
                        st.warning("Please upload an image of the UI first.")
                    else:
                        with st.spinner("Converting UI to HTML code..."):
                            try:
                                results = engine.run_ui_to_html(query, uploaded_file.getvalue(), uploaded_file.type)
                                ui_html = results['UI_to_HTML']['output']
                                
                                header = f"### 🎨 Developer Architect ({results['UI_to_HTML']['time']}s)\n\n"
                                st.markdown(header + ui_html)
                                
                                audio_b64 = None
                                st.session_state.history.append({"role": "assistant", "content": header + ui_html, "audio": audio_b64, "image": None})
                                persist_chat()
                            except Exception as e:
                                st.error(f"Error: {e}")

                elif selected_mode == "🌐 Search":
                    with st.spinner("Searching for information..."):
                        try:
                            results = engine.run_search_and_analyze(query)
                            search_html = results['Analysis']['output']
                            
                            header = f"### 🌐 Omni Search ({results['Analysis']['time']}s)\n\n"
                            st.markdown(header + search_html)
                            
                            audio_b64 = None
                            st.session_state.history.append({"role": "assistant", "content": header + search_html, "audio": audio_b64, "image": None})
                            persist_chat()
                        except Exception as e:
                            st.error(f"Error: {e}")

                elif "Agent Debate" in selected_mode:
                    try:
                        st_placeholder = st.empty()
                        full_md = ""
                        results = None

                        for update in engine.run_pipeline(query):
                            if update["status"] == "thinking":
                                st_placeholder.markdown(full_md + f"<div class='agent-box'>\n\n*⏳ {update['message']}*\n\n</div>", unsafe_allow_html=True)
                            elif update["status"] == "done":
                                agent = update["agent"]
                                data = update["data"]
                                
                                if "output" in data:
                                    out = data['output']
                                    out = out.replace("CONFIDENCE SCORE SYSTEM:", "<br><br><span style='background-color:rgba(192, 132, 252, 0.15); color:#9d4edd; padding: 6px 10px; border-radius:8px; font-weight:bold; font-size:0.9em; box-shadow: 0 2px 5px rgba(0,0,0,0.05);'>🏆 CONFIDENCE SCORE SYSTEM:</span>")
                                    out = out.replace("EXPLAINABLE AI (XAI):", "<br><br><span style='background-color:rgba(96, 165, 250, 0.15); color:#2563eb; padding: 6px 10px; border-radius:8px; font-weight:bold; font-size:0.9em; box-shadow: 0 2px 5px rgba(0,0,0,0.05);'>🧠 EXPLAINABLE AI (XAI):</span>")
                                    data['output'] = out
                                    
                                t_span = f"<span style='font-size:0.55em; color:#9ca3af; font-weight:500; vertical-align:middle; margin-left:8px;'>({data['time']}s)</span>"
                                
                                if agent == "Analyzer":
                                    parsed = update["parsed"]
                                    full_md += f"<div class='agent-box'>\n\n### 🔍 Analyzer {t_span}\n**GOAL:** {parsed['goal']}\n\n**ANALYSIS:**\n{parsed['analysis']}\n\n</div>\n"
                                elif agent == "Pro":
                                    full_md += f"<div class='agent-box'>\n\n### ⚖️ Pro {t_span}\n{data['output']}\n\n</div>\n"
                                elif agent == "Con":
                                    full_md += f"<div class='agent-box'>\n\n### ⚖️ Con {t_span}\n{data['output']}\n\n</div>\n"
                                elif agent == "Critic":
                                    full_md += f"<div class='agent-box'>\n\n### 🧐 Critic {t_span}\n{data['output']}\n\n</div>\n"
                                elif agent == "Decision":
                                    full_md += f"<div class='agent-box'>\n\n### 👑 Decision {t_span}\n{data['output']}\n\n</div>\n"
                                
                                st_placeholder.markdown(full_md, unsafe_allow_html=True)
                            elif update["status"] == "complete":
                                results = update["results"]
                        
                        decision_html = results['Decision']['output']
                        
                        audio_b64 = None
                        st.session_state.history.append({"role": "assistant", "content": full_md, "audio": audio_b64, "image": None})
                        persist_chat()
                    except Exception as e:
                        st.error(f"Error: {e}")
            
        time.sleep(0.5)
        st.session_state.input_key += 1
        st.rerun()
