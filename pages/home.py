import streamlit as st
import json
import uuid
import os
import boto3
from dotenv import load_dotenv
from datetime import datetime
import time
from botocore.config import Config

# Load environment
load_dotenv()

# AWS Configuration
BUCKET_NAME = os.getenv('S3_UPLOADS_BUCKET', 'openomi-uploads-dev')
BEDROCK_AGENT_ID = os.getenv('BEDROCK_AGENT_ID')
BEDROCK_AGENT_ALIAS_ID = os.getenv('BEDROCK_AGENT_ALIAS_ID')
AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

boto_config = Config(
    read_timeout=600,
    connect_timeout=60,
    retries={'max_attempts': 3}
)

# Initialize AWS clients
s3_client = boto3.client('s3', region_name=AWS_DEFAULT_REGION, config=boto_config)
bedrock_agent_client = boto3.client('bedrock-agent-runtime', region_name=AWS_DEFAULT_REGION, config=boto_config)

# Session state
if 'processing_time' not in st.session_state:
    st.session_state.processing_time = None


def invoke_bedrock_agent(prompt: str) -> tuple:
    """Invokes the Bedrock Agent and returns (response, processing_time)"""
    start_time = time.time()

    try:
        if not BEDROCK_AGENT_ID or not BEDROCK_AGENT_ALIAS_ID:
            return ("ERROR: Agent not configured", 0)

        session_id = str(uuid.uuid4())

        response = bedrock_agent_client.invoke_agent(
            agentId=BEDROCK_AGENT_ID,
            agentAliasId=BEDROCK_AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=prompt
        )

        # Stream response
        completion = ""
        for event in response.get('completion', []):
            chunk = event.get('chunk', {})
            if 'bytes' in chunk:
                completion += chunk['bytes'].decode('utf-8')

        processing_time = time.time() - start_time

        return (completion, processing_time)

    except Exception as e:
        return (f"ERROR: {str(e)}", time.time() - start_time)


# --- PAGE CONTENT ---

# Key Metrics
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown('<div class="metric-card"><h2>95% Faster</h2><p>2-4 hours reduced to 60 seconds</p></div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="metric-card"><h2>99% Accurate</h2><p>AI-powered fraud detection</p></div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="metric-card"><h2>$50K+ Saved</h2><p>Per 1000 applications processed</p></div>', unsafe_allow_html=True)

st.markdown("---")

# Program Selection
st.subheader("Step 1: Select Immigration Program")

programs = {
    "FSW-EE": "Federal Skilled Worker (Express Entry)",
    "CEC-EE": "Canadian Experience Class (Express Entry)",
    "FST-EE": "Federal Skilled Trades (Express Entry)",
    "PNP-ON": "Provincial Nominee Program - Ontario",
    "PNP-BC": "Provincial Nominee Program - British Columbia",
    "PNP-AB": "Provincial Nominee Program - Alberta",
    "QSW-ARRIMA": "Quebec Skilled Worker (Arrima)",
    "FAMILY-SPONSOR": "Family Sponsorship",
    "SUV": "Start-Up Visa",
    "SELF-EMPLOYED": "Self-Employed Persons"
}

col1, col2 = st.columns([2, 1])

with col1:
    selected_program = st.selectbox(
        "Choose the immigration program you're applying for:",
        options=list(programs.keys()),
        format_func=lambda x: programs[x],
        help="Different programs have different financial requirements"
    )

with col2:
    family_size = st.number_input(
        "Family size:",
        min_value=1,
        max_value=10,
        value=1,
        help="Total number of people in your family (including yourself)"
    )

st.markdown("---")

# File Upload
st.subheader("Step 2: Upload Bank Statements (6 Months)")
st.markdown("Upload PDF or image files of bank statements for audit")

uploaded_files = st.file_uploader(
    "Choose files",
    accept_multiple_files=True,
    type=["pdf", "jpg", "png", "jpeg"],
    help="Upload 6 months of consecutive bank statements"
)

