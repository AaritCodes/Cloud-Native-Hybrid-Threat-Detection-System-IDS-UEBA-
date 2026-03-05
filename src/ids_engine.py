import boto3
from datetime import datetime, timedelta
import joblib
import numpy as np

REGION = "ap-south-1"
INSTANCE_ID = "i-029c928e980af3165"


class IDSEngine:

    def __init__(self, model_path):
        """Initialize IDS engine with trained Isolation Forest model"""
        self.cloudwatch = boto3.client("cloudwatch", region_name=REGION)
        
        # Load the trained Isolation Forest model
        print(f"Loading IDS model from {model_path}...")
        self.model = joblib.load(model_path)
        print("✓ IDS model loaded successfully")
        
        # Store baseline for comparison
        self.baseline_network_in = 15000  # 15KB
        self.baseline_packets_in = 72     # 72 packets

    # ------------------------------------------
    # Get Metric Helper
    # ------------------------------------------
    def get_metric(self, metric_name):

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)  # Back to 5 minutes for better data

        print(f"  Fetching {metric_name}...", end=" ", flush=True)
        
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
            Period=300,  # 5-minute period for better aggregation
            Statistics=['Sum', 'Average']
        )

        datapoints = response.get('Datapoints', [])

        if not datapoints:
            # Return baseline values instead of 0 when no CloudWatch data
            if metric_name == "NetworkIn":
                print(f"No data (using baseline: {self.baseline_network_in:,} bytes)")
                return self.baseline_network_in
            elif metric_name == "NetworkPacketsIn":
                print(f"No data (using baseline: {self.baseline_packets_in} packets)")
                return self.baseline_packets_in
            print("No data")
            return 0

        latest = sorted(datapoints, key=lambda x: x['Timestamp'])[-1]
        value = latest.get('Sum', latest.get('Average', 0))
        print(f"Done ({value:.0f})")
        return value

    # ------------------------------------------
    # Detect Traffic Spike using Isolation Forest
    # ------------------------------------------
    def detect(self):

        network_in = self.get_metric("NetworkIn")
        packets_in = self.get_metric("NetworkPacketsIn")

        # Prepare features for the model
        # Features: [network_bytes, network_packets, bytes_per_packet, packet_rate]
        bytes_per_packet = network_in / packets_in if packets_in > 0 else 0
        packet_rate = packets_in / 300  # packets per second (5-minute window)
        
        features = np.array([[
            network_in,
            packets_in,
            bytes_per_packet,
            packet_rate
        ]])
        
        # Use Isolation Forest model to predict anomaly
        # Returns -1 for anomalies, 1 for normal
        prediction = self.model.predict(features)[0]
        
        # Get anomaly score (lower = more anomalous)
        anomaly_score = self.model.decision_function(features)[0]
        
        # Convert anomaly score to risk (0-1 scale)
        # Isolation Forest scores typically range from -0.5 to 0.5
        # More negative = more anomalous = higher risk
        if prediction == -1:  # Anomaly detected
            # Map anomaly score to risk (0.6 to 0.95)
            # More negative score = higher risk
            risk = min(0.95, max(0.60, 0.75 - (anomaly_score * 0.5)))
        else:  # Normal traffic
            # Low risk for normal traffic
            risk = 0.05
        
        # Add rule-based boost for extreme values (safety net)
        if network_in > 8_000_000 or packets_in > 15_000:
            risk = max(risk, 0.95)  # Ensure critical threats are caught
        elif network_in > 4_000_000 or packets_in > 8_000:
            risk = max(risk, 0.85)
        
        print(f"  Model prediction: {'ANOMALY' if prediction == -1 else 'NORMAL'} (score: {anomaly_score:.3f}, risk: {risk:.2f})")

        return [{
            "ip": "EC2_INSTANCE",
            "network_risk": risk,
            "network_bytes": network_in,
            "network_packets": packets_in
        }]