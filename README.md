# openomi

Create a "Audit Agent" for government agencies (such as IRCC) to automate compliance audits, detect fraud, and validate the integrity of immigration applicants' financial records, reducing processing times from several hours to a few seconds.

## Architecture (Phase 2)

**Streamlit → S3 → Bedrock Agent → Lambda (LandingAI) → RAG Knowledge Base**

### Flow:
1. **Streamlit UI** - User uploads bank statements (PDF/images)
2. **S3 Upload** - Documents stored securely in S3 bucket
3. **Bedrock Agent** - Receives file keys and orchestrates analysis
4. **Lambda Tool** - Downloads from S3, extracts data via LandingAI
5. **RAG Knowledge Base** - Agent uses IRCC rules to detect red flags
6. **Report** - Final compliance audit returned to user

## Setup

### 1. Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# AWS Configuration
S3_UPLOADS_BUCKET=openomi-uploads-dev
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1

# Bedrock Agent Configuration
BEDROCK_AGENT_ID=your_agent_id_here
BEDROCK_AGENT_ALIAS_ID=your_agent_alias_id_here

# LandingAI Configuration (for Lambda)
LANDINGAI_API_KEY=your_landingai_api_key_here
```

### 2. Deploy Lambda Function

```bash
sam build --use-container
sam deploy --guided
```

This will deploy:
- Lambda Layer with dependencies (landingai-ade, pydantic, boto3)
- Lambda Function (`openomi_logic.py`)
- S3 read permissions
- Bedrock Agent invocation permissions

### 3. Configure Bedrock Agent

1. Create a Bedrock Agent in AWS Console
2. Add Action Group with `openapi_schema.json`
3. Link the deployed Lambda ARN as the Tool
4. Set up RAG Knowledge Base with IRCC compliance rules
5. Note the Agent ID and Alias ID for `.env`

### 4. Run Streamlit

```bash
streamlit run app.py
```

## Files

- **app.py** - Streamlit interface (production with Bedrock)
- **openomi_logic.py** - Lambda handler for Bedrock Agent
- **lambda_test_extraction.py** - Local testing functions
- **template.yaml** - SAM deployment configuration
- **openapi_schema.json** - API schema for Bedrock Agent
- **requirements.txt** - Python dependencies for Lambda Layer

## Testing

Local test mode is available in `lambda_test_extraction.py` for development without AWS resources.
