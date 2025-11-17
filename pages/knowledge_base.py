import streamlit as st
import os
import boto3
from dotenv import load_dotenv
from botocore.config import Config

# Load environment
load_dotenv()

# AWS Configuration
KNOWLEDGE_BUCKET = os.getenv('S3_KNOWLEDGE_BUCKET', 'openomi-rag-kb')
AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

boto_config = Config(
    read_timeout=600,
    connect_timeout=60,
    retries={'max_attempts': 3}
)

# Initialize AWS client
s3_client = boto3.client('s3', region_name=AWS_DEFAULT_REGION, config=boto_config)


def list_knowledge_base_files(prefix=""):
    """List all files in the knowledge base bucket"""
    try:
        response = s3_client.list_objects_v2(Bucket=KNOWLEDGE_BUCKET, Prefix=prefix)
        if 'Contents' in response:
            # Return full object info including metadata
            files = [obj for obj in response['Contents'] if not obj['Key'].endswith('/')]
            return files
        return []
    except Exception as e:
        st.error(f"Error listing files from bucket '{KNOWLEDGE_BUCKET}': {e}")
        return []


def delete_knowledge_file(file_key: str):
    """Delete a file from the knowledge base"""
    try:
        s3_client.delete_object(Bucket=KNOWLEDGE_BUCKET, Key=file_key)
        return True
    except Exception as e:
        st.error(f"Error deleting file: {e}")
        return False


# --- PAGE CONTENT ---

st.markdown('<div class="page-title">📚 Knowledge Base Management</div>', unsafe_allow_html=True)

st.markdown("""
<div class="info-card">
    <h4>📖 What is the Knowledge Base?</h4>
    <p>The Knowledge Base contains reference documents that the AI agent uses for grounding its analysis.
    These documents help ensure accurate, compliant, and context-aware fraud detection decisions.</p>
    <br>
    <p><strong>Examples of knowledge base documents:</strong></p>
    <ul>
        <li>IRCC official financial requirements and regulations</li>
        <li>Program-specific compliance guidelines</li>
        <li>Common fraud patterns and red flags documentation</li>
        <li>Case studies and precedents</li>
        <li>Policy updates and amendments</li>
    </ul>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Upload new documents
st.subheader("📤 Upload New Documents to Knowledge Base")

col1, col2 = st.columns([2, 1])

with col1:
    uploaded_kb_files = st.file_uploader(
        "Select documents to add to Knowledge Base",
        accept_multiple_files=True,
        type=["pdf", "txt", "md", "docx", "jpg", "png"],
        help="Upload reference documents, regulations, guidelines, etc.",
        key="kb_uploader"
    )

with col2:
    st.info(f"""
    **Accepted formats:**
    - PDF documents
    - Text files (.txt)
    - Markdown (.md)
    - Word docs (.docx)
    - Images (JPG, PNG)
    """)

if uploaded_kb_files:
    if st.button("📥 Upload to Knowledge Base", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        success_count = 0

        for idx, file in enumerate(uploaded_kb_files):
            try:
                # Upload directly to root of knowledge base bucket (no prefix)
                file_key = file.name
                file.seek(0)
                s3_client.upload_fileobj(file, KNOWLEDGE_BUCKET, file_key)
                success_count += 1
                progress_bar.progress((idx + 1) / len(uploaded_kb_files))
            except Exception as e:
                st.error(f"Failed to upload {file.name}: {e}")

        if success_count > 0:
            st.success(f"Successfully uploaded {success_count} document(s) to Knowledge Base!")
            st.rerun()

st.markdown("---")

# List existing documents
st.subheader("📂 Current Knowledge Base Documents")

kb_files = list_knowledge_base_files()

if kb_files:
    st.info(f"**{len(kb_files)} document(s)** in Knowledge Base (Bucket: `{KNOWLEDGE_BUCKET}`)")

    # Display files with metadata from S3
    for idx, file_obj in enumerate(kb_files, 1):
        file_key = file_obj['Key']
        file_name = file_key.split('/')[-1]  # Get filename from key
        file_size = f"{file_obj['Size'] / 1024:.1f} KB"
        last_modified = file_obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')

        col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

        with col1:
            st.write(f"**{idx}. {file_name}**")
        with col2:
            st.write(f"Size: {file_size}")
        with col3:
            st.write(f"Modified: {last_modified}")
        with col4:
            if st.button("🗑️", key=f"delete_{idx}", help="Delete this document"):
                if delete_knowledge_file(file_key):
                    st.success(f"Deleted {file_name}")
                    st.rerun()
else:
    st.warning(f"⚠️ No documents in Knowledge Base yet. Upload your first document above!\n\nBucket: `{KNOWLEDGE_BUCKET}`")

st.markdown("---")

# Knowledge Base Statistics
st.subheader("📊 Knowledge Base Statistics")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Documents", len(kb_files))

with col2:
    # Count PDF files
    pdf_count = sum(1 for f in kb_files if f['Key'].lower().endswith('.pdf'))
    st.metric("PDF Documents", pdf_count)

with col3:
    # Count other formats
    other_count = len(kb_files) - pdf_count
    st.metric("Other Formats", other_count)

st.markdown("---")

# Best Practices
with st.expander("💡 Best Practices for Knowledge Base", expanded=False):
    st.markdown("""
    ### Tips for Effective Knowledge Base Management

    **Document Organization:**
    - Use clear, descriptive file names (e.g., `IRCC_FSW_Requirements_2024.pdf`)
    - Keep documents up-to-date with latest regulations
    - Remove outdated or superseded documents

    **Content Quality:**
    - Upload official, authoritative sources
    - Include version numbers or dates in file names
    - Ensure documents are readable and well-formatted

    **Recommended Documents:**
    1. IRCC official program requirements
    2. Financial threshold tables
    3. Fraud detection guidelines
    4. Common red flags documentation
    5. Program-specific compliance rules

    **Maintenance:**
    - Review and update quarterly
    - Remove duplicates
    - Archive old versions
    """)
