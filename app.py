import streamlit as st
import time
from dotenv import load_dotenv
from utils.audio_processor import process_input, process_uploaded_file
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

load_dotenv()

# ─── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Video Assistant",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Syne:wght@700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Root Variables (Maximalism Theme) ── */
:root {
    --bg: #5c5bee; /* Bold Cornflower Purple */
    --surface: #ffd6e8; /* Soft Pastel Pink card background */
    --surface-2: #ffffff; /* White input/inner backgrounds */
    --border: #0b0f19; /* Solid dark navy borders */
    --accent: #5c5bee; /* Bold Purple accent */
    --accent-glow: #22c55e; /* Bright Green highlight */
    --accent-2: #0b0f19;
    --text: #0b0f19; /* High-contrast dark navy text */
    --text-muted: #4b5563; /* Slate gray text */
    --success: #22c55e;
    --warning: #f59e0b;
    --danger: #ef4444;
}

/* ── Global Reset ── */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

.stApp {
    background: var(--bg) !important;
}

/* ── Streamlit Header Styling for Sidebar Toggle visibility ── */
[data-testid="stHeader"] {
    background-color: transparent !important;
    background: transparent !important;
    backdrop-filter: none !important;
    -webkit-backdrop-filter: none !important;
    border: none !important;
    box-shadow: none !important;
    display: block !important;
    z-index: 99 !important;
}

/* Hide deploy button and main menu toolbar, keeping the sidebar toggle */
[data-testid="stHeader"] [data-testid="stDeployButton"],
[data-testid="stHeader"] #MainMenu,
[data-testid="stHeader"] [data-testid="stToolbar"] button:not([data-testid="stExpandSidebarButton"]) {
    display: none !important;
}

/* Style the remaining header button (the sidebar open toggle button) */
[data-testid="stHeader"] button {
    background-color: #ffffff !important;
    border: 2px solid #0b0f19 !important;
    border-radius: 12px !important;
    color: #0b0f19 !important;
    box-shadow: 3px 3px 0px 0px #0b0f19 !important;
    transition: all 0.2s ease-in-out !important;
}

[data-testid="stHeader"] button:hover {
    background-color: #fbcfe8 !important;
    transform: translate(-1px, -1px) !important;
    box-shadow: 4px 4px 0px 0px #0b0f19 !important;
}

[data-testid="stHeader"] svg {
    fill: #0b0f19 !important;
    color: #0b0f19 !important;
}

.block-container {
    padding-top: 5rem !important;
    padding-bottom: 2.5rem !important;
}

/* ── Sidebar (Frosted Panel in Pink) ── */
[data-testid="stSidebar"] {
    background: #ffd6e8 !important;
    border-right: 2px solid #0b0f19 !important;
}

[data-testid="stSidebar"] * {
    color: #0b0f19 !important;
}

[data-testid="stSidebar"] button {
    background-color: #ffffff !important;
    border: 2px solid #0b0f19 !important;
    border-radius: 10px !important;
    color: #0b0f19 !important;
    box-shadow: 2px 2px 0px 0px #0b0f19 !important;
    transition: all 0.2s !important;
}

[data-testid="stSidebar"] button:hover {
    background-color: #fbcfe8 !important;
    transform: translate(-1px, -1px) !important;
    box-shadow: 3px 3px 0px 0px #0b0f19 !important;
}

[data-testid="stSidebar"] svg {
    fill: #0b0f19 !important;
    color: #0b0f19 !important;
}

/* ── Headings ── */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Syne', sans-serif !important;
    color: #0b0f19 !important;
    font-weight: 800 !important;
}

/* ── Hero Title ── */
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: clamp(2.2rem, 5vw, 3.5rem);
    font-weight: 800;
    line-height: 1.1;
    margin: 0;
    color: #ffffff !important;
    text-shadow: 3px 3px 0px #0b0f19;
}

