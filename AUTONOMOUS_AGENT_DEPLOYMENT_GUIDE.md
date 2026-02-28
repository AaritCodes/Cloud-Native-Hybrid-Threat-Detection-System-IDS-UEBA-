# Autonomous Response Agent - Deployment & Integration Guide

## Overview

Your Hybrid Threat Detection System now includes a fully functional **Autonomous Response Agent** that automatically responds to security threats based on risk severity levels. This guide explains the system architecture, deployment steps, and operational procedures.

---

## System Architecture

### 1. **Detection Layer** (Input)
- **IDS Engine**: Detects volumetric DDoS anomalies using AWS CloudWatch
- **UEBA Engine**: Detects behavioral anomalies using AWS CloudTrail
- **Threat Fusion**: Combines network + user risk → Final Risk Score (0-1)

### 2. **Response Layer** (Action)
- **Autonomous Response Agent**: Monitors risk score & takes automated actions
  - Continuously runs every 60 seconds
  - Makes decisions based on risk thresholds
  - Automatically blocks IPs via AWS Security Groups
  - Maintains blacklist and auto-unblock policy

### 3. **Alert Layer** (Notification)
- **Alert System**: Multi-channel notifications (console, email, JSON logs)

---

## Risk-Based Response Levels

| Risk Score | Threat Level | Action | Details |
|-----------|-------------|--------|---------|
| **< 0.4** | **LOW** | 🟢 Log | Log only - no action taken |
| **0.4 - 0.6** | **MEDIUM** | 🟡 Alert | Send alerts to security team |
| **0.6 - 0.8** | **HIGH** | 🟠 Rate Limit | Apply traffic rate limiting |
| **≥ 0.8** | **CRITICAL** | 🔴 Block | Automatically block attacker IP |

---

## Prerequisites

### AWS Configuration

1. **Security Group Setup**
   ```bash
   # Get your Security Group ID
   aws ec2 describe-security-groups --region ap-south-1 --query 'SecurityGroups[0].GroupId'
   ```

2. **IAM Permissions Required**
   ```json
   {
       "Version": "2012-10-17",
       "Statement": [
           {
               "Effect": "Allow",
               "Action": [
                   "ec2:AuthorizeSecurityGroupIngress",
                   "ec2:RevokeSecurityGroupIngress",
                   "ec2:DescribeSecurityGroups"
               ],
               "Resource": "arn:aws:ec2:*:*:security-group/*"
           },
           {
               "Effect": "Allow",
               "Action": [
                   "cloudwatch:GetMetricStatistics",
                   "ec2:DescribeInstances"
               ],
               "Resource": "*"
           }
       ]
   }
   ```

3. **AWS Credentials Configuration**
   - Use **IAM Role** (recommended for EC2)
   - Or configure `~/.aws/credentials`
   - Or set environment variables:
     ```bash
     export AWS_ACCESS_KEY_ID=your_key
     export AWS_SECRET_ACCESS_KEY=your_secret
     export AWS_DEFAULT_REGION=ap-south-1
     ```

### Python Dependencies

All required packages are in `requirements.txt`:
```bash
pip install -r requirements.txt
```

Key packages:
- `boto3` - AWS SDK
- `pandas` - Data processing
- `joblib` - ML model loading
- `scikit-learn` - ML algorithms

---

## Getting Started

### Step 1: Configure Your Security Group ID

Edit [enhanced_main_with_agent.py](src/enhanced_main_with_agent.py):

```python
# Line ~235 - Replace with your actual Security Group ID
SECURITY_GROUP_ID = "sg-0123456789abcdef0"  # Your SG ID here

# Enable/disable autonomous response
ENABLE_AUTONOMOUS_RESPONSE = True  # Set to False for monitoring only
```

### Step 2: Start the System

```bash
# Default mode (with autonomous response enabled)
python run.py

# Or run directly with full control
python src/enhanced_main_with_agent.py
```

### Step 3: Monitor the Agent

The system will output:

```
=======================================================
🛡️  Hybrid Threat Detection System with Autonomous Response
=======================================================
🔒 Security Group: sg-0123456789abcdef0
🤖 Autonomous Response: ENABLED
=======================================================

🚀 Initializing Enhanced Hybrid Threat Detection System with Autonomous Response...
✅ IDS Engine initialized
✅ UEBA Engine initialized
✅ Alert System initialized
✅ Autonomous Response Agent enabled
✅ System initialized successfully!

===== Hybrid Threat Detection Cycle =====
Running IDS...
Running UEBA...
... (detection results and autonomous actions)
```

---

## Core Components

### 1. AutonomousResponseAgent Class

**Location**: [src/autonomous_response_agent.py](src/autonomous_response_agent.py)

**Key Methods**:

```python
# Initialize agent
agent = AutonomousResponseAgent(
    security_group_id="sg-xxxxx",
    region="ap-south-1",
    block_timeout_minutes=10,
    monitoring_interval=60
)

# Take action on threat
action = agent.take_action(
    ip_address="192.168.1.100",
    risk_score=0.85,
    network_risk=0.9,
    user_risk=0.75
)
# Returns: "LOG", "ALERT", "RATE_LIMIT", or "BLOCK"

# Check for expired blocks (auto-unblock)
agent.check_and_unblock_expired()

# Get statistics
stats = agent.get_statistics()
agent.display_statistics()
```

