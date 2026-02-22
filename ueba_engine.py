import boto3
import json
import gzip
import joblib
import pandas as pd
import datetime
from io import BytesIO

REGION = "ap-south-1"
BUCKET = "aws-cloudtrail-logs-468087121208-269f0498"
ACCOUNT_ID = "468087121208"

class UEBAEngine:

    def __init__(self, model_path):
        self.model = joblib.load(model_path)
        self.s3 = boto3.client("s3", region_name=REGION)

    # ---------------------------------------------------
    # Fetch only today's CloudTrail logs (FAST VERSION)
    # ---------------------------------------------------
    def fetch_logs(self):

        logs = []

        today = datetime.datetime.utcnow()

        prefix = (
            f"AWSLogs/{ACCOUNT_ID}/CloudTrail/"
            f"{REGION}/{today.year}/"
            f"{today.month:02d}/{today.day:02d}/"
        )

        print("Fetching logs from prefix:", prefix)

        response = self.s3.list_objects_v2(
            Bucket=BUCKET,
            Prefix=prefix,
            MaxKeys=5   # only latest few files
        )

        if "Contents" not in response:
            print("No logs found for today.")
            return pd.DataFrame()

        for obj in response["Contents"]:
            key = obj["Key"]

            if not key.endswith(".json.gz"):
                continue

            print("Processing:", key)

            file_obj = self.s3.get_object(Bucket=BUCKET, Key=key)

            bytestream = BytesIO(file_obj["Body"].read())

            with gzip.GzipFile(fileobj=bytestream) as f:
                data = json.loads(f.read().decode("utf-8"))

                for record in data["Records"]:
                    logs.append({
                        "user": record.get("userIdentity", {}).get("type", "system"),
                        "ip": record.get("sourceIPAddress"),
                        "time": record.get("eventTime"),
                        "service": record.get("eventSource"),
                        "event": record.get("eventName")
                    })

        return pd.DataFrame(logs)

    # ---------------------------------------------------
    # Feature Engineering
    # ---------------------------------------------------
    def engineer_features(self, df):

        df["time"] = pd.to_datetime(df["time"], errors="coerce")

        df["hour"] = df["time"].dt.hour.fillna(0)
        df["day"] = df["time"].dt.dayofweek.fillna(0)

        df["activity_volume"] = df.groupby("user")["event"].transform("count")
        df["service_diversity"] = df.groupby("user")["service"].transform("nunique")

        features = df[[
            "hour",
            "day",
            "activity_volume",
            "service_diversity"
        ]].fillna(0)

        df["anomaly_score"] = self.model.decision_function(features)

        # Normalize anomaly score to 0-1 risk
        min_score = df["anomaly_score"].min()
        max_score = df["anomaly_score"].max()

        if max_score - min_score == 0:
            df["user_risk"] = 0.1
        else:
            df["user_risk"] = 1 - (
                (df["anomaly_score"] - min_score) /
                (max_score - min_score)
            )

        return df

    # ---------------------------------------------------
    # Main Detection Function
    # ---------------------------------------------------
    def detect(self):

        df = self.fetch_logs()

        if df.empty:
            print("No UEBA data available.")
            return []

        df = self.engineer_features(df)

        results = []

        for _, row in df.iterrows():
            results.append({
                "ip": row["ip"],
                "user": row["user"],
                "user_risk": float(row["user_risk"])
            })

        return results