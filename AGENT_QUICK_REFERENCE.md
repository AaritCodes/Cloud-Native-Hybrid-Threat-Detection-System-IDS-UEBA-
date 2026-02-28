# Autonomous Response Agent - Quick Reference

## Quick Start (60 seconds)

### 1. Get your Security Group ID
```bash
aws ec2 describe-security-groups --region ap-south-1 --query 'SecurityGroups[0].GroupId'
```

### 2. Update configuration
Edit `src/enhanced_main_with_agent.py` (around line 235):
```python
SECURITY_GROUP_ID = "sg-YOUR_ID_HERE"
ENABLE_AUTONOMOUS_RESPONSE = True
```

### 3. Start the system
```bash
python run.py
```

---

## What Does It Do?

The Autonomous Response Agent **automatically protects your infrastructure** by:

| Risk Level | What Happens | Example |
|-----------|------------|---------|
| 📊 0.0-0.4 | Nothing (just log) | Normal traffic |
| 🟡 0.4-0.6 | Alert security team | Suspicious activity |
| 🟠 0.6-0.8 | Slow down traffic | Likely attack starting |
| 🔴 0.8-1.0 | **BLOCK IP for 10 min** | Clear attack detected |

---

## Real-World Example

### Scenario: DDoS Attack Detected

**Time 14:23:45**
```
🚨 NETWORK SPIKE DETECTED
   - 50M bytes/sec (normal: 100K)
   - 8M packets/sec (normal: 100K)
   
📊 UEBA ANALYSIS
   - Unusual traffic pattern
   - Unknown IP: 203.0.113.42
   
🔄 FUSION ENGINE
   Risk Score: 0.92 (CRITICAL)
   
🤖 AUTONOMOUS AGENT
   ➤ Action: BLOCK IP
   ➤ Duration: 10 minutes
   ➤ Security Group Rule Added
   ➤ Alert Sent to Team
```

**Time 14:33:45** (10 minutes later)
```
⏰ BLOCK TIMEOUT REACHED
   ➤ IP 203.0.113.42 Auto-Unblocked
   ➤ Security Group Rule Removed
   ➤ Traffic Available Again
```

---

## Architecture Diagram

```
┌─────────────┐
│   AWS EC2   │
│  Instance   │
└──────┬──────┘
       │
       ├─ CloudWatch Metrics ──→ IDS Engine (Network Risk)
       │  (NetworkIn, NetworkPacketsIn)
       │
       └─ CloudTrail Logs      └─ UEBA Engine (User Risk)
          (IAM Events)

         ↓         ↓
    ┌────────────────────┐
    │  Threat Fusion     │
    │  (0.6*Net + 0.4*User)
    └─────────┬──────────┘
              ↓
    ┌─────────────────────────────────────┐
    │ Autonomous Response Agent           │
    │ • Monitors Risk Every 60 Seconds   │
    │ • Makes Decisions                  │
    │ • Executes Actions                 │
    └────────┬────────────────────────────┘
             │
    ┌────────▼─────────────────────┐
    │  Action Decision Tree         │
    │                               │
    │  Risk < 0.4  → 🟢 LOG        │
    │  0.4 ≤ Risk < 0.6 → 🟡 ALERT │
    │  0.6 ≤ Risk < 0.8 → 🟠 LIMIT  │
    │  Risk ≥ 0.8  → 🔴 BLOCK      │
    └────────┬─────────────────────┘
             │
    ┌────────▼────────────────────────┐
    │  AWS Security Group              │
    │  • Add Deny Rules                │
    │  • Remove Rules After Timeout    │
    │  • Track Blocked IPs             │
    └─────────────────────────────────┘
```

---

## Key Features

### ✅ Automatic IP Blocking
- Risk ≥ 0.8 → Instantly blocks IP in Security Group
- No manual intervention needed
- Works 24/7

### ✅ Auto-Unblock Policy (10 minutes)
- Removes block automatically after timeout
- Prevents permanent blacklists
- Configurable duration

### ✅ Duplicate Prevention
- Prevents blocking same IP twice
- Avoids AWS API errors
- Efficient resource usage

### ✅ Production-Grade Logging
- Every action logged with timestamp
- JSON format for easy parsing
- Audit trail for compliance

### ✅ IAM Role Support
- No hardcoded credentials
- Secure credential management
- Works with EC2 IAM roles

### ✅ Comprehensive Statistics
- Track total blocks/unblocks
- Monitor currently blocked IPs
- Measure system uptime

---

## Common Commands

```bash
# Start the system
python run.py

# Check AWS credentials
aws sts get-caller-identity

# List your security groups
aws ec2 describe-security-groups --region ap-south-1

# View logs
tail -f logs/autonomous_response.log

# View threat alerts
cat logs/threat_alerts.json | json_pp

# Stop the system
# Press Ctrl+C in terminal
```