**Features**:
- ✅ Automatic IP blocking via AWS Security Groups
- ✅ Timeout-based auto-unblocking (default: 10 minutes)
- ✅ In-memory blacklist to prevent duplicate blocks
- ✅ Comprehensive logging to `logs/autonomous_response.log`
- ✅ Exception handling for AWS API failures
- ✅ Operational statistics tracking

### 2. Integration with Detection Engines

**Flow**:
```
IDS Engine (Network Risk)  ──────┐
                                  ├──> Threat Fusion ──> Final Risk
UEBA Engine (User Risk)    ──────┤
                                  └──> Autonomous Agent (Decision + Action)
```

**Example Code**:
```python
from src.autonomous_response_agent import AutonomousResponseAgent
from src.ids_engine import IDSEngine
from src.ueba_engine import UEBAEngine
from src.threat_fusion_engine import combine_risks

# Initialize
agent = AutonomousResponseAgent(security_group_id="sg-xxxxx")
ids = IDSEngine("models/ddos_model.pkl")
ueba = UEBAEngine("models/uba_model.pkl")

# Get risks
network_results = ids.detect()  # [{"ip": "X.X.X.X", "network_risk": 0.85}]
user_results = ueba.detect()    # [{"ip": "X.X.X.X", "user_risk": 0.75}]

# Combine and respond
for net in network_results:
    ip = net["ip"]
    network_risk = net["network_risk"]
    user_risk = next(u["user_risk"] for u in user_results if u["ip"] == ip)
    
    final_risk, level = combine_risks(network_risk, user_risk)
    agent.take_action(ip, final_risk, network_risk, user_risk)
```

### 3. Blocking Mechanism

**How IP Blocking Works**:

1. **Block (Risk ≥ 0.8)**:
   - Adds inbound DENY rule to Security Group
   - Blocks all protocols from attacking IP
   - Tracks in in-memory blacklist

2. **Auto-Unblock (After 10 minutes)**:
   - Removes DENY rule from Security Group
   - Clears from blacklist
   - Logged for audit trail

3. **Duplicate Prevention**:
   - Checks blacklist before blocking
   - Skips if already blocked
   - Prevents AWS API errors

---

## Monitoring & Logging

### Log Files

1. **Autonomous Response Log**
   - File: `logs/autonomous_response.log`
   - Contains all agent actions with timestamps
   - Includes IP blocks, unblocks, alerts, rate limits

2. **Threat Alerts Log**
   - File: `logs/threat_alerts.json`
   - JSON format for easy parsing
   - Used by dashboard for visualization

### Log Examples

```
2026-02-28 14:23:45 - autonomous_response_agent - INFO - ✅ IP BLOCKED | IP: 192.168.1.105 | Risk: 0.92 | Network: 0.95 | User: 0.85 | Security Group: sg-xxxxx

2026-02-28 14:23:47 - autonomous_response_agent - WARNING - ⚠️  CRITICAL ALERT | IP: 192.168.1.105 | Risk: 0.92 | Action: Alert sent to security team

2026-02-28 14:33:45 - autonomous_response_agent - INFO - ✅ IP UNBLOCKED | IP: 192.168.1.105 | Blocked duration: 10 minutes
```

### Statistics Tracking

The agent tracks:
- Total IP blocks
- Total IP unblocks
- Total alerts sent
- Total rate limits applied
- Currently blocked IPs
- System uptime

---

## Configuration Options

### Adjusting Block Timeout

Edit [enhanced_main_with_agent.py](src/enhanced_main_with_agent.py):

```python
self.response_agent = AutonomousResponseAgent(
    security_group_id=security_group_id,
    region="ap-south-1",
    block_timeout_minutes=15,  # Change from 10 to 15 minutes
    monitoring_interval=60
)
```

### Adjusting Monitoring Interval

```python
# More frequent monitoring (30 seconds)
monitoring_interval=30

# Less frequent monitoring (120 seconds / 2 minutes)
monitoring_interval=120
```

### Adjusting Risk Thresholds

Edit [src/threat_fusion_engine.py](src/threat_fusion_engine.py):

```python
def combine_risks(network_risk, user_risk):
    # Adjust weights (currently 60% network, 40% user)
    final_risk = (0.7 * network_risk) + (0.3 * user_risk)  # 70/30 split
    # ... rest of function
```

---

## Production Deployment Checklist

- [ ] **Security Group Setup**
  - [ ] Create dedicated security group for threat response
  - [ ] Set inbound rule restrictions
  - [ ] Document security group ID

- [ ] **AWS IAM Configuration**
  - [ ] Create IAM role with required permissions
  - [ ] Attach role to EC2 instance (if using role)
  - [ ] Test EC2 → Security Group API access

- [ ] **Credentials Configuration**
  - [ ] Verify AWS credentials work (`aws ec2 describe-instances`)
  - [ ] Set proper AWS region in code
  - [ ] Test boto3 client initialization

- [ ] **System Configuration**
  - [ ] Update Security Group ID in main file
  - [ ] Adjust block timeout if needed
  - [ ] Adjust monitoring interval if needed
  - [ ] Set ENABLE_AUTONOMOUS_RESPONSE = True

- [ ] **Logging Setup**
  - [ ] Ensure `logs/` directory exists
  - [ ] Verify log file permissions
  - [ ] Configure log rotation (optional)

- [ ] **Testing**
  - [ ] Test with LOW threat (risk < 0.4)
  - [ ] Test with MEDIUM threat (0.4 ≤ risk < 0.6)
  - [ ] Test with HIGH threat (0.6 ≤ risk < 0.8)
  - [ ] Test with CRITICAL threat (risk ≥ 0.8)
  - [ ] Verify auto-unblock after timeout

- [ ] **Monitoring**
  - [ ] Set up log aggregation
  - [ ] Configure alerting on agent errors
  - [ ] Monitor blocked IP list
  - [ ] Track false positives

- [ ] **Documentation**
  - [ ] Document your Security Group ID
  - [ ] Document response procedures
  - [ ] Document escalation contacts
  - [ ] Document incident investigation process

---

## Troubleshooting

### Issue: "Failed to initialize AWS client"

**Cause**: AWS credentials not configured

**Solution**:
```bash
# Check credentials
aws sts get-caller-identity

# Configure credentials
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### Issue: "Failed to block IP: InvalidParameterValue"

**Cause**: Invalid Security Group ID or IP format

**Solution**:
```bash
# Verify Security Group exists
aws ec2 describe-security-groups --group-ids sg-xxxxx --region ap-south-1

# Use correct CIDR format (IP/32 for single host)
```

### Issue: "Rule already exists" warning

**Behavior**: Expected if IP is already blocked

**Action**: None required - agent skips duplicate

### Issue: Agent not taking actions

**Check**:
1. ENABLE_AUTONOMOUS_RESPONSE = True in config
2. Risk scores are actually high enough (≥ 0.4 for any action)
3. AWS credentials are valid
4. Security Group ID is correct
5. IAM permissions include EC2 security group modifications

---

## Advanced Usage

### Running in Monitoring-Only Mode

Disable autonomous response (observation mode):

```python
# In enhanced_main_with_agent.py
ENABLE_AUTONOMOUS_RESPONSE = False  # Disables auto-blocking
```

### Custom Integration

```python
from src.autonomous_response_agent import AutonomousResponseAgent

# Initialize agent
agent = AutonomousResponseAgent(
    security_group_id="sg-xxxxx",
    region="ap-south-1",
    block_timeout_minutes=10,
    monitoring_interval=60
)

# Take custom action
action = agent.take_action(
    ip_address="203.0.113.42",
    risk_score=0.92,
    network_risk=0.95,
    user_risk=0.85
)

print(f"Action taken: {action}")

# Get statistics
stats = agent.get_statistics()
print(f"Currently blocked IPs: {stats['currently_blocked']}")

# Manual unblock if needed
agent.unblock_ip_address("203.0.113.42")
```

### Extending for Additional Actions

Example: Integrate with AWS WAF or SNS notifications:

```python
def send_sns_notification(self, message):
    """Send SNS notification for critical threats"""
    sns = boto3.client('sns')
    sns.publish(
        TopicArn='arn:aws:sns:region:account:topic-name',
        Message=message,
        Subject='Critical Threat Detected'
    )

# In CRITICAL action block
if risk_score >= 0.8:
    self.send_sns_notification(f"Critical threat from {ip_address}")
```

---

## Performance Considerations

- **Monitoring Interval**: 60 seconds (configurable)
- **Block Timeout**: 10 minutes (configurable)
- **In-Memory Blacklist**: Stores blocked IPs (clears on agent restart)
- **Log File Size**: Grows ~50KB per 1000 actions (consider rotation)

---

## Security Best Practices

1. **Least Privilege**: Use minimal IAM permissions
2. **Audit Trail**: Monitor `autonomous_response.log` for suspicious patterns
3. **Rate Limiting**: Prevent log spam from DoS attacks
4. **Backup**: Regularly backup Security Group rules
5. **Testing**: Test thoroughly in non-production first
6. **Monitoring**: Alert on unexpected agent behavior
7. **Credentials**: Never hardcode AWS keys (use IAM roles)
8. **Network Segmentation**: Use separate security groups for different purposes

---

## Support & Debugging

For detailed debugging, enable more verbose logging:

```python
# In autonomous_response_agent.py
logging.basicConfig(
    level=logging.DEBUG,  # Changed from INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/autonomous_response.log'),
        logging.StreamHandler()
    ]
)
```

---

## Next Steps

1. ✅ Configure your Security Group ID
2. ✅ Set up AWS IAM credentials
3. ✅ Test in development environment
4. ✅ Review and customize block timeout/interval
5. ✅ Deploy to production
6. ✅ Monitor logs and statistics
7. ✅ Adjust thresholds based on false positive rate

---

**Last Updated**: February 28, 2026
**Version**: 2.0 - Production Ready
