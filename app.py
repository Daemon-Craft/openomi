import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Openomi - AI-Powered Financial Fraud Detection",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'user_icon' not in st.session_state:
    st.session_state.user_icon = None

# Custom CSS for professional design
st.markdown("""
<style>
    /* Headers */
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        text-align: center;
        color: #1a1a1a;
        margin-bottom: 0.5rem;
        letter-spacing: -0.5px;
        color: #667eea;
    }
    .sub-header {
        font-size: 1.1rem;
        text-align: center;
        color: #555;
        margin-top: 0;
        font-weight: 400;
    }
    .page-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a1a;
        margin-bottom: 1rem;
        border-bottom: 3px solid #667eea;
        padding-bottom: 0.5rem;
    }

    /* Top Bar */
    .top-bar {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 0 0 12px 12px;
        margin-bottom: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .top-bar-left {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .top-bar-right {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .user-badge {
        background: rgba(255, 255, 255, 0.2);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: 600;
    }

    /* Cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card h2 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-card p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
    }

    .info-card {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
    }

    .knowledge-card {
        background: white;
        border: 2px solid #e9ecef;
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        transition: all 0.3s;
    }
    .knowledge-card:hover {
        border-color: #667eea;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
    }

    /* Verdicts */
    .verdict-approved {
        background-color: #d4edda;
        color: #155724;
        padding: 1.5rem;
        border-radius: 12px;
        font-size: 1.5rem;
        font-weight: 700;
        text-align: center;
        border: 2px solid #28a745;
    }
    .verdict-rejected {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1.5rem;
        border-radius: 12px;
        font-size: 1.5rem;
        font-weight: 700;
        text-align: center;
        border: 2px solid #dc3545;
    }
    .verdict-review {
        background-color: #fff3cd;
        color: #856404;
        padding: 1.5rem;
        border-radius: 12px;
        font-size: 1.5rem;
        font-weight: 700;
        text-align: center;
        border: 2px solid #ffc107;
    }

    /* Buttons */
    .stButton>button {
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: 600;
    }

    /* Upload area */
    .uploadedFile {
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


# --- LOGOUT FUNCTION ---
def logout():
    """Logout function to reset authentication state"""
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.user_icon = None
    st.rerun()


# --- DEFINE PAGES ---

# Login page
login_page = st.Page(
    "pages/login.py",
    title="Login",
    icon="🔐"
)

# Home page - fraud detection audit
home_page = st.Page(
    "pages/home.py",
    title="Home",
    icon="🏠",
    default=True
)

# Knowledge Base page - manage reference documents
knowledge_base_page = st.Page(
    "pages/knowledge_base.py",
    title="Knowledge Base",
    icon="📚"
)

# Logout page
logout_page = st.Page(
    logout,
    title="Logout",
    icon="🚪"
)

# --- NAVIGATION LOGIC ---

# Add logo to sidebar (always visible)
st.logo("images/logo.png", icon_image="images/icon.png")

# Check authentication and build navigation
if st.session_state.authenticated:
    # --- TOP BAR FOR AUTHENTICATED USERS ---
    st.markdown(f"""
    <div class="top-bar">
        <div class="top-bar-left">
            <span style="font-size: 1.5rem; font-weight: 700;">OPENOMI</span>
            <span style="opacity: 0.9;">AI-Powered Financial Fraud Detection</span>
        </div>
        <div class="top-bar-right">
            <div class="user-badge">
                {st.session_state.user_icon} {st.session_state.user_role}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Build navigation for authenticated users
    page_dict = {
        "Main": [home_page],
        "Resources": [knowledge_base_page],
        "Account": [logout_page]
    }

    pg = st.navigation(page_dict)

else:
    # --- HEADER FOR UNAUTHENTICATED USERS ---
    st.markdown('<div class="main-header">OPENOMI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-Powered Financial Fraud Detection (Immigration case)</div>', unsafe_allow_html=True)
    st.markdown("---")

    # Show login page only
    pg = st.navigation([login_page])

# --- RUN NAVIGATION ---
pg.run()

# --- FOOTER (only for authenticated users) ---
if st.session_state.authenticated:
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; padding: 20px;'>
        <p><strong>Openomi - Built for LandingAI Financial Hackathon 2024</strong></p>
        <p>Powered by AWS Bedrock (Claude 3.5 Sonnet) + LandingAI Agentic Document Extraction (ADE)</p>
        <p><em>Transforming immigration financial audits from hours to seconds with no compromise on accuracy</em></p>
        <p style='font-size: 0.8rem; margin-top: 10px;'>This is a prototype for demonstration purposes. Not for production use.</p>
    </div>
    """, unsafe_allow_html=True)
