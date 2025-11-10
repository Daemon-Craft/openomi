import json
import os
import tempfile
import uuid
import boto3
from dotenv import load_dotenv
from pathlib import Path

try:
    from landingai_ade import LandingAIADE
    from landingai_ade.lib import pydantic_to_json_schema
    from pydantic import BaseModel, Field
except ImportError:
    print("Failed to import landingai_ade or pydantic.")
    print("Did you attach the Lambda Layer containing these libraries?")

load_dotenv()


s3_client = boto3.client('s3')
bedrock_agent_client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

class AccountTest(BaseModel):
    account_number: str = Field(description="Account number")
    account_holder: str = Field(description="Account holder")
    balance: float = Field(description="Opening balance")
    all_transactions: list = Field(description="All Transactions")

class Transaction(BaseModel):
    date: str = Field(description="The date of the transaction")
    description: str = Field(description="The description of the transaction")
    amount: float = Field(description="The value of the transaction (use negative for withdrawals)")

class BankStatementSchema(BaseModel):
    account_holder: str = Field(description="Full name of the account holder")
    open_balance: float = Field(description="The opening balance at the start of the period")
    ending_balance: float = Field(description="The final balance at the end of the period")
    currency: str = Field(description="The currency of the balances (e.g., CAD, USD)")
    
    # Tell to the AI to find a LIST of Transactions
    transactions: list[Transaction] = Field(description="A list of all transactions found in the statement")

SCHEMA_JSON = pydantic_to_json_schema(BankStatementSchema)

def lambda_handler(event, context):
    """
    Lambda handler that downloads PDF files from S3 and processes them with LandingAI.
    Performs both parsing (markdown extraction) and structured data extraction.
    """
    # Get configuration from environment variables
    try:
        BUCKET_NAME = os.environ['S3_UPLOADS_BUCKET']
    except KeyError as e:
        print(f"Environment variable {e} not set.")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Missing environment variable: {e}'})
        }

    TEST_FILE_PATH = "statement-1.pdf"
    print(f"Starting processing for file: s3://{BUCKET_NAME}/{TEST_FILE_PATH}")

    temp_file_path = None
    try:
        # Download file from S3 to temporary file
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = os.path.join(temp_dir, "statement-1.pdf")
            print(f"Downloading file from S3: s3://{BUCKET_NAME}/{TEST_FILE_PATH}")
            s3_client.download_file(BUCKET_NAME, TEST_FILE_PATH, temp_file_path)

        print(f"Successfully downloaded file to temporary path: {temp_file_path}")

        # Initialize LandingAI ADE client
        ade = LandingAIADE()

        # Step 1: Parse the document to get markdown
        print("Step 1: Parsing document with LandingAI...")
        response = ade.parse(
            document_url=temp_file_path,
            model="dpt-2-latest"
        )

        if not response.markdown:
            print("No markdown content returned from LandingAI.")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'LandingAI returned no markdown content'})
            }

        print("Parsing completed successfully! Markdown generated.")

        # Step 2: Extract structured JSON data from markdown
        print("Step 2: Extracting structured JSON data...")
        json_data = ade.extract(
            schema=SCHEMA_JSON,
            markdown=response.markdown,
            model="extract-latest"
        )

        if not json_data.extraction:
            print("No JSON data extracted.")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'No JSON data could be extracted'})
            }

        print("JSON data extracted successfully!")
        print(json_data.extraction)

        # Return the extracted data
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'File processed successfully',
                'file': TEST_FILE_PATH,
                'extraction': json_data.extraction
            }, indent=2)
        }

    except Exception as e:
        print(f"Error processing file: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Failed to process file: {str(e)}'})
        }
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                print(f"Temporary file cleaned up: {temp_file_path}")
            except Exception as cleanup_error:
                print(f"Warning: Could not clean up temporary file: {cleanup_error}")




def run_extraction_on_file(file_bytes: bytes):
    temp_file_path = None
    try:
        # Create temporary file and write data
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(file_bytes)
            temp_file.flush() # Ensure all data is written to disk
            temp_file_path = temp_file.name
        
        print(f"Temporary file created at: {temp_file_path}")
        
        # Process the file with LandingAI (after closing the file handle)
        print("Processing file with LandingAI...")
        #initialize landingai ade client
        ade = LandingAIADE()
        #parse the document
        response = ade.parse(
            document_url=temp_file_path,
            model="dpt-2-latest"
        )

        if not response.markdown:
            print("No markdown content returned from LandingAI.")
            return {'error': 'LandingAI returned no content'}

        # Process the markdown content
        print("Parsing completed successfully! Markdown generated.")
        
        # Now extract the json
        print('Extracting JSON data...')
        json_data = ade.extract(
                schema=SCHEMA_JSON,
                markdown=response.markdown,
                model="extract-latest"
            )

        if not json_data.extraction:
            print("No JSON data found.")
            return {'error': 'No JSON data found'}

        print("JSON data extracted successfully!")
        print(json_data.extraction)
        return json.dumps(json_data.extraction, indent=2)

    except Exception as e:
        return {'error': f"Error processing file: {e}"}
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass




def run_bedrock_reasoning(dossier_data: list[dict]) -> str:
    """
    invokes an Amazon Bedrock Agent to perform reasoning on the provided dossier data.
    The dossier_data is expected to be a list of dictionaries, each representing extracted data from documents
    """
    try:
        AGENT_ID = os.environ['BEDROCK_AGENT_ID']
        AGENT_ALIAS_ID = os.environ['BEDROCK_AGENT_ALIAS_ID']
        SESSION_ID = str(uuid.uuid4())
        
        # Convert dossier data to JSON string
        input_text = json.dumps(dossier_data)
        
        print(f"Invoking Bedrock Agent (Session: {SESSION_ID}) with {len(dossier_data)} documents...")

        response = bedrock_agent_client.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=AGENT_ALIAS_ID,
            sessionId=SESSION_ID,
            inputText=input_text
        )

        completion = ""
        for event in response.get('completion', []): 
            chunk = event.get('chunk', {})
            if 'bytes' in chunk:
                completion += chunk['bytes'].decode('utf-8')
                print(completion, end='') # Print the current completion as it streams in to console

        print("Bedrock reasoning complete.")
        return completion

    except KeyError as e:
        error_msg = f"ERROR: Missing environment variable: {e}. Please set BEDROCK_AGENT_ID and BEDROCK_AGENT_ALIAS_ID."
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"ERROR in run_bedrock_reasoning: {e}"
        print(error_msg)
        return error_msg