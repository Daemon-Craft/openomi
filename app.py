import streamlit as st
import json
import uuid
import os
import boto3
from dotenv import load_dotenv

# --- Page Configuration (Must be the FIRST st command) ---
st.set_page_config(
    page_title="Openomi Proof of Funds Auditor",
    page_icon="🤖",
    layout="centered",
)

# Load environment variables
load_dotenv()

# --- AWS Configuration ---
BUCKET_NAME = os.getenv('S3_UPLOADS_BUCKET', 'openomi-uploads-dev')
BEDROCK_AGENT_ID = os.getenv('BEDROCK_AGENT_ID')
BEDROCK_AGENT_ALIAS_ID = os.getenv('BEDROCK_AGENT_ALIAS_ID')
AWS_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

# Initialize AWS clients
s3_client = boto3.client('s3', region_name=AWS_REGION)
bedrock_agent_client = boto3.client('bedrock-agent-runtime', region_name=AWS_REGION)


def invoke_bedrock_agent(prompt: str) -> str:
    """
    Invokes the Bedrock Agent with a given prompt.
    Returns the agent's response as a string.
    """
    try:
        if not BEDROCK_AGENT_ID or not BEDROCK_AGENT_ALIAS_ID:
            return "ERROR: Missing BEDROCK_AGENT_ID or BEDROCK_AGENT_ALIAS_ID in environment variables."
        
        session_id = str(uuid.uuid4())
        
        print(f"Invoking Bedrock Agent (Session: {session_id})...")
        
        response = bedrock_agent_client.invoke_agent(
            agentId=BEDROCK_AGENT_ID,
            agentAliasId=BEDROCK_AGENT_ALIAS_ID,
            sessionId=session_id,
            inputText=prompt
        )
        
        # Stream the response
        completion = ""
        for event in response.get('completion', []):
            chunk = event.get('chunk', {})
            if 'bytes' in chunk:
                completion += chunk['bytes'].decode('utf-8')
        
        return completion
        
    except Exception as e:
        return f"ERROR invoking Bedrock Agent: {str(e)}"


# --- Header ---
st.title("Openomi - Proof of Funds Auditor")
st.markdown("""
    Welcome to the Openomi MVP. 
    This tool simulates a pre-validation audit for immigration proof of funds documentation.
    Upload your bank statements (PDF, JPG, PNG) to check for "Red Flags" before submission.
""")


# --- File Uploader ---
# This widget allows users to upload multiple files of specified types
uploaded_files = st.file_uploader(
    "Upload your financial documents (6 months of bank statements, investment letters, etc.)",
    accept_multiple_files=True,
    type=["pdf", "jpg", "png", "jpeg"]
)

# This button will start the analysis process
if st.button("Analyze my files for Red Flags 🚩"):
    if uploaded_files:
        uploaded_keys = []  # S3 keys of uploaded files
        
        # --- PHASE 1: Upload to S3 ---
        st.divider()
        st.subheader("Phase 1: Uploading to S3...")
        with st.spinner("Securely uploading documents..."):
            try:
                for uploaded_file in uploaded_files:
                    # Create a unique filename
                    file_key = f"doc-{uuid.uuid4()}-{uploaded_file.name}"
                    
                    # Reset file pointer to beginning
                    uploaded_file.seek(0)
                    
                    s3_client.upload_fileobj(
                        uploaded_file,
                        BUCKET_NAME,
                        file_key
                    )
                    uploaded_keys.append(file_key)
                    st.write(f"✓ Uploaded `{uploaded_file.name}` as `{file_key}`")
                
                st.success(f"Successfully uploaded {len(uploaded_keys)} document(s).")
                
            except Exception as e:
                st.error(f"Error uploading to S3: {e}")
                st.stop()
        
        # --- PHASE 2: Bedrock Agent Reasoning ---
        if uploaded_keys:
            st.divider()
            st.subheader("Phase 2: Audit Report (Bedrock Agent)")
            
            with st.spinner("Contacting Bedrock Agent... The Agent is now running extraction (Lambda) and reasoning (RAG)..."):
                try:
                    # Create the prompt for the Agent
                    prompt = f"Please analyze the compliance of the following document dossier: {json.dumps(uploaded_keys)}. Check for all IRCC red flags."
                    
                    final_report = invoke_bedrock_agent(prompt)
                    
                    st.markdown("### 📋 Audit Report:")
                    st.markdown(final_report)
                
                except Exception as e:
                    st.error(f"An error occurred during Bedrock reasoning: {e}")

    else:
        # If the user clicks the button without uploading files
        st.warning("Please upload at least one document before analyzing.")

# --- Footer ---
st.markdown("---")
st.caption("© 2025 Openomi (Hackathon MVP). This is a proof-of-concept and does not constitute legal or financial advice.")


