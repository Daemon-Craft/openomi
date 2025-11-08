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
        LANDINGAI_API_KEY = os.environ['LANDINGAI_API_KEY']
        BUCKET_NAME = os.environ['S3_UPLOADS_BUCKET']
    except KeyError as e:
        print(f"Environment variable {e} not set.")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Missing environment variable: {e}'})
        }
    
    TEST_FILE_PATH = "test_documents/statement_month_1.pdf"
    print(f"Starting processing for file: s3://{BUCKET_NAME}/{TEST_FILE_PATH}")

    # Read the test file from S3


    # Parse the incoming event to extract file information
    body = json.loads(event['body'])
    files_info = body.get('files', [])
    
    results = []
    
    for file_info in files_info:
        file_name = file_info['file_name']
        s3_bucket = file_info['s3_bucket']
        s3_key = file_info['s3_key']
        
        # Download the file from S3 to a temporary location
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            s3_client.download_fileobj(s3_bucket, s3_key, tmp_file)
            tmp_file_path = tmp_file.name
        
        # Simulate processing the file (e.g., extracting text, analyzing content)
        # Here we just read the file size as a placeholder for actual processing
        file_size = os.path.getsize(tmp_file_path)
        
        # Clean up the temporary file
        os.remove(tmp_file_path)
        
        # Append the result for this file
        results.append({
            'file_name': file_name,
            'file_size': file_size,
            'status': 'Processed'
        })
    
    # Return the results as a JSON response
    return {
        'statusCode': 200,
        'body': json.dumps({'results': results})
    }