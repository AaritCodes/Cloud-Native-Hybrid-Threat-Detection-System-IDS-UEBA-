import boto3
from datetime import datetime, timedelta

REGION = "ap-south-1"
INSTANCE_ID = "i-029c928e980af3165"


class IDSEngine:

    def __init__(self, model_path=None):
        self.cloudwatch = boto3.client("cloudwatch", region_name=REGION)

    # ------------------------------------------
    # Get Metric Helper
    # ------------------------------------------
    def get_metric(self, metric_name):

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)

        response = self.cloudwatch.get_metric_statistics(
            Namespace='AWS/EC2',
            MetricName=metric_name,
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': INSTANCE_ID
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=60,
            Statistics=['Sum']
        )

        datapoints = response.get('Datapoints', [])

        if not datapoints:
            return 0

        latest = sorted(datapoints, key=lambda x: x['Timestamp'])[-1]
        return latest['Sum']

    # ------------------------------------------
    # Detect Traffic Spike
    # ------------------------------------------
    def detect(self):

        network_in = self.get_metric("NetworkIn")
        packets_in = self.get_metric("NetworkPacketsIn")

        print("DEBUG: NetworkIn bytes:", network_in)
        print("DEBUG: NetworkPacketsIn:", packets_in)

        # ---- Dynamic Spike Logic ----

        if network_in > 8_000_000 or packets_in > 15_000:
            risk = 0.95
        elif network_in > 4_000_000 or packets_in > 8_000:
            risk = 0.85
        elif network_in > 1_500_000 or packets_in > 3_000:
            risk = 0.60
        else:
            risk = 0.05

        return [{
            "ip": "EC2_INSTANCE",
            "network_risk": risk
        }]