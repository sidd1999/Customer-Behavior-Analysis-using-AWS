import json
import boto3
from collections import defaultdict

# Initialize the S3 client
s3_client = boto3.client('s3')

def lambda_handler(event, context):
    try:
        # Extract bucket name and object key from the event
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = event['Records'][0]['s3']['object']['key']
        
        # Log the received file details
        print(f"Processing file from bucket: {bucket}, key: {key}")
        
        # Get the object from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        records = [json.loads(line) for line in content.splitlines()]
        
        # Initialize counters for views and abandonment
        product_views = defaultdict(int)
        product_abandonments = defaultdict(int)
        
        # Process each record to count views and abandonments
        for record in records:
            product_id = record.get('product_id')
            action_type = record.get('action_type')
            
            if action_type == 'view':
                product_views[product_id] += 1
            elif action_type == 'add_to_cart':
                product_abandonments[product_id] += 1
        
        # Compile the results into a structured dictionary
        analytics_data = {
            'frequent_views': dict(product_views),
            'high_abandonments': dict(product_abandonments)
        }
        
        # Prepare the output key and data for saving to S3
        output_key = f"processed/analytics_{key.split('/')[-1].replace('.json', '')}.json"
        output_data = json.dumps(analytics_data)
        
        # Save the processed analytics data back to S3
        s3_client.put_object(Bucket=bucket, Key=output_key, Body=output_data)
        
        # Log success
        print(f"Analytics data saved to {output_key} in bucket {bucket}")
        
        return {
            'statusCode': 200,
            'body': json.dumps(f'Successfully processed and saved analytics data to {output_key}')
        }
    
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing file: {str(e)}')
        }