import streamlit as st
import requests
import time


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


# --- F-01: File Uploader ---
# This widget allows users to upload multiple files of specified types
uploaded_files = st.file_uploader(
    "Upload your financial documents (6 months of bank statements, investment letters, etc.)",
    accept_multiple_files=True,
    type=["pdf", "jpg", "png", "jpeg"]
)

# --- F-02: Analysis Trigger ---
# This button will start the analysis process
if st.button("Analyze my files for Red Flags 🚩"):
    if uploaded_files:
        # Check if files were actually uploaded
        
        # 1. Set the API Gateway endpoint URL (we will fill this in later in Epic 3)
        # API_ENDPOINT_URL = "YOUR_API_GATEWAY_URL_HERE" 

        st.info(f"Processing {len(uploaded_files)} document(s)... This may take a moment.")
        
        # 2. Show a spinner during processing to improve user experience
        with st.spinner("Running extraction (LandingAI) and reasoning (Bedrock)..."):
            try:
                # --- MOCKUP FOR F-06 (To be replaced in Epic 4) ---
                
                # This simulates the network and processing time of Lambda,
                # LandingAI, and Bedrock.
                time.sleep(5) 
                
                # This is a mock Markdown report. 
                # Our Bedrock Agent will generate this for real in Epic 3.
                mock_report = """
                ## 📊 Openomi Audit Report
                
                **Decision Level: <font color='orange'>Medium Risk</font>**
                
                ---
                
                ### Summary
                * **Total Calculated Funds:** $15,100.00 CAD
                * **Required Threshold:** $14,690.00 CAD
                * **Status:** <font color='green'>Threshold Met</font>
                
                ---
                
                ### 🚩 Red Flags Identified
                
                1.  **Suspicious Deposit:**
                    * **Finding:** A large cash deposit of **$8,000.00** was detected on 2025-10-15 in `statement_month_5.pdf`.
                    * **Rule (IRCC KB):** "Large, unexplainable deposits or gifts received shortly before application may cast doubt on the applicant's financial integrity."
                    * **Recommendation:** Provide a notarized gift deed or a letter of explanation for the source of this deposit.
                
                2.  **Missing Document:**
                    * **Finding:** Analysis detected a gap. Bank statements for **August 2025** appear to be missing.
                    * **Recommendation:** Ensure all 6 consecutive months of statements are provided.
                """
                
                # --- F-06: Display the Final Report ---
                st.divider()
                st.subheader("Your Audit Report is Ready:")
                # We use unsafe_allow_html=True to render the color tags
                st.markdown(mock_report, unsafe_allow_html=True)

            except Exception as e:
                # Catch any potential errors during the API call
                st.error(f"An error occurred during analysis: {e}")

    else:
        # If the user clicks the button without uploading files
        st.warning("Please upload at least one document before analyzing.")

# --- Footer / Disclaimer ---
st.markdown("---")
st.caption("© 2025 Openomi (Hackathon MVP). This is a proof-of-concept and does not constitute legal or financial advice.")


