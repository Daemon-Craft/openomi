from unittest import result
import streamlit as st
import time
from dotenv import load_dotenv
from lambda_test_extraction import run_extraction_on_file


# --- Page Configuration (Must be the first st command) ---
st.set_page_config(
    page_title="Openomi Proof of Funds Auditor",
    page_icon="🤖",
    layout="centered",
)

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
        # Check if files were actually uploaded
    

        st.info(f"Processing {len(uploaded_files)} document(s)... This may take a moment.")
        
        # 2. Show a spinner during processing to improve user experience
        with st.spinner("Running extraction (LandingAI) and reasoning (Bedrock)..."):
            try:
                # This simulates the network and processing time of Lambda,
                # LandingAI, and Bedrock.
                time.sleep(5) 

                st.divider()
                st.subheader("Analysis Results Local test:")

                for i, uploaded_file in enumerate(uploaded_files):
                    st.markdown(f"### Document {i+1}: {uploaded_file.name}")
                    # Call the extraction function for each uploaded file
                    files_bytes = uploaded_file.read()  
                    extraction_result = run_extraction_on_file(files_bytes)

                    if "error" in extraction_result:
                        st.error(f"Error processing {uploaded_file.name}: {extraction_result['error']}")
                    else:
                        st.success(f"Successfully processed {uploaded_file.name}")
                        st.markdown("**Extracted Content:**")
                        st.markdown(extraction_result)

            except Exception as e:
                # Catch any potential errors during the API call
                st.error(f"An error occurred during analysis: {e}")

    else:
        # If the user clicks the button without uploading files
        st.warning("Please upload at least one document before analyzing.")

# --- Footer ---
st.markdown("---")
st.caption("© 2025 Openomi (Hackathon MVP). This is a proof-of-concept and does not constitute legal or financial advice.")


