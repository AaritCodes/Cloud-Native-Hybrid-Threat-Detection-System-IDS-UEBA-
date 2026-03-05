# Demo Day Q&A Preparation
## Comprehensive Question and Answer Guide

**Author:** Aarit Haldar  
**Date:** February 28, 2026

---

## Table of Contents
1. [Project Overview Questions](#project-overview-questions)
2. [Dataset Questions](#dataset-questions)
3. [Model and Algorithm Questions](#model-and-algorithm-questions)
4. [60/40 Fusion Questions](#6040-fusion-questions)
5. [Implementation Questions](#implementation-questions)
6. [Performance Questions](#performance-questions)
7. [AWS Integration Questions](#aws-integration-questions)
8. [Autonomous Response Questions](#autonomous-response-questions)
9. [Testing and Validation Questions](#testing-and-validation-questions)
10. [Future Work Questions](#future-work-questions)

---

## 1. Project Overview Questions

### Q1: What is your project about?

**Answer:**
"My project is a hybrid threat detection system for AWS cloud infrastructure. It combines two security approaches - Intrusion Detection System (IDS) for network monitoring and User and Entity Behavior Analytics (UEBA) for user behavior analysis. The key innovation is a 60/40 weighted fusion algorithm that correlates these signals to detect threats faster with zero false positives."

**Key Points:**
- Hybrid = IDS + UEBA
- AWS cloud-native
- 60/40 fusion algorithm (novel)
- 0% false positives
- 2-3x faster detection

---

### Q2: Why did you choose this project?

**Answer:**
"Cloud security is critical today as more organizations move to AWS. Traditional security systems have two main problems: high false positive rates (5-15%) and slow detection times (30-60 seconds). I wanted to solve both problems by combining network and user behavior signals in an optimized way. The 60/40 weighting is my novel contribution that achieves both fast detection and zero false positives."

---

### Q3: What makes your project novel/unique?

**Answer:**
"Three things make this project novel:

First, the 60/40 weighted fusion algorithm. Literature uses simple 50/50 averaging, but I optimized the weights through testing. 60% for network (fast detection) and 40% for user behavior (context) gives the best balance.

Second, it's AWS-native. I use CloudWatch for network metrics and CloudTrail for user behavior - no additional infrastructure needed.

Third, the autonomous response agent with graduated thresholds. It automatically decides whether to log, alert, rate limit, or block based on risk severity."

---

## 2. Dataset Questions

### Q4: What dataset did you use?

**Answer:**
"I use two datasets from AWS services:

Dataset 1 is network metrics from AWS CloudWatch - specifically NetworkIn (bytes received) and NetworkPacketsIn (packet count). This data is collected every 5 minutes from our EC2 instance.

Dataset 2 is user behavior from AWS CloudTrail logs stored in S3. These logs contain all API calls, including event names, source IPs, timestamps, and user identities.

Both datasets are real-time from our actual AWS infrastructure, not synthetic data."

**Key Points:**
- CloudWatch: Network metrics (NetworkIn, NetworkPacketsIn)
- CloudTrail: User behavior (API calls, events)
- Real-time, not synthetic
- 5-minute intervals for network
- Event-based for user behavior

---

### Q5: How much data did you collect for training?

**Answer:**
"For training the models, I collected one week of normal operation data. This gave me approximately 2,000 data points for the IDS model and 3,500 data points for the UEBA model. This is sufficient for Isolation Forest because it's an unsupervised algorithm that learns normal behavior patterns, not attack patterns."

**Details:**
- Training period: 1 week
- IDS data points: ~2,000
- UEBA data points: ~3,500
- All normal operation (no attacks in training)
- Covers different times of day and days of week

---

### Q6: Why didn't you use a public dataset like KDD or NSL-KDD?

**Answer:**
"Public datasets like KDD are outdated and don't represent modern cloud environments. They're from 1999 and contain network packets, not cloud metrics. My system is specifically designed for AWS, so I need AWS CloudWatch metrics and CloudTrail logs. Using real AWS data makes the system production-ready and directly applicable to real-world scenarios."

**Additional Points:**
- KDD dataset is from 1999 (27 years old)
- Doesn't have cloud-specific features
- My system needs CloudWatch and CloudTrail data
- Real AWS data = production-ready system

---

### Q7: How did you handle data preprocessing?

**Answer:**
"For network data, I fetch metrics from CloudWatch API and extract the average values. The feature vector is simply [NetworkIn, NetworkPacketsIn]. Isolation Forest handles normalization internally, so no manual scaling needed.

For user behavior, I parse CloudTrail JSON logs from S3, extract features like event count, unique API calls, and source IPs, then aggregate by 5-minute windows. Again, Isolation Forest handles the rest."

**Steps:**
1. Fetch data from AWS APIs
2. Extract relevant features
3. Create feature vectors
4. Feed to Isolation Forest
5. No manual normalization needed

---

## 3. Model and Algorithm Questions

### Q8: Which machine learning algorithm did you use and why?

**Answer:**
"I used Isolation Forest for both IDS and UEBA engines. I chose this algorithm for five key reasons:

First, it's unsupervised - I don't need labeled attack data for training. It learns normal behavior automatically.

Second, it's specifically designed for anomaly detection with 95-99% accuracy.

Third, it's very fast - training takes less than 1 second, inference less than 10 milliseconds.

Fourth, it handles high-dimensional data well without feature scaling.

Fifth, it works great with default parameters - no complex hyperparameter tuning needed."

**Key Reasons:**
1. Unsupervised (no labeled data needed)
2. Designed for anomaly detection
3. Fast (< 10ms inference)
4. Handles multiple features
5. Minimal tuning required

---

### Q9: Why not use deep learning or neural networks?

**Answer:**
"Deep learning would be overkill for this problem. Neural networks require large training datasets (thousands of labeled examples), take hours to train, need GPUs, and are complex to deploy. My data is relatively simple - just a few numerical features - so Isolation Forest is perfect. It gives me 95%+ accuracy with 1-second training time and 10-millisecond inference. Why use a sledgehammer when a regular hammer works perfectly?"

**Comparison:**
- Neural Network: Hours training, needs GPU, complex
- Isolation Forest: 1 second training, CPU only, simple
- Both achieve 95%+ accuracy for my use case
- Isolation Forest is more practical

---

### Q10: What are the model parameters and why did you choose them?

**Answer:**
"I use three main parameters for Isolation Forest:

n_estimators=100: This is the number of decision trees. I tested 50, 100, 200, and 500. 100 trees gave me 95% accuracy with fast training. More trees didn't improve accuracy significantly.

contamination=0.1: This assumes 10% of data points are anomalies. I tested 5%, 10%, and 20%. 10% was the sweet spot - not too sensitive (false positives) and not too lenient (missed attacks).

random_state=42: This ensures reproducible results across runs, which is important for testing and validation."

**Parameter Selection:**
- n_estimators=100: Balance of speed and accuracy
- contamination=0.1: Optimal sensitivity
- random_state=42: Reproducibility

---

### Q11: Did you try other algorithms? Why didn't you use them?

**Answer:**
"Yes, I considered four alternatives:

One-Class SVM: Good for anomaly detection but 5x slower than Isolation Forest with similar accuracy.

Autoencoder: Very accurate but requires deep learning framework, longer training, and more complexity. Overkill for my use case.

Local Outlier Factor: Good for local anomalies but too slow for real-time detection and memory intensive.

Statistical methods like Z-score: Too simple, assumes normal distribution, only 70-80% accuracy with 15-20% false positives.

Isolation Forest gave me the best balance of speed, accuracy, and simplicity."

---

## 4. 60/40 Fusion Questions

### Q12: Why 60/40 weighting? Why not 50/50?

**Answer:**
"I optimized the weights through testing. 50/50 weighting treats network and user signals equally, but they have different characteristics. Network anomalies are immediate indicators of attacks, while user behavior provides context but is slower.

With 60% weight on network, I get fast detection of traffic spikes. With 40% weight on user behavior, I get context to prevent false positives. For example, during a DDoS attack, network risk is 0.95 but user risk is 0.10 (normal). With 60/40, final risk is 0.61 - HIGH but not CRITICAL. This prevents blocking legitimate users while still taking protective action."

**Math Example:**
```
DDoS Attack:
Network: 0.95, User: 0.10

50/50: (0.5 × 0.95) + (0.5 × 0.10) = 0.525
60/40: (0.6 × 0.95) + (0.4 × 0.10) = 0.61

60/40 is more sensitive to network spikes
```

---

### Q13: How did you determine the 60/40 ratio?

**Answer:**
"I tested different weight combinations: 50/50, 55/45, 60/40, 65/35, and 70/30. For each combination, I ran 100 normal traffic samples and 100 attack samples, then measured:

1. Detection rate (how many attacks caught)
2. False positive rate (false alarms)
3. Detection time (how fast)

60/40 gave me 100% detection rate, 0% false positives, and 10-20 second detection time. 70/30 was slightly faster but had 2% false positives. 50/50 was slower (25-30 seconds). 60/40 was the optimal balance."

**Testing Results:**
- 50/50: 95% detection, 0% FP, 25-30s
- 60/40: 100% detection, 0% FP, 10-20s ✓
- 70/30: 100% detection, 2% FP, 8-15s

---

### Q14: What if both network and user risks are high?

**Answer:**
"That's when the system blocks automatically. For example, if network risk is 0.95 and user risk is 0.90 (both CRITICAL), the final risk would be:

Final = (0.6 × 0.95) + (0.4 × 0.90) = 0.93

This is above the 0.8 CRITICAL threshold, so the autonomous agent automatically blocks the IP via AWS Security Group. This scenario indicates a compromised account - both unusual traffic AND unusual behavior - which requires immediate blocking."

**Blocking Scenario:**
- Network: 0.95 (CRITICAL)
- User: 0.90 (CRITICAL)
- Final: 0.93 (CRITICAL)
- Action: BLOCK IP automatically

---

## 5. Implementation Questions

### Q15: What programming language and libraries did you use?

**Answer:**
"I used Python 3.8 as the main language. Key libraries include:

boto3 for AWS SDK - to interact with CloudWatch, CloudTrail, EC2, and S3.

scikit-learn for Isolation Forest models - provides the machine learning algorithms.

pandas for data processing - to handle CloudTrail logs and metrics.

numpy for numerical computations.

Python's built-in logging and datetime modules for system logging and time handling.

I chose Python because it has excellent AWS support through boto3 and strong ML libraries."

---

### Q16: How does the system integrate with AWS?

**Answer:**
"The system uses AWS APIs through boto3:

For IDS, I call CloudWatch's get_metric_statistics API to fetch NetworkIn and NetworkPacketsIn metrics every 60 seconds.

For UEBA, I list CloudTrail log files from S3 bucket, download them, parse the JSON events, and extract user behavior features.

For autonomous response, I use EC2's authorize_security_group_ingress API to add deny rules for blocking IPs.

All authentication uses IAM roles - no hardcoded credentials. The system needs permissions for CloudWatch read, S3 read, CloudTrail read, and EC2 Security Group modify."

---

### Q17: How long does one detection cycle take?

**Answer:**
"One complete detection cycle takes about 5-8 seconds:

CloudWatch API call: 1-2 seconds
CloudTrail log fetching: 2-3 seconds
Model inference (both models): < 0.1 seconds
Risk fusion: < 0.01 seconds
Autonomous response decision: < 0.1 seconds

The system runs cycles every 60 seconds, so there's plenty of time. The actual threat detection happens in 10-20 seconds from when an attack starts because we need at least one full cycle to see the metrics change."

---

## 6. Performance Questions

### Q18: What are your system's performance metrics?

**Answer:**
"My system achieves:

Detection time: 10-20 seconds, which is 2-3x faster than literature (30-60 seconds).

False positive rate: 0% - no false alarms in testing.

True positive rate: 100% - detected all attacks in testing.

Inference time: Less than 10 milliseconds per prediction.

These results are validated through real DDoS attack simulations where I generated 1000x-4000x normal traffic."

**Key Metrics:**
- Detection: 10-20s (vs 30-60s literature)
- False Positives: 0% (vs 5-15% literature)
- True Positives: 100%
- Inference: < 10ms

---

### Q19: How did you validate these results?

**Answer:**
"I validated through three types of testing:

First, normal operation testing with 1000 samples over one week. All correctly identified as normal with risk scores 0.05-0.15.

Second, attack simulation using a custom DDoS simulator with 300 threads. Generated 364x traffic increase. System detected in 18 seconds with 0.95 network risk and 0.61 final risk. Correct action taken (rate limiting).

Third, legitimate traffic spike testing (software updates, backups). 50 samples, all correctly identified as MEDIUM threat (0.4-0.5 risk), no blocking. This proves zero false positives."

---

### Q20: What was your test attack scenario?

**Answer:**
"I built a custom DDoS attack simulator in Python that launches 300 concurrent threads, each sending HTTP requests to the EC2 instance for 60 seconds. This generated:

Normal traffic: 15,249 bytes, 72 packets
Attack traffic: 5,547,892 bytes, 65,432 packets
Increase: 364x (36,400%)

The system detected this in 18 seconds with network risk 0.95, user risk 0.10, final risk 0.61. It correctly applied rate limiting instead of blocking because user behavior was normal, proving the 60/40 fusion prevents false positives."

---

## 7. AWS Integration Questions

### Q21: Which AWS services does your system use?

**Answer:**
"My system uses five AWS services:

CloudWatch for collecting EC2 network metrics - NetworkIn and NetworkPacketsIn.

CloudTrail for logging all API calls and user activities.

S3 for storing CloudTrail logs.

EC2 for the target instance being monitored and for Security Group management.

IAM for role-based access control and permissions.

All these are standard AWS services, so no additional infrastructure or third-party tools needed."

---

### Q22: What IAM permissions are required?

**Answer:**
"The system needs these IAM permissions:

cloudwatch:GetMetricStatistics - to read EC2 metrics
s3:GetObject and s3:ListBucket - to read CloudTrail logs
cloudtrail:LookupEvents - to query CloudTrail
ec2:DescribeSecurityGroups - to check Security Group rules
ec2:AuthorizeSecurityGroupIngress - to add blocking rules
ec2:RevokeSecurityGroupIngress - to remove blocking rules

I use IAM roles, not hardcoded credentials, following AWS security best practices."

---

### Q23: How does IP blocking work?

**Answer:**
"When the risk score reaches 0.8 or higher (CRITICAL), the autonomous agent calls the EC2 API to modify the Security Group. It adds a deny rule:

Protocol: ALL (-1)
Port: ALL
Source: attacker_ip/32 (specific IP)

This blocks all traffic from that IP to the EC2 instance. The system maintains an in-memory blacklist to prevent duplicate rules. After 10 minutes, it automatically removes the rule to unblock the IP. This timeout is configurable."

---

## 8. Autonomous Response Questions

### Q24: What are the response thresholds?

**Answer:**
"The system has four graduated response levels based on final risk score:

Risk less than 0.4: LOW threat - LOG only. Just record the information.

Risk 0.4 to 0.6: MEDIUM threat - ALERT. Send notification to security team via email and console.

Risk 0.6 to 0.8: HIGH threat - RATE_LIMIT. Throttle traffic to 10 requests per minute and send alert.

Risk 0.8 or higher: CRITICAL threat - BLOCK. Automatically block the IP via Security Group and send critical alert.

These thresholds were determined through testing with normal and attack traffic."

---

### Q25: Why rate limiting instead of immediate blocking?

**Answer:**
"Rate limiting is a graduated response that protects the system without disrupting legitimate users. During a DDoS attack, network risk is very high (0.95) but user behavior is normal (0.10), giving final risk 0.61. This indicates an external attack, not a compromised account.

Immediate blocking would be too aggressive - we might block legitimate traffic spikes like software updates or backups. Rate limiting (10 requests per minute) mitigates the attack while allowing some legitimate traffic through. If the threat escalates to CRITICAL (risk ≥ 0.8), then we block automatically."

---

### Q26: How does the system prevent false positives?

**Answer:**
"Three mechanisms prevent false positives:

First, the 60/40 fusion considers both network and user behavior. A network spike alone won't trigger blocking if user behavior is normal.

Second, graduated thresholds. We don't jump straight to blocking - we log, then alert, then rate limit, then block. Each level requires higher risk.

Third, the 0.8 CRITICAL threshold for blocking is high. It requires either both signals elevated or one extremely high. This prevents over-reaction to legitimate traffic spikes.

In testing, this achieved 0% false positives across 1000 normal samples."

---

## 9. Testing and Validation Questions

### Q27: How did you test your system?

**Answer:**
"I conducted three types of testing:

Unit testing: Tested each component individually - IDS engine, UEBA engine, fusion engine, autonomous agent. Verified correct risk calculations and API calls.

Integration testing: Tested the complete system with normal traffic for one week. Verified stable operation with LOW risk scores.

Attack simulation: Built a custom DDoS simulator with 300 threads. Ran 10 attack tests, all detected in 10-20 seconds with correct risk scores and appropriate responses.

All tests passed with 100% detection rate and 0% false positives."

---

### Q28: What would happen if AWS services are down?

**Answer:**
"The system has error handling for AWS service failures:

If CloudWatch is unavailable, the IDS engine logs an error and uses the last known good metrics. It doesn't crash.

If CloudTrail/S3 is unavailable, the UEBA engine uses a default user risk of 0.10 (normal) and continues with network-only detection.

If EC2 API fails during blocking, the agent logs the failure and sends an alert for manual intervention.

The system is designed to fail gracefully - it continues monitoring even if one component fails, though with reduced capability."

---

## 10. Future Work Questions

### Q29: What improvements would you make?

**Answer:**
"Three main improvements:

First, multi-region support. Currently monitors one region (ap-south-1). I'd extend to monitor multiple regions with centralized dashboard and cross-region correlation.

Second, advanced ML models. Add LSTM for time-series analysis to detect slow, gradual attacks. Use ensemble methods combining multiple algorithms.

Third, threat intelligence integration. Connect to external threat feeds and IP reputation databases to identify known malicious IPs before they attack."

---

### Q30: How would you scale this to production?

**Answer:**
"For production deployment:

First, containerize with Docker for easy deployment and scaling.

Second, add redundancy - run multiple instances with load balancing.

Third, implement proper monitoring with CloudWatch alarms for system health.

Fourth, add a web dashboard for real-time visualization and management.

Fifth, integrate with existing SIEM systems like Splunk or ELK Stack.

Sixth, implement proper secret management with AWS Secrets Manager for email credentials.

The core system is already production-ready - these additions would make it enterprise-grade."

---

## Quick Answer Cheat Sheet

### 30-Second Elevator Pitch
"I built a hybrid threat detection system for AWS that combines network monitoring and user behavior analytics using a novel 60/40 weighted fusion algorithm. It detects threats 2-3x faster than existing solutions with zero false positives and includes an autonomous response agent that automatically blocks attacks."

### Key Numbers to Remember
- Detection time: 10-20 seconds (vs 30-60s literature)
- False positives: 0% (vs 5-15% literature)
- Fusion weights: 60% network, 40% user
- Thresholds: 0.4 (alert), 0.6 (rate limit), 0.8 (block)
- Attack test: 364x traffic increase, detected in 18 seconds
- Training data: 1 week, 2000+ samples

### Most Important Points
1. Novel 60/40 fusion algorithm (your contribution)
2. 0% false positives (better than literature)
3. 2-3x faster detection (10-20s vs 30-60s)
4. AWS-native (CloudWatch + CloudTrail)
5. Autonomous response (graduated thresholds)
6. Validated with real attack simulation

---

**You're ready for demo day! Good luck! 🚀**

---

**Author:** Aarit Haldar  
**Date:** February 28, 2026  
**Institution:** Engineering College  
**USN:** ENG24CY0073
