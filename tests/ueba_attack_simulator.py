"""
UEBA Attack Simulator for Hybrid Threat Detection System

This script simulates a compromised insider account (UEBA attack) by 
generating anomalous AWS API activity. It makes a high volume of rapid 
calls across multiple AWS services (IAM, EC2, S3, KMS, CloudWatch) to 
spike the "activity_volume" and "service_diversity" features in the UEBA Isolation Forest model.

Note: Since this hits real AWS APIs, it may take 5-10 minutes for the 
activity to appear in CloudTrail logs and be detected by the dashboard.

Author: Hybrid Threat Detection Team
"""

import boto3
import threading
import time
import sys
import random

print("=" * 50)
print("    Compromised Insider Simulator (UEBA Attack)")
print("=" * 50)
print("This will generate rapid, diverse API calls across.")
print("multiple AWS services to trigger UEBA anomalies.")
print("WARNING: CloudTrail has a 5-15 minute delivery delay.")
print("=" * 50)
print()

# Use default boto3 session
try:
    session = boto3.Session()
    # verify credentials
    sts = session.client('sts')
    identity = sts.get_caller_identity()
    print(f"Executing as: {identity['Arn']}")
except Exception as e:
    print(f"AWS Credentials missing or invalid: {e}")
    sys.exit(1)

DURATION = 60  # seconds to run the simulation
request_count = 0
lock = threading.Lock()

# Define various read-only "snooping" actions across different services
def snooper_thread():
    global request_count
    end_time = time.time() + DURATION
    
    # Initialize clients for various services to spike 'service_diversity'
    ec2 = session.client('ec2', region_name='ap-south-1')
    s3 = session.client('s3', region_name='ap-south-1')
    iam = session.client('iam')
    kms = session.client('kms', region_name='ap-south-1')
    cw = session.client('cloudwatch', region_name='ap-south-1')
    
    local_count = 0
    
    while time.time() < end_time:
        try:
            # Randomly pick a service to hit to simulate "fishing" for access
            action = random.choice([
                lambda: ec2.describe_instances(),
                lambda: ec2.describe_vpcs(),
                lambda: ec2.describe_security_groups(),
                lambda: s3.list_buckets(),
                lambda: iam.get_account_summary(),
                lambda: iam.list_users(),
                lambda: iam.list_roles(),
                lambda: kms.list_keys(),
                lambda: cw.describe_alarms()
            ])
            
            action()
            local_count += 1
            time.sleep(0.1) # Small delay to avoid API throttling limits
            
        except Exception as e:
            # We specifically WANT access denied errors (they get logged as anomalies)
            local_count += 1
            time.sleep(0.1)
            
    with lock:
        request_count += local_count

NUM_THREADS = 5
print(f"Starting {NUM_THREADS} concurrent insider simulation threads...")

start_time = time.time()
threads = []
for i in range(NUM_THREADS):
    t = threading.Thread(target=snooper_thread)
    t.start()
    threads.append(t)

for remaining in range(DURATION, 0, -10):
    print(f"Simulation in progress... ({remaining}s remaining)")
    time.sleep(10)

for t in threads:
    t.join()

elapsed = time.time() - start_time
print()
print("=" * 50)
print("Simulation Completed")
print("=" * 50)
print(f"Total API Calls made: {request_count}")
print("These events are now entering the AWS CloudTrail pipeline.")
print("Watch the 'User Risk' meter on the dashboard. It may take")
print("up to 10-15 minutes for CloudTrail to deliver these logs")
print("to the S3 bucket where the UEBA Engine can read them.")
print("=" * 50)
