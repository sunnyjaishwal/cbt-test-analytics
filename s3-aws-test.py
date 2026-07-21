import os

import boto3

# Credentials come from the environment / AWS default credential chain.
# Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your shell or .env.
# Never hardcode credentials in this file.
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    region_name=os.environ.get("AWS_REGION", "us-east-1"),
)

session = boto3.Session()
creds = session.get_credentials()

print("Access Key:", creds.access_key if creds else None)
print("Secret Key:", creds.secret_key[:4] + "..." if creds and creds.secret_key else None)
print("Token:", creds.token if creds else None)
print("Region:", session.region_name)

response = s3.list_buckets()

for bucket in response["Buckets"]:
    print(bucket["Name"])
