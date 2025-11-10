import json
import os
import tempfile
import boto3
from pathlib import Path

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
    Supports both requestBody and parameters formats with extensive logging.
    """
    # ===== LOG EVERYTHING FOR DEBUGGING =====
    print(f"===== FULL EVENT RECEIVED =====")
    print(json.dumps(event, indent=2, default=str))
    print(f"===== END OF EVENT =====")
    
    action_group = event.get('actionGroup', '')
    api_path = event.get('apiPath', '')
    
    print(f"Action Group: {action_group}, API Path: {api_path}")

    response_body = {}
    
    if api_path == '/extract_document':
        file_key = None
        
        try:
            # ===== requestBody (Bedrock Agent with OpenAPI) =====
            request_body = event.get('requestBody')
            print(f"requestBody type: {type(request_body)}")
            print(f"requestBody content: {request_body}")
            
            if request_body:
                content = request_body.get('content', {})
                print(f"content type: {type(content)}")
                print(f"content: {content}")
                
                app_json = content.get('application/json', {})
                print(f"application/json type: {type(app_json)}")
                print(f"application/json: {app_json}")
                
                # Iterate safely
                if isinstance(app_json, dict):
                    properties = app_json.get('properties', [])
                    print(f"properties type: {type(properties)}")
                    print(f"properties: {properties}")
                    
                    if isinstance(properties, list):
                        for item in properties:
                            print(f"item: {item}")
                            if isinstance(item, dict) and item.get('name') == 'file_key':
                                file_key = item.get('value')
                                print(f"Found file_key in requestBody: {file_key}")
                                break
                # FIX: Also handle if it's directly a list (backward compatibility)
                elif isinstance(app_json, list):
                    for item in app_json:
                        if isinstance(item, dict) and item.get('name') == 'file_key':
                            file_key = item.get('value')
                            print(f"Found file_key in requestBody (list): {file_key}")
                            break
            
            # ===== parameters[] (fallback) =====
            if file_key is not None:
                parameters = event.get('parameters', [])
                print(f"parameters: {parameters}")
                
                if isinstance(parameters, list):
                    for param in parameters:
                        if isinstance(param, dict):
                            if param.get('name') == 'file_key':
                                file_key = param.get('value')
                                print(f"Found file_key in parameters: {file_key}")
                                break
            
            # ===== EXECUTE EXTRACTION =====
            if file_key:
                print(f"Starting extraction for: {file_key}")
                extraction_result = run_extraction_from_s3(file_key)
                response_body = extraction_result
            else:
                print(f"file_key not found in event")
                response_body = {
                    "error": "Missing 'file_key' parameter. Check Lambda logs for event structure."
                }
                
        except Exception as e:
            print(f"EXCEPTION in lambda_handler: {e}")
            import traceback
            traceback.print_exc()
            response_body = {
                "error": f"Exception: {str(e)}",
                "type": type(e).__name__
            }
    else:
        response_body = {"error": f"Unknown apiPath: {api_path}"}

    # Build response
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
    
    print(f"===== RESPONSE TO AGENT =====")
    print(json.dumps(api_response, indent=2))
    print(f"===== END OF RESPONSE =====")
    
    return api_response