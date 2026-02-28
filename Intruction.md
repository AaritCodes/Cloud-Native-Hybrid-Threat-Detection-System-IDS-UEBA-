# Project Execution Instructions

## Prerequisites

- Python 3.9+
- AWS CLI configured
- EC2 instance running Apache
- CloudWatch metrics enabled
- CloudTrail logging enabled

---

## Step 1 – Install Dependencies

pip install boto3 scikit-learn joblib requests

---

## Step 2 – Run Baseline Detection

python main.py

Expected Output:
- Network Risk: LOW
- Threat Level: LOW

---

## Step 3 – Launch Attack Simulation

In a new terminal:

python attack_simulator.py

This generates sustained traffic for 60 seconds.

---

## Step 4 – Wait for CloudWatch Update

Wait approximately 60–120 seconds for metrics to refresh.

---

## Step 5 – Run Detection Again

python main.py

Expected Output:
- NetworkIn spike
- NetworkPacketsIn spike
- Network Risk: HIGH
- Threat Level: HIGH

---

## Troubleshooting

If risk does not spike:
- Ensure EC2 instance is publicly accessible
- Confirm NetworkIn metric increases in CloudWatch
- Wait additional 60 seconds
- Verify attack simulator completed successfully

---

## Demo Tips

1. Show baseline first.
2. Run attack.
3. Wait.
4. Show spike.
5. Explain architecture clearly.

Keep demo under 3 minutes.