if uploaded_files:
    st.success(f"{len(uploaded_files)} file(s) ready for analysis")

    # Show file list
    for idx, file in enumerate(uploaded_files, 1):
        st.write(f"{idx}. {file.name} ({file.size / 1024:.1f} KB)")

st.markdown("---")

# Analyze Button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    analyze_button = st.button(
        "RUN FRAUD DETECTION AUDIT",
        type="primary",
        use_container_width=True,
        disabled=not uploaded_files
    )

# Processing
if analyze_button and uploaded_files:

    # Phase 1: Upload
    st.markdown("---")
    st.subheader("Phase 1: Secure Upload")

    progress_bar = st.progress(0)
    uploaded_keys = []

    try:
        for idx, file in enumerate(uploaded_files):
            file_key = f"audit-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}-{file.name}"
            file.seek(0)
            s3_client.upload_fileobj(file, BUCKET_NAME, file_key)
            uploaded_keys.append(file_key)
            progress_bar.progress((idx + 1) / len(uploaded_files))

        st.success(f"Uploaded {len(uploaded_keys)} documents")

    except Exception as e:
        st.error(f"Upload error: {e}")
        st.stop()

    # Phase 2: AI Analysis
    st.markdown("---")
    st.subheader("Phase 2: AI Fraud Detection & Compliance Analysis")

    with st.spinner(f"Analyzing for {programs[selected_program]}..."):
        prompt = f"""Perform a complete IRCC financial compliance audit for the **{programs[selected_program]}** program.
        **Program Code:** {selected_program}
        **Family Size:** {family_size}
        **Documents:** {json.dumps(uploaded_keys)}
        CRITICAL: Apply the specific financial requirements and red flags for {selected_program} program, NOT generic rules.
        Extract data from each file, verify compliance with {selected_program} requirements, detect fraud, and generate your audit report."""

        agent_response, processing_time = invoke_bedrock_agent(prompt)
        st.session_state.processing_time = processing_time

    st.success(f"Analysis complete in {processing_time:.1f} seconds")

    # Phase 3: Results
    st.markdown("---")
    st.subheader("Phase 3: Audit Report")

    # Parse verdict from response
    verdict = "NEEDS REVIEW"
    if "APPROVED" in agent_response.upper():
        verdict = "APPROVED"
    elif "REJECTED" in agent_response.upper():
        verdict = "REJECTED"

    # Show verdict banner
    if verdict == "APPROVED":
        st.markdown(f'<div class="verdict-approved">VERDICT: APPROVED</div>', unsafe_allow_html=True)
    elif verdict == "REJECTED":
        st.markdown(f'<div class="verdict-rejected">VERDICT: REJECTED</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="verdict-review">VERDICT: NEEDS REVIEW</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Documents", len(uploaded_keys))
    with col2:
        st.metric("Processing Time", f"{processing_time:.1f}s")
    with col3:
        red_flags = agent_response.upper().count("RED FLAG") + agent_response.upper().count("❌")
        st.metric("Red Flags", red_flags)
    with col4:
        time_saved_hours = (2.5 * 3600 - processing_time) / 3600
        st.metric("Time Saved", f"{time_saved_hours:.1f}h")

    st.markdown("---")

    # Full Report
    st.markdown("### Complete Audit Report")
    st.markdown(agent_response)

    st.markdown("---")

    # Export
    st.subheader("Export Report")

    report_data = {
        'timestamp': datetime.now().isoformat(),
        'verdict': verdict,
        'files_analyzed': len(uploaded_keys),
        'processing_time_seconds': processing_time,
        'red_flags_detected': red_flags,
        'report': agent_response
    }

    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "Download Report (JSON)",
            data=json.dumps(report_data, indent=2),
            file_name=f"openomi_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

    with col2:
        st.download_button(
            "Download Report (TXT)",
            data=agent_response,
            file_name=f"openomi_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