---

## Troubleshooting

### ❌ "Failed to initialize AWS client"
```bash
# Fix: Configure AWS credentials
aws configure
# Then enter: Access Key, Secret Key, Region (ap-south-1), Output format (json)
```

### ❌ "No such file or directory: logs/autonomous_response.log"
```bash
# Fix: Create logs directory
mkdir -p logs
```

### ❌ "InvalidParameterValue: Invalid id: sg-xxxxx"
```bash
# Fix: Use correct Security Group ID
aws ec2 describe-security-groups --region ap-south-1
# Copy the GroupId and update your configuration
```

### ❌ "User is not authorized to perform: ec2:AuthorizeSecurityGroupIngress"
```bash
# Fix: Check IAM permissions
# Ensure your IAM role/user has EC2 security group modify permissions
```

---

## Statistics & Monitoring

```
📊 AUTONOMOUS RESPONSE AGENT STATISTICS
===============================================
⏰ Uptime: 1234 minutes
🚫 Total Blocks: 42
✅ Total Unblocks: 38
🚨 Total Alerts: 89
⚡ Total Rate Limits: 12
🔒 Currently Blocked: 4 IPs
📋 Blocked IPs: 203.0.113.42, 192.0.2.15, ...
===============================================
```

---

## Response Actions Explained

### 🟢 LOG (Risk < 0.4)
- **When**: Normal activity or low threat
- **Action**: Write to log file only
- **Example**: Background traffic, scheduled jobs

### 🟡 ALERT (0.4 ≤ Risk < 0.6)  
- **When**: Suspicious activity detected
- **Action**: Send alert to security team
- **Example**: Unusual login patterns, spike in API calls

### 🟠 RATE_LIMIT (0.6 ≤ Risk < 0.8)
- **When**: Likely attack in progress
- **Action**: Slow down traffic, trigger alert
- **Example**: Sustained high traffic from one IP

### 🔴 BLOCK (Risk ≥ 0.8)
- **When**: Clear attack detected
- **Action**: Block IP immediately for 10 minutes
- **Example**: DDoS attack, rapid connection attempts

---

## Response Time

```
Detection → Decision → Action
   ↓          ↓          ↓
  <1s       <1s       <1s
                       
Total: Typically < 3 seconds from detection to blocking
```

---

## What's Protected

This system protects:
- ✅ EC2 Instances (via Security Groups)
- ✅ ALB/NLB (via Security Groups)
- ✅ RDS Databases (via Security Groups)
- ✅ Any AWS resource using Security Groups

---

## Risk Score Formula

```
Final Risk Score = (0.6 × Network Risk) + (0.4 × User Risk)

Where:
  Network Risk = Traffic anomaly detection
  User Risk = Behavioral anomaly detection
  
Range: 0.0 to 1.0
```

---

## Example Response Flows

### Normal Day
```
14:00 Risk=0.15 → 🟢 LOG
14:01 Risk=0.18 → 🟢 LOG
14:02 Risk=0.12 → 🟢 LOG
... (no actions taken)
```

### Suspicious Activity
```
14:00 Risk=0.45 → 🟡 ALERT (Alert sent)
14:01 Risk=0.48 → 🟡 ALERT (Already alerted)
14:02 Risk=0.50 → 🟡 ALERT (Continues)
14:03 Risk=0.35 → 🟢 LOG (Threat passed)
```

### Active Attack
```
14:00 Risk=0.72 → 🟠 RATE_LIMIT + 🟡 ALERT
14:01 Risk=0.85 → 🔴 BLOCK (IP: 203.0.113.42)
14:02 Risk=0.88 → (Already blocked)
14:12 Risk=N/A  → ✅ AUTO-UNBLOCK (10 min timeout)
14:13 Risk=0.15 → 🟢 LOG (Back to normal)
```

---

## Best Practices

1. **Review Logs Weekly**
   - Check for false positives
   - Monitor blocked IP patterns

2. **Adjust Thresholds Gradually**
   - Start with default thresholds
   - Fine-tune based on traffic patterns

3. **Test in Development First**
   - Verify blocking mechanism works
   - Test auto-unblock after 10 minutes

4. **Monitor System Health**
   - Check EC2 <→ AWS API connectivity
   - Verify IAM permissions

5. **Keep Logs Backed Up**
   - Export logs to S3 regularly
   - Archive for compliance

---

## Support

For issues or questions:
1. Check logs: `tail -f logs/autonomous_response.log`
2. Verify AWS credentials: `aws sts get-caller-identity`
3. Verify Security Group: `aws ec2 describe-security-groups --group-ids sg-xxxxx`
4. Test with manual threat: Run test scenario

---

**Last Updated**: February 28, 2026
**Status**: ✅ Production Ready
