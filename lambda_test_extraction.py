import json
import os
import tempfile
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

def lambda_handler(event, context):

    # Get configuration from environment variables
    try:
        LANDINGAI_ENDPOINT_ID = os.environ['LANDINGAI_ENDPOINT_ID']
        BUCKET_NAME = os.environ['S3_UPLOADS_BUCKET']
    except KeyError as e:
        print(f"Environment variable {e} not set.")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Missing environment variable: {e}'})
        }
    
    TEST_FILE_PATH = "statement_month_1.pdf"
    print(f"Starting processing for file: s3://{BUCKET_NAME}/{TEST_FILE_PATH}")

    
    with tempfile.TemporaryDirectory() as tmpdirname:
        try:
            local_file_path = os.path.join(tmpdirname, TEST_FILE_PATH)
            s3_client.download_file(BUCKET_NAME, TEST_FILE_PATH, local_file_path)
            print(f"Successfully downloaded file to temporary path: {local_file_path}")

            # Process the file with LandingAI
            print("Processing file with LandingAI...")
            #initialize landingai ade client
            ade = LandingAIADE()
            #parse the document
            response = ade.parse(
                document_url=local_file_path, 
                model="dpt-2-latest"
            )

            if not response.markdown:
                print("No markdown content returned from LandingAI.")
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': 'LandingAI returned no content'})
                }

            # Process the markdown content
            print("Processing markdown content...")
            # Here you can add your logic to process the markdown content
            for block in response.markdown:
                print(block)
            
        except Exception as e:
            print(f"Error downloading file: {e}")
            return {
                'statusCode': 500,
                'body': json.dumps({'error': f'Failed to download file: {e}'})
            }




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
        print("Extraction completed successfully")
        
        return {"markdown": response.markdown}
        
    except Exception as e:
        return {'error': f"Errorrr processing file: {e}"}
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass