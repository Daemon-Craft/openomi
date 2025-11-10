import json
import os
import tempfile
import boto3
from pathlib import Path
import traceback

try:
    from landingai_ade import LandingAIADE
    from landingai_ade.lib import pydantic_to_json_schema
    from pydantic import BaseModel, Field
except ImportError:
    print("Failed to import landingai-ade or pydantic. Ensure Layer is attached.")

# --- Initialize clients (outside handler for reuse) ---
s3_client = boto3.client('s3')
ade_client = LandingAIADE()

BUCKET_NAME = os.environ.get('S3_UPLOADS_BUCKET', 'openomi-uploads-dev')

# --- Pydantic Schema (Defines what LandingAI should extract) ---
class Transaction(BaseModel):
    date: str = Field(description="The date of the transaction")
    description: str = Field(description="The description of the transaction")
    amount: float = Field(description="The value of the transaction (use negative for withdrawals)")

class BankStatementSchema(BaseModel):
    account_holder: str = Field(description="Full name of the account holder")
    open_balance: float = Field(description="The opening balance at the start of the period")
    ending_balance: float = Field(description="The final balance at the end of the period")
    currency: str = Field(description="The currency of the balances (e.g., CAD, USD)")
    transactions: list[Transaction] = Field(description="A list of all transactions found in the statement")

SCHEMA_JSON = pydantic_to_json_schema(BankStatementSchema)

def run_extraction_from_s3(file_key: str) -> dict:
    """
    Runs the Parse/Extract flow on a file stored in S3.
    Downloads the file, parses it to markdown, then extracts structured JSON.
    """
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            local_file_path = os.path.join(tmp_dir, Path(file_key).name)
            
            print(f"Downloading s3://{BUCKET_NAME}/{file_key} to {local_file_path}")
            s3_client.download_file(BUCKET_NAME, file_key, local_file_path)

            print(f"Parsing document: {local_file_path}")
            parse_response = ade_client.parse(
                document_url=str(local_file_path),
                model="dpt-2-latest"
            )

            if not parse_response.markdown:
                return {"error": "Parse failed. No markdown returned."}

            print("Parse successful. Extracting JSON...")
            json_data = ade_client.extract(
                schema=SCHEMA_JSON,
                markdown=parse_response.markdown,
                model="extract-latest"
            )

            if not json_data.extraction:
                return {'error': 'Extract failed. No JSON data found.'}

            print("Extraction successful.")
            return json_data.extraction
            
    except Exception as e:
        print(f"ERROR in run extraction from_s3: {e}")
        return {'error': str(e)}

def lambda_handler(event, context):
    """
    Main handler for Bedrock Agent.
    Supports both requestBody format (new) and parameters format (old).
    """
    action_group = event.get('actionGroup', '')
    api_path = event.get('apiPath', '')
    
    print(f"Received event for action group: {action_group}, apiPath: {api_path}")

    response_body = {}
    
    if api_path == '/extract_document':
        file_key = None
        # Support both requestBody and parameters formats
        try:
            # Agent sends parameters via requestBody (preferred)
            request_body = event.get('requestBody', {})
            if request_body:
                content = request_body.get('content', {})
                properties = content.get('application/json', [])
                file_key_param = next((p for p in properties if p.get('name') == 'file_key'), None)
                if file_key_param:
                    file_key = file_key_param.get('value')
                    print(f"Found file_key in requestBody: {file_key}")
            
            # Method 2: Check parameters[] (fallback for direct invocation)
            if not file_key:
                parameters = event.get('parameters', [])
                file_key_param = next((p for p in parameters if p.get('name') == 'file_key'), None)
                if file_key_param:
                    file_key = file_key_param.get('value')
                    print(f"Found file_key in parameters: {file_key}")
            
            if file_key:
                print(f"Starting extraction for file_key: {file_key}")
                extraction_result = run_extraction_from_s3(file_key)
                response_body = extraction_result
            else:
                response_body = {
                    "error": "Missing 'file_key' parameter in both requestBody and parameters."
                }
                
        except Exception as e:
            print(f"Error during extraction: {e}")
            response_body = {"error": str(e)}
            traceback.print_exc()
            response_body = {"error": str(e)}
    else:
        response_body = {"error": f"Unknown apiPath: {api_path}"}

    # Response format expected by Bedrock Agent
    api_response = {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': action_group,
            'apiPath': api_path,
            'httpMethod': event.get('httpMethod', ''),
            'httpStatusCode': 200,
            'responseBody': {
                'application/json': {
                    'body': json.dumps(response_body)
                }
            }
        }
    }
    
    print(f"Returning response to Agent: {json.dumps(api_response)}")
    return api_response