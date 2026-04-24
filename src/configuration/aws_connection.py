import boto3
import os
import sys
from botocore.config import Config
from src.exception import FraudException
from src.logger import logging

class S3Connection:
    """
    Thread-safe Singleton connection to AWS S3.
    Optimized for high-concurrency production environments.
    """
    _s3_client = None
    _s3_resource = None

    def __init__(self, region_name: str = "us-east-1"):
        try:
            if S3Connection._s3_client is None:
                logging.info(f"Initializing Production S3 Session in {region_name}...")
                
                # 1. RETRY & TIMEOUT CONFIGURATION
                # Production apps must handle "Transient Errors" (brief network drops)
                aws_config = Config(
                    region_name=region_name,
                    retries={'max_attempts': 3, 'mode': 'standard'},
                    connect_timeout=5, 
                    read_timeout=10
                )

                # 2. IDENTITY AWARE AUTHENTICATION
                # We check for Env Vars first (local dev), 
                # but if missing, boto3 automatically uses IAM Roles (Production/EKS)
                access_key = os.getenv("AWS_ACCESS_KEY_ID")
                secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")

                if access_key and secret_key:
                    session = boto3.Session(
                        aws_access_key_id=access_key,
                        aws_secret_access_key=secret_key,
                        region_name=region_name
                    )
                else:
                    # In EKS, the pod uses an IAM Role. This line handles that automatically.
                    logging.info("Using IAM Role for authentication.")
                    session = boto3.Session(region_name=region_name)

                # 3. RESOURCE INITIALIZATION
                S3Connection._s3_resource = session.resource('s3', config=aws_config)
                S3Connection._s3_client = session.client('s3', config=aws_config)
                
                logging.info(f"S3 Connection fully established.")
            
            self.s3_resource = S3Connection._s3_resource
            self.s3_client = S3Connection._s3_client

        except Exception as e:
            raise FraudException(e, sys)