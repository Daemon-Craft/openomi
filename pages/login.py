import streamlit as st

# Login page styling
st.markdown("""
<style>
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 3rem 2rem;
    }
    .login-header {
        text-align: center;
        margin-bottom: 2rem;
    }
    .login-header h1 {
        color: #667eea;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    .login-header p {
        color: #666;
        font-size: 1.1rem;
    }
    .login-card {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border: 2px solid #e9ecef;
    }
    .role-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s;
        text-align: center;
    }
    .role-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.3);
    }
    .info-box {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem;
        border-radius: 4px;
        margin-top: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

st.subheader("Sign In")
st.write("Select your role to access the system")

# Role selection with info
roles = {
    "Officer": {
        "icon": "👮",
        "description": "Immigration Officer - Full access to audit tools and reports",
        "access": ["Run fraud detection audits", "View all reports", "Manage knowledge base"]
    },
    "Analyst": {
        "icon": "📊",
        "description": "Data Analyst - View and analyze reports",
        "access": ["View reports", "Download data", "Access knowledge base"]
    },
    "Admin": {
        "icon": "⚙️",
        "description": "System Administrator - Full system access",
        "access": ["Full system access", "User management", "System configuration"]
    }
}

# Role selector
selected_role = st.selectbox(
    "Choose your role:",
    options=[None] + list(roles.keys()),
    format_func=lambda x: f"{roles[x]['icon']} {x}" if x else "-- Select a role --",
    help="Different roles have different system access levels"
)

# Display role info if selected
if selected_role:
    role_info = roles[selected_role]
    st.info(f"**{role_info['icon']} {selected_role}**: {role_info['description']}")

st.markdown("---")

# Login button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    login_button = st.button(
        "🚀 Sign In",
        type="primary",
        use_container_width=True,
        disabled=not selected_role
    )

if login_button and selected_role:
    # Save authentication state
    st.session_state.authenticated = True
    st.session_state.user_role = selected_role
    st.session_state.user_icon = roles[selected_role]['icon']

    # Success message
    st.success(f"✅ Welcome, {selected_role}!")
    st.balloons()

    # Redirect to home
    import time
    time.sleep(1)
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)


st.markdown('</div>', unsafe_allow_html=True)