.hero-sub {
    font-family: 'Plus Jakarta Sans', sans-serif;
    font-size: 0.85rem;
    font-weight: 700;
    color: #ffffff !important;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-top: 0.75rem;
    text-shadow: 1.5px 1.5px 0px #0b0f19;
}

/* ── Neobrutalist Cards ── */
.card {
    background: var(--surface);
    border: 2px solid var(--border);
    border-radius: 20px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    position: relative;
    overflow: hidden;
    box-shadow: 5px 5px 0px 0px #0b0f19;
    transition: all 0.2s ease-in-out;
}

.card:hover {
    transform: translate(-2px, -2px);
    box-shadow: 7px 7px 0px 0px #0b0f19;
}

.card-title {
    font-family: 'Syne', sans-serif;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #0b0f19;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.card-content {
    font-size: 0.95rem;
    line-height: 1.7;
    color: #0b0f19;
}

/* ── Accent Badge ── */
.badge {
    display: inline-block;
    padding: 0.25rem 0.6rem;
    border-radius: 8px;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border: 1.5px solid #0b0f19;
}

.badge-purple { background: #ffd6e8; color: #0b0f19; }
.badge-cyan   { background: #cffafe; color: #0b0f19; }
.badge-green  { background: #4ade80; color: #0b0f19; }

/* ── Input & Buttons ── */
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: #ffffff !important;
    border: 2px solid #0b0f19 !important;
    border-radius: 12px !important;
    color: #0b0f19 !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.95rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 2px 2px 0px 0px #0b0f19 !important;
}

.stTextInput > div > div > input:focus,
.stSelectbox > div > div:hover {
    border-color: var(--accent) !important;
    transform: translate(-1px, -1px);
    box-shadow: 3px 3px 0px 0px #0b0f19 !important;
}

.stButton > button,
.stFormSubmitButton > button {
    background: #5c5bee !important; /* Theme Purple background */
    color: #ffffff !important;
    border: 2px solid #0b0f19 !important;
    border-radius: 12px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 800 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.05em !important;
    padding: 0.7rem 1.6rem !important;
    transition: all 0.2s ease-in-out !important;
    text-transform: uppercase !important;
    box-shadow: 3px 3px 0px 0px #0b0f19 !important; /* Black neobrutalist shadow */
}

.stButton > button:hover,
.stFormSubmitButton > button:hover {
    background: #ffd6e8 !important; /* Warm pink hover */
    color: #0b0f19 !important;
    transform: translate(-1px, -1px) !important;
    box-shadow: 4px 4px 0px 0px #0b0f19 !important;
}

/* Secondary button */
.stButton > button[kind="secondary"] {
    background: #ffffff !important;
    border: 2px solid #0b0f19 !important;
    color: #0b0f19 !important;
    box-shadow: 2px 2px 0px 0px #0b0f19 !important;
}

.stButton > button[kind="secondary"]:hover {
    transform: translate(-1px, -1px) !important;
    box-shadow: 3px 3px 0px 0px #0b0f19 !important;
}

/* ── Progress / Status ── */
.status-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.85rem 1.25rem;
    background: #ffffff;
    border-radius: 12px;
    margin: 0.5rem 0;
    border: 2px solid #0b0f19;
    font-size: 0.85rem;
    font-weight: 700;
    color: #0b0f19;
    box-shadow: 3px 3px 0px 0px #0b0f19;
}

.status-dot {
    width: 10px; height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
    border: 1px solid #0b0f19;
}

.dot-active   { background: #eab308; box-shadow: 0 0 6px #eab308; animation: pulse 1.5s infinite; }
.dot-done     { background: #22c55e; }
.dot-pending  { background: #e5e7eb; }

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.4; }
}

/* ── Chat ── */
.chat-container {
    background: #ffd6e8;
    border: 2px solid #0b0f19;
    border-radius: 20px;
    padding: 1.5rem;
    max-height: 480px;
    overflow-y: auto;
    margin-bottom: 1.25rem;
    box-shadow: inset 2px 2px 6px rgba(0,0,0,0.1), 4px 4px 0px 0px #0b0f19;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
}

.chat-msg {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    width: 100%;
}

.chat-label {
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #0b0f19;
    margin-left: 0.2rem;
}

.chat-bubble {
    display: inline-block;
    padding: 0.8rem 1.25rem;
    border-radius: 16px;
    font-size: 0.95rem;
    line-height: 1.6;
    max-width: 80%;
    word-wrap: break-word;
    border: 2px solid #0b0f19;
}

.user-label  { color: #ffffff; text-shadow: 1px 1px 0px #0b0f19; align-self: flex-end; margin-right: 0.2rem; }
.bot-label   { color: #0b0f19; align-self: flex-start; }

.user-bubble {
    background: #5c5bee !important;
    color: #ffffff !important;
    align-self: flex-end;
    border-bottom-right-radius: 2px;
    box-shadow: 3px 3px 0px 0px #0b0f19;
}

.bot-bubble {
    background: #ffffff !important;
    color: #0b0f19 !important;
    align-self: flex-start;
    border-bottom-left-radius: 2px;
    box-shadow: 3px 3px 0px 0px #0b0f19;
}

/* ── Divider ── */
hr {
    border: none !important;
    border-top: 2px solid #0b0f19 !important;
    margin: 1.75rem 0 !important;
}

/* ── Transcript box ── */
.transcript-box {
    background: #ffffff;
    border: 2px solid #0b0f19;
    border-radius: 16px;
    padding: 1.25rem;
    font-size: 0.9rem;
    line-height: 1.8;
    max-height: 320px;
    overflow-y: auto;
    color: #0b0f19;
    white-space: pre-wrap;
    word-break: break-word;
    box-shadow: 4px 4px 0px 0px #0b0f19;
}

/* ── Stale Streamlit elements overrides ── */
.stProgress > div > div > div { background: #0b0f19 !important; }
.stSpinner > div { border-top-color: var(--accent) !important; }
[data-testid="stMarkdownContainer"] p { color: #0b0f19 !important; }
label { color: #0b0f19 !important; font-size: 0.9rem !important; font-weight: 700 !important; }

/* Custom scrollbar */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: #0b0f19; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* Card Highlight (Neobrutalist Green Card) */
.card-highlight {
    background-color: #22c55e !important;
    color: #0b0f19 !important;
    border: 2px solid #0b0f19 !important;
    box-shadow: 4px 4px 0px 0px #0b0f19 !important;
}
.card-highlight:hover {
    box-shadow: 6px 6px 0px 0px #0b0f19 !important;
}
.card-highlight-title {
    color: #0b0f19 !important;
    font-weight: 800 !important;
}
.card-highlight-content {
    font-family: 'Syne', sans-serif !important;
    font-size: 1.4rem !important;
    font-weight: 800 !important;
    color: #0b0f19 !important;
}

/* Remove default Streamlit form borders and padding */
div[data-testid="stForm"] {
    border: none !important;
    padding: 0 !important;
    background: transparent !important;
    box-shadow: none !important;
}
</style>
""", unsafe_allow_html=True)


# ─── Session State Init ──────────────────────────────────────────────────────────
for key, default in {
    "result": None,
    "chat_history": [],
    "processing": False,
    "pipeline_done": False,
    "pipeline_steps": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─── Helpers ────────────────────────────────────────────────────────────────────
def step_status(steps: dict, key: str) -> str:
    s = steps.get(key, "pending")
    if s == "active":  return "dot-active"
    if s == "done":    return "dot-done"
    return "dot-pending"

def render_step_bar(label: str, key: str, icon: str):
    css = step_status(st.session_state.pipeline_steps, key)
    st.markdown(f"""
    <div class="status-bar">
        <div class="status-dot {css}"></div>
        <span>{icon} {label}</span>
    </div>""", unsafe_allow_html=True)

# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="hero-title" style="font-size:1.6rem">🎬 AI<br>Video</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Meeting Intelligence</div>', unsafe_allow_html=True)
    st.markdown("---")

    st.markdown('<span class="badge badge-purple">Input</span>', unsafe_allow_html=True)

    input_tab = st.radio(
        "Input Mode",
        ["🔗 YouTube URL", "📁 Upload File"],
        horizontal=True,
        label_visibility="collapsed",
    )

    source = ""
    uploaded_file = None

    if input_tab == "🔗 YouTube URL":
        source = st.text_input(
            "YouTube URL",
            placeholder="https://youtube.com/watch?v=...",
            label_visibility="visible",
        )
    else:
        uploaded_file = st.file_uploader(
            "Upload video or audio file",
            type=["mp4", "mp3", "wav", "m4a", "webm", "mkv", "ogg"],
            label_visibility="visible",
        )

    run_btn = st.button("⚡  Analyse", use_container_width=True)

    if st.session_state.pipeline_done:
        st.markdown("---")
        st.markdown('<span class="badge badge-green">Pipeline Status</span>', unsafe_allow_html=True)
        for step, icon, label in [
            ("audio",      "🔊", "Audio Processing"),
            ("transcript", "📝", "Transcription"),
            ("title",      "🏷️", "Title Generation"),
            ("summary",    "📋", "Summarisation"),
            ("extract",    "🔍", "Extraction"),
            ("rag",        "🧠", "RAG Engine"),
        ]:
            render_step_bar(label, step, icon)

# ─── Main Area ──────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">AI Video Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Transcribe · Summarise · Chat with your meetings</div>', unsafe_allow_html=True)
st.markdown("---")

# ── Run Pipeline ────────────────────────────────────────────────────────────────
if run_btn:
    _no_input = (not source.strip()) and (uploaded_file is None)
    if _no_input:
        st.error("Please enter a YouTube URL or upload a video/audio file.")
    else:
        st.session_state.pipeline_done = False
        st.session_state.result = None
        st.session_state.chat_history = []
        st.session_state.pipeline_steps = {}

        progress_placeholder = st.empty()

        def update_step(key, state):
            st.session_state.pipeline_steps[key] = state

        try:
            with progress_placeholder.container():
                st.info("⚙️ Pipeline running — see sidebar for live status…")

            update_step("audio", "active")
            if uploaded_file is not None:
                result = process_uploaded_file(uploaded_file)
            else:
                result = process_input(source)
            update_step("audio", "done")

            update_step("transcript", "active")
            if isinstance(result, str):
                # YouTube transcript fetched directly — no Whisper needed
                transcript = result
            else:
                # Local file audio chunks — run Whisper
                transcript = transcribe_all(result)
            update_step("transcript", "done")

            update_step("title", "active")
            title = generate_title(transcript)
            update_step("title", "done")

            update_step("summary", "active")
            summary = summarize(transcript)
            update_step("summary", "done")

            update_step("extract", "active")
            action_items  = extract_action_items(transcript)
            decisions     = extract_key_decisions(transcript)
            questions     = extract_questions(transcript)
            update_step("extract", "done")

            update_step("rag", "active")
            rag_chain = build_rag_chain(transcript)
            update_step("rag", "done")

            st.session_state.result = {
                "title": title,
                "transcript": transcript,
                "summary": summary,
                "action_items": action_items,
                "key_decisions": decisions,
                "open_questions": questions,
                "rag_chain": rag_chain,
            }
            st.session_state.pipeline_done = True
            progress_placeholder.success("✅ Analysis complete!")
            time.sleep(0.5)
            progress_placeholder.empty()
            st.rerun()

        except Exception as e:
            for k in ["audio","transcript","title","summary","extract","rag"]:
                if st.session_state.pipeline_steps.get(k) == "active":
                    st.session_state.pipeline_steps[k] = "pending"
            progress_placeholder.error(f"❌ Error: {e}")

# ── Results ──────────────────────────────────────────────────────────────────────
if st.session_state.result:
    r = st.session_state.result

    # Title banner
    st.markdown(f"""
    <div class="card card-highlight">
        <div class="card-title card-highlight-title">📌 Session Title</div>
        <div class="card-highlight-content">
            {r['title']}
        </div>
    </div>""", unsafe_allow_html=True)

    # Top row: summary + transcript
    col1, col2 = st.columns([3, 2], gap="medium")

    with col1:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">📋 Summary</div>
            <div class="card-content">{r['summary']}</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        with st.expander("📝 Full Transcript", expanded=False):
            st.markdown(f'<div class="transcript-box">{r["transcript"]}</div>', unsafe_allow_html=True)

    # Second row: action items | decisions | questions
    c1, c2, c3 = st.columns(3, gap="medium")

    with c1:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">✅ Action Items</div>
            <div class="card-content">{r['action_items']}</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">🔑 Key Decisions</div>
            <div class="card-content">{r['key_decisions']}</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="card">
            <div class="card-title">❓ Open Questions</div>
            <div class="card-content">{r['open_questions']}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── RAG Chat ──────────────────────────────────────────────────────────────
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:1.2rem;font-weight:700;margin-bottom:1rem">💬 Chat with your Meeting</div>', unsafe_allow_html=True)

    # Chat history display
    if st.session_state.chat_history:
        chat_html = '<div class="chat-container">'
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                chat_html += f"""
                <div class="chat-msg" style="align-items:flex-end">
                    <span class="chat-label user-label">You</span>
                    <div class="chat-bubble user-bubble">{msg['content']}</div>
                </div>"""
            else:
                chat_html += f"""
                <div class="chat-msg" style="align-items:flex-start">
                    <span class="chat-label bot-label">🤖 Assistant</span>
                    <div class="chat-bubble bot-bubble">{msg['content']}</div>
                </div>"""
        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="card" style="text-align:center;padding:2rem">
            <div style="font-size:2rem;margin-bottom:0.5rem">💬</div>
            <div style="color:var(--text-muted);font-size:0.85rem">Ask anything about your meeting transcript</div>
        </div>""", unsafe_allow_html=True)

    # Chat input form to support Enter submission and auto-clearing
    with st.form(key="chat_form", clear_on_submit=True):
        chat_col1, chat_col2 = st.columns([5, 1], gap="small")
        with chat_col1:
            user_input = st.text_input("Your question", placeholder="What were the main decisions made?", label_visibility="collapsed", key="chat_input_val")
        with chat_col2:
            send_btn = st.form_submit_button("Send →", use_container_width=True)

        if send_btn and user_input.strip():
            with st.spinner("Thinking…"):
                answer = ask_question(r["rag_chain"], user_input.strip())
            st.session_state.chat_history.append({"role": "user",      "content": user_input.strip()})
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.rerun()

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat", type="secondary"):
            st.session_state.chat_history = []
            st.rerun()

else:
    # Empty state
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;padding:5rem 2rem;text-align:center">
        <div style="font-size:4rem;margin-bottom:1rem">🎬</div>
        <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:700;color:var(--text);margin-bottom:0.5rem">
            Ready to Analyse
        </div>
        <div style="color:var(--text-muted);font-size:0.85rem;max-width:380px;line-height:1.7">
            Paste a YouTube URL or local file path in the sidebar, choose your language, and hit <strong>Analyse</strong> to get started.
        </div>
        <div style="margin-top:2rem;display:flex;gap:1rem;flex-wrap:wrap;justify-content:center">
            <span class="badge badge-purple">Transcription</span>
            <span class="badge badge-cyan">Summarisation</span>
            <span class="badge badge-green">RAG Chat</span>
        </div>
    </div>""", unsafe_allow_html=True)