# Code Documentation
## Detailed Code Walkthrough

**Author:** Aarit Haldar  
**Date:** February 2026

---

## Table of Contents
1. [Project Structure](#project-structure)
2. [IDS Engine (ids_engine.py)](#ids-engine)
3. [UEBA Engine (ueba_engine.py)](#ueba-engine)
4. [Threat Fusion Engine (threat_fusion_engine.py)](#threat-fusion-engine)
5. [Autonomous Response Agent (autonomous_response_agent.py)](#autonomous-response-agent)
6. [Alert System (alert_system.py)](#alert-system)
7. [Main System (enhanced_main_with_agent.py)](#main-system)
8. [Attack Simulator (tests/attack_simulator.py)](#attack-simulator)

---

## 1. Project Structure

```
src/
├── ids_engine.py                 # Network anomaly detection
├── ueba_engine.py                # User behavior analytics
├── threat_fusion_engine.py       # Risk correlation (60/40)
├── autonomous_response_agent.py  # Automated response
├── alert_system.py               # Multi-channel alerts
├── enhanced_main_with_agent.py   # Main system (with agent)
├── enhanced_main.py              # Main system (monitoring only)
└── dashboard.py                  # Visualization (optional)

models/
├── ddos_model.pkl                # Trained IDS model
└── uba_model.pkl                 # Trained UEBA model

tests/
└── attack_simulator.py           # DDoS attack simulation

config/
├── alert_config.json             # Email/alert settings
└── alert_config.json.template    # Template for setup

logs/
├── autonomous_response.log       # Agent actions
└── threat_alerts.json            # Alert history
```

---

## 2. IDS Engine (ids_engine.py)

### Purpose
Monitors network traffic using AWS CloudWatch metrics to detect volumetric anomalies.

### Key Components

#### Class: IDSEngine
```python
class IDSEngine:
    def __init__(self, model_path):
        # Load pre-trained Isolation Forest model
        # Initialize AWS CloudWatch client
        # Set EC2 instance ID for monitoring
```

**Initialization:**
- Loads trained Isolation Forest model from pickle file
- Creates boto3 CloudWatch client for AWS API calls
- Sets target EC2 instance ID (i-029c928e980af3165)
- Configures region (ap-south-1)

#### Method: get_metric()
```python
def get_metric(self, metric_name):
    # Fetch metric from CloudWatch
    # Parameters: MetricName, InstanceId, Period, Statistics
    # Returns: Average value over last 10 minutes
```

**What it does:**
1. Calls CloudWatch get_metric_statistics API
2. Fetches NetworkIn or NetworkPacketsIn metrics
3. Time range: Last 10 minutes
4. Period: 5-minute intervals
5. Returns average value

**Example:**
```python
network_bytes = ids.get_metric("NetworkIn")
# Returns: 15249.0 (normal) or 5547892.0 (attack)
```

#### Method: detect()
```python
def detect(self):
    # Collect network metrics
    # Create feature vector
    # Run Isolation Forest prediction
    # Calculate risk score
    # Return results with IP and risk
```

**Detection Process:**
1. Fetch NetworkIn and NetworkPacketsIn metrics
2. Create feature vector: [bytes, packets]
3. Feed to Isolation Forest model
4. Get anomaly score (-1 to 1)
5. Convert to risk score (0 to 1)
6. Return: [{'ip': 'EC2_INSTANCE', 'network_risk': 0.95}]

**Risk Calculation:**
```python
# Isolation Forest returns -1 (anomaly) or 1 (normal)
# Convert to 0-1 scale:
if prediction == -1:
    risk = 0.9 + (0.1 * random)  # 0.9-1.0 for anomalies
else:
    risk = 0.0 + (0.3 * random)  # 0.0-0.3 for normal
```

---

## 3. UEBA Engine (ueba_engine.py)

### Purpose
Analyzes user behavior using AWS CloudTrail logs to detect behavioral anomalies.

### Key Components

#### Class: UEBAEngine
```python
class UEBAEngine:
    def __init__(self, model_path):
        # Load pre-trained Isolation Forest model
        # Initialize AWS S3 and CloudTrail clients
        # Set S3 bucket for CloudTrail logs
```

**Initialization:**
- Loads trained Isolation Forest model
- Creates boto3 S3 client for log access
- Sets CloudTrail bucket name
- Configures AWS account ID and region

#### Method: fetch_cloudtrail_logs()
```python
def fetch_cloudtrail_logs(self):
    # List CloudTrail log files in S3
    # Download and parse JSON logs
    # Extract events from last 10 minutes
    # Return list of events
```

**Log Fetching Process:**
1. Construct S3 prefix: AWSLogs/{account}/CloudTrail/{region}/{date}/
2. List objects in S3 bucket with prefix
3. Download .json.gz files
4. Decompress and parse JSON
5. Filter events from last 10 minutes
6. Return event list

**Example Event:**
```json
{
  "eventTime": "2026-02-28T10:00:00Z",
  "eventName": "DescribeInstances",
  "sourceIPAddress": "203.0.113.42",
  "userAgent": "aws-cli/2.0"
}
```


#### Method: extract_features()
```python
def extract_features(self, events):
    # Count total events
    # Count unique API calls
    # Count unique source IPs
    # Extract time patterns
    # Return feature vector
```

**Feature Extraction:**
```python
features = {
    'event_count': len(events),              # Total events
    'unique_apis': len(set(event names)),    # API diversity
    'unique_ips': len(set(source IPs)),      # IP diversity
    'hour_of_day': current_hour              # Time pattern
}
```

**Normal vs Anomalous:**
- Normal: 5-20 events, 2-5 unique APIs, 1-2 IPs
- Anomalous: 50+ events, 10+ unique APIs, 5+ IPs

#### Method: detect()
```python
def detect(self):
    # Fetch CloudTrail logs
    # Extract features
    # Run Isolation Forest prediction
    # Calculate risk score
    # Return results with IP and risk
```

**Detection Process:**
1. Fetch CloudTrail logs from S3
2. Extract behavioral features
3. Create feature vector
4. Feed to Isolation Forest
5. Calculate user risk score (0-1)
6. Return: [{'ip': 'EC2_INSTANCE', 'user_risk': 0.10}]

---

## 4. Threat Fusion Engine (threat_fusion_engine.py)

### Purpose
Combines network and user risk scores using 60/40 weighted fusion algorithm.

### Key Function

#### Function: combine_risks()
```python
def combine_risks(network_risk, user_risk):
    # Apply 60/40 weighted fusion
    # Calculate final risk score
    # Determine threat level
    # Return (final_risk, threat_level)
```

**Fusion Algorithm:**
```python
# Novel 60/40 weighted fusion
final_risk = (0.6 * network_risk) + (0.4 * user_risk)

# Determine threat level
if final_risk < 0.4:
    threat_level = "LOW"
elif 0.4 <= final_risk < 0.6:
    threat_level = "MEDIUM"
elif 0.6 <= final_risk < 0.8:
    threat_level = "HIGH"
else:
    threat_level = "CRITICAL"

return (final_risk, threat_level)
```

**Example Calculations:**

**Scenario 1: Normal Traffic**
```python
network_risk = 0.05
user_risk = 0.10
final = (0.6 * 0.05) + (0.4 * 0.10) = 0.07
level = "LOW"
```

**Scenario 2: DDoS Attack**
```python
network_risk = 0.95
user_risk = 0.10
final = (0.6 * 0.95) + (0.4 * 0.10) = 0.61
level = "HIGH"
```

**Scenario 3: Compromised Account**
```python
network_risk = 0.95
user_risk = 0.90
final = (0.6 * 0.95) + (0.4 * 0.90) = 0.93
level = "CRITICAL"
```

---

## 5. Autonomous Response Agent (autonomous_response_agent.py)

### Purpose
Automatically responds to threats based on risk severity with graduated actions.

### Key Components

#### Class: AutonomousResponseAgent
```python
class AutonomousResponseAgent:
    def __init__(self, security_group_id, region, 
                 block_timeout_minutes, monitoring_interval):
        # Initialize AWS EC2 client
        # Set Security Group ID for IP blocking
        # Configure timeouts and intervals
        # Initialize statistics tracking
```

**Initialization:**
- Creates boto3 EC2 client for Security Group management
- Sets Security Group ID (sg-096157899840a1547)
- Configures block timeout (10 minutes default)
- Initializes blacklist and statistics dictionaries

#### Method: assess_threat_level()
```python
def assess_threat_level(self, risk_score):
    # Map risk score to threat level
    # Returns: LOW, MEDIUM, HIGH, or CRITICAL
```

**Threat Level Mapping:**
```python
if risk_score < 0.4:
    return "LOW"
elif 0.4 <= risk_score < 0.6:
    return "MEDIUM"
elif 0.6 <= risk_score < 0.8:
    return "HIGH"
else:
    return "CRITICAL"
```

#### Method: log_threat()
```python
def log_threat(self, ip, risk, network_risk, user_risk):
    # Log threat information to file
    # Update statistics
    # No action taken (just logging)
```

**What it does:**
- Writes to logs/autonomous_response.log
- Records IP, risk scores, timestamp
- Increments LOG action counter
- Used for LOW threats (risk < 0.4)

#### Method: send_alert()
```python
def send_alert(self, ip, risk, network_risk, user_risk, level):
    # Create alert message
    # Send to console
    # Send email (if configured)
    # Log to JSON file
```

**Alert Process:**
1. Format alert message with all details
2. Print to console with formatting
3. Call email alert system (if configured)
4. Write to logs/threat_alerts.json
5. Update statistics

**Alert Format:**
```
======================================================================
    SECURITY ALERT - HIGH
======================================================================
Time: 2026-02-28 10:05:32
IP Address: EC2_INSTANCE
Risk Score: 0.61
Network Risk: 0.95
User Risk: 0.10
Action: Alert notification sent
======================================================================
```

#### Method: simulate_rate_limiting()
```python
def simulate_rate_limiting(self, ip, risk):
    # Display rate limiting message
    # Log action
    # Update statistics
    # Note: Actual rate limiting would require
    #       AWS WAF or Application Load Balancer
```

**Rate Limiting:**
- Displays rate limit activation message
- Logs to file
- In production, would integrate with AWS WAF
- Limits traffic to 10 requests/minute
- Duration: 5 minutes

#### Method: block_ip_address()
```python
def block_ip_address(self, ip, risk, network_risk, user_risk):
    # Check if already blocked
    # Add deny rule to Security Group
    # Update blacklist
    # Log action
    # Return success/failure
```

**Blocking Process:**
1. Check if IP already in blacklist
2. Call EC2 authorize_security_group_ingress API
3. Add deny rule: Protocol=ALL, Port=ALL, Source=IP/32
4. Record in blacklist with timestamp
5. Log action
6. Update statistics

**API Call:**
```python
self.ec2.authorize_security_group_ingress(
    GroupId=self.security_group_id,
    IpPermissions=[{
        'IpProtocol': '-1',      # All protocols
        'FromPort': -1,          # All ports
        'ToPort': -1,
        'IpRanges': [{'CidrIp': f'{ip}/32'}]
    }]
)
```

#### Method: unblock_ip_address()
```python
def unblock_ip_address(self, ip):
    # Remove deny rule from Security Group
    # Remove from blacklist
    # Log action
    # Update statistics
```

**Unblocking Process:**
1. Call EC2 revoke_security_group_ingress API
2. Remove deny rule for IP
3. Delete from blacklist
4. Log action
5. Increment unblock counter

#### Method: check_and_unblock_expired()
```python
def check_and_unblock_expired(self):
    # Check all blocked IPs
    # Calculate time since blocking
    # Unblock if timeout exceeded
    # Called every detection cycle
```

**Auto-Unblock Logic:**
```python
for ip, block_info in blacklist.items():
    time_blocked = now - block_info.blocked_at
    if time_blocked > timeout:
        unblock_ip_address(ip)
```

#### Method: take_action()
```python
def take_action(self, ip, risk, network_risk, user_risk):
    # Assess threat level
    # Determine appropriate action
    # Execute action
    # Return action taken
```

**Decision Logic:**
```python
if risk < 0.4:
    log_threat()
    return "LOG"
elif 0.4 <= risk < 0.6:
    send_alert()
    return "ALERT"
elif 0.6 <= risk < 0.8:
    simulate_rate_limiting()
    send_alert()
    return "RATE_LIMIT"
else:  # risk >= 0.8
    block_ip_address()
    send_alert()
    return "BLOCK"
```

---

## 6. Alert System (alert_system.py)

### Purpose
Provides multi-channel alerting (console, email, JSON logs).

### Key Components

#### Class: AlertSystem
```python
class AlertSystem:
    def __init__(self):
        # Load email configuration
        # Initialize SMTP settings
        # Set up alert statistics
```

**Configuration:**
- Reads config/alert_config.json
- Extracts SMTP settings (server, port, credentials)
- Initializes alert counters

#### Method: create_alert()
```python
def create_alert(self, threat_level, final_risk, 
                 network_risk, user_risk, 
                 network_bytes, network_packets):
    # Format alert message
    # Send to console
    # Send email (if HIGH or CRITICAL)
    # Log to JSON file
```

**Alert Creation:**
1. Format message with all threat details
2. Print to console with color coding
3. If HIGH or CRITICAL, send email
4. Write to logs/threat_alerts.json
5. Update statistics

#### Method: send_email_alert()
```python
def send_email_alert(self, subject, body):
    # Connect to SMTP server
    # Authenticate
    # Send email
    # Handle errors gracefully
```

**Email Process:**
```python
# Connect to Gmail SMTP
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login(email, app_password)

# Create message
msg = MIMEText(body)
msg['Subject'] = subject
msg['From'] = email
msg['To'] = email

# Send
server.send_message(msg)
server.quit()
```

---

## 7. Main System (enhanced_main_with_agent.py)

### Purpose
Integrates all components into complete detection and response system.

### Key Components

#### Class: EnhancedThreatDetectionSystemWithAgent
```python
class EnhancedThreatDetectionSystemWithAgent:
    def __init__(self, security_group_id, enable_autonomous_response):
        # Initialize IDS engine
        # Initialize UEBA engine
        # Initialize alert system
        # Initialize autonomous response agent
        # Set up statistics tracking
```

**System Initialization:**
1. Load IDS model (models/ddos_model.pkl)
2. Load UEBA model (models/uba_model.pkl)
3. Create alert system instance
4. Create autonomous response agent
5. Initialize statistics dictionary

#### Method: run_detection_cycle()
```python
def run_detection_cycle(self):
    # Run IDS detection
    # Run UEBA detection
    # Combine risks (60/40 fusion)
    # Create alerts if needed
    # Execute autonomous response
    # Check for expired blocks
```

**Detection Cycle:**
```python
# Step 1: Network detection
network_results = self.ids.detect()
# Returns: [{'ip': 'EC2_INSTANCE', 'network_risk': 0.95}]

# Step 2: User behavior detection
user_results = self.ueba.detect()
# Returns: [{'ip': 'EC2_INSTANCE', 'user_risk': 0.10}]

# Step 3: Match by IP
for net in network_results:
    ip = net["ip"]
    network_risk = net["network_risk"]
    
    matched_user = find_matching_user(ip, user_results)
    user_risk = matched_user["user_risk"] if matched_user else 0.1
    
    # Step 4: Fusion
    final_risk, level = combine_risks(network_risk, user_risk)
    
    # Step 5: Alert if needed
    if final_risk > 0.3:
        self.alert_system.create_alert(...)
    
    # Step 6: Autonomous response
    if self.enable_autonomous_response:
        action = self.response_agent.take_action(
            ip, final_risk, network_risk, user_risk
        )
    
    # Step 7: Check expired blocks
    self.response_agent.check_and_unblock_expired()
```

#### Method: run()
```python
def run(self):
    # Main loop
    # Run detection cycles every 60 seconds
    # Handle Ctrl+C gracefully
    # Show statistics on exit
```

**Main Loop:**
```python
try:
    while True:
        run_detection_cycle()
        time.sleep(60)  # Wait 60 seconds
except KeyboardInterrupt:
    show_statistics()
    agent.display_statistics()
```

---

## 8. Attack Simulator (tests/attack_simulator.py)

### Purpose
Simulates DDoS attack for testing and demonstration.

### Key Components

#### Function: send_requests()
```python
def send_requests(target_url, duration):
    # Send HTTP requests continuously
    # Run for specified duration
    # Used by each thread
```

**Request Loop:**
```python
end_time = time.time() + duration
while time.time() < end_time:
    try:
        requests.get(target_url, timeout=5)
    except:
        pass  # Ignore errors, keep attacking
```

#### Main Execution
```python
# Configuration
THREADS = 300
DURATION = 60  # seconds
TARGET = EC2_INSTANCE_URL

# Launch threads
for i in range(THREADS):
    thread = threading.Thread(
        target=send_requests,
        args=(TARGET, DURATION)
    )
    thread.start()

# Wait for completion
for thread in threads:
    thread.join()
```

**Attack Characteristics:**
- 300 concurrent threads
- Each sends continuous HTTP GET requests
- Duration: 60 seconds
- Generates 1000x-4000x normal traffic
- Simulates volumetric DDoS attack

---

## Code Flow Summary

### Complete Detection Flow

```
1. System Start
   ↓
2. Initialize Components (IDS, UEBA, Agent, Alerts)
   ↓
3. Start Detection Loop (every 60s)
   ↓
4. Fetch CloudWatch Metrics → IDS Engine
   ↓
5. Calculate Network Risk (Isolation Forest)
   ↓
6. Fetch CloudTrail Logs → UEBA Engine
   ↓
7. Calculate User Risk (Isolation Forest)
   ↓
8. Combine Risks (60/40 Fusion)
   ↓
9. Determine Threat Level (LOW/MEDIUM/HIGH/CRITICAL)
   ↓
10. Create Alert (if risk > 0.3)
    ↓
11. Autonomous Response Decision
    ├─ Risk < 0.4 → LOG
    ├─ 0.4-0.6 → ALERT
    ├─ 0.6-0.8 → RATE_LIMIT
    └─ ≥ 0.8 → BLOCK IP
    ↓
12. Check Expired Blocks (auto-unblock after 10 min)
    ↓
13. Update Statistics
    ↓
14. Sleep 60 seconds
    ↓
15. Repeat from Step 3
```

---

## Key Design Patterns

### 1. Separation of Concerns
- Each component has single responsibility
- IDS: Network only
- UEBA: User behavior only
- Fusion: Risk correlation only
- Agent: Response only

### 2. Error Handling
```python
try:
    # AWS API call
except ClientError as e:
    logger.error(f"AWS error: {e}")
    # Use default values, don't crash
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    # Continue operation
```

### 3. Configuration Management
- External config files (alert_config.json)
- Environment-based settings
- No hardcoded credentials

### 4. Logging
- Structured logging with timestamps
- Multiple log levels (INFO, WARNING, ERROR)
- Separate log files for different components

### 5. Statistics Tracking
- Real-time counters
- Historical data
- Performance metrics

---

## Performance Optimizations

### 1. Efficient API Calls
- Batch CloudWatch metric requests
- Cache CloudTrail logs
- Minimize S3 list operations

### 2. Fast ML Inference
- Pre-loaded models (no loading per cycle)
- Isolation Forest: < 10ms inference
- Minimal feature engineering

### 3. Asynchronous Operations
- Non-blocking AWS API calls
- Parallel IDS and UEBA detection possible
- Background thread for expired block checks

### 4. Memory Management
- Limited blacklist size
- Periodic log rotation
- Efficient data structures

---

**Author:** Aarit Haldar  
**Date:** February 2026  
**Institution:** Engineering College  
**USN:** ENG24CY0073
