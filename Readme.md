# Cloud-Native Hybrid Threat Detection System (IDS + UEBA)

## Overview

This project implements a cloud-based hybrid threat detection framework that combines:

- **Network Intrusion Detection (IDS)** using AWS CloudWatch EC2 metrics
- **User and Entity Behavior Analytics (UEBA)** using AWS CloudTrail logs
- **Risk Fusion Engine** to generate unified threat scores

The system detects volumetric anomalies (e.g., DDoS-style traffic spikes) and correlates them with abnormal user behavior to produce a final risk classification.

---

## Architecture

Internet Traffic  
        ↓  
EC2 Instance (Apache Server)  
        ↓  
CloudWatch Metrics → IDS Engine  
CloudTrail Logs → UEBA Engine  
        ↓  
Risk Fusion Engine  
        ↓  
Final Threat Level

---

## Components

### 1. IDS (Network Layer)
- Uses:
  - `NetworkIn`
  - `NetworkPacketsIn`
- Detects volumetric spikes per minute
- Cloud-native metric-based detection

### 2. UEBA (User Behavior Layer)
- Parses AWS CloudTrail logs
- Extracted features:
  - Activity volume
  - Service diversity
  - Access timing
- Uses anomaly detection model

### 3. Threat Fusion Engine
- Combines:
  - Network Risk Score
  - User Risk Score
- Outputs:
  - Final Risk
  - Threat Level (LOW / MEDIUM / HIGH)

---

## Features

- Live attack simulation support
- Cloud-native detection
- Hybrid ML + rule-based logic
- Multi-layer threat scoring
- Real AWS infrastructure testing

---

## Technologies Used

- Python
- AWS EC2
- AWS CloudWatch
- AWS CloudTrail
- boto3
- scikit-learn
- joblib

---

## Detection Strategy

Instead of relying solely on VPC Flow Logs, this system uses:

- EC2 NetworkIn metrics
- EC2 NetworkPacketsIn metrics

This provides more reliable volumetric anomaly detection in cloud environments.

---

## Demo Flow

1. Run baseline detection
2. Launch sustained traffic simulation
3. Wait for CloudWatch metric update
4. Run detection again
5. Observe risk escalation

---

## Limitations

- CloudWatch metrics update in 60-second intervals
- No deep packet inspection (L7)
- Prototype-level mitigation (no auto-blocking)

---

## Future Improvements

- Dynamic baseline learning
- Auto-mitigation (Security Group / WAF integration)
- Real-time dashboard visualization
- SIEM integration
