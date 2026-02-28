# Autonomous Response Agent - Operations Runbook

## Emergency Procedures

### 🚨 Immediate Issues

#### Agent Not Starting

```bash
# Check 1: Verify Python environment
python --version  # Should be 3.8+

# Check 2: Verify dependencies
pip list | grep boto3

# Check 3: Check logs directory
ls -la logs/

# Check 4: Run test suite
python test_autonomous_agent.py
```

#### Agent Not Blocking IPs

```bash
# Check 1: Verify Security Group exists
aws ec2 describe-security-groups --group-ids sg-xxxxx --region ap-south-1

# Check 2: Verify IAM permissions
aws ec2 describe-instances --region ap-south-1  # Should work

# Check 3: Check log for errors
grep "ERROR" logs/autonomous_response.log | tail -20

# Check 4: Verify agent is enabled
grep "ENABLE_AUTONOMOUS_RESPONSE = True" src/enhanced_main_with_agent.py
```

#### AWS Credentials Not Working

```bash
# Option 1: Configure AWS CLI
aws configure
# Enter: Access Key ID, Secret Access Key, Region (ap-south-1), Output (json)

# Option 2: Use IAM Role (if on EC2)
aws sts get-caller-identity  # Should show your account

# Option 3: Set environment variables
export AWS_ACCESS_KEY_ID="your-key"
export AWS_SECRET_ACCESS_KEY="your-secret"
export AWS_DEFAULT_REGION="ap-south-1"
```

---

## Daily Operations

### Morning Checklist

- [ ] Start the system: `python run.py`
- [ ] Monitor initial log output
- [ ] Check for any unblocked IPs from overnight
- [ ] Verify Security Group rules are clean

### Throughout Day

- [ ] Monitor for false positives in alerts
- [ ] Track blocked IPs and patterns
- [ ] Check agent statistics every 2 hours
- [ ] Review unusual threat patterns

### End of Day

- [ ] Export logs for archival
- [ ] Review day's threat statistics
- [ ] Check for any unresolved blocks
- [ ] Plan for next day adjustments

---

## Common Operations

### Manually Block an IP (Emergency)

```bash
# If agent isn't responding fast enough:
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol all \
  --cidr 203.0.113.42/32 \
  --region ap-south-1
```

### Manually Unblock an IP

```bash
# If you need to unblock immediately:
aws ec2 revoke-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol all \
  --cidr 203.0.113.42/32 \
  --region ap-south-1
```

### View Currently Blocked IPs

```bash
# Option 1: From agent statistics
python -c "
from src.autonomous_response_agent import AutonomousResponseAgent
agent = AutonomousResponseAgent('sg-xxxxx')
print(agent.get_statistics()['blocked_ips'])
"

# Option 2: From AWS Security Group
aws ec2 describe-security-group-rules \
  --filters Name=group-id,Values=sg-xxxxx \
  --region ap-south-1 | grep CIDR
```

### View Recent Actions

```bash
# Last 50 agent actions
tail -50 logs/autonomous_response.log

# Last 20 blocks
grep "BLOCKED" logs/autonomous_response.log | tail -20

# Last 20 unblocks
grep "UNBLOCKED" logs/autonomous_response.log | tail -20

# All alerts from today
grep "ALERT" logs/autonomous_response.log | grep "$(date +%Y-%m-%d)"
```

### Check System Statistics

```bash
# Print current statistics
python -c "
from src.autonomous_response_agent import AutonomousResponseAgent
agent = AutonomousResponseAgent('sg-xxxxx')
agent.display_statistics()
"
```

---

## Monitoring Dashboard

### Key Metrics to Track

```
REAL-TIME (every minute):
  ▶ Currently blocked IPs count
  ▶ Average risk score
  ▶ Last action taken

HOURLY:
  ▶ Blocks in last hour
  ▶ Unblocks in last hour
  ▶ Alerts sent
  ▶ Rate limits applied

DAILY:
  ▶ Total threats detected
  ▶ Total unique IPs blocked
  ▶ Average block duration
  ▶ False positive rate
```

### Setting Up Log Aggregation

```bash
# Export logs to S3 (daily backup)
aws s3 cp logs/autonomous_response.log \
  s3://my-backup-bucket/threat-logs/$(date +%Y-%m-%d).log

# Or set up CloudWatch logging
aws logs create-log-group --log-group-name /threat-detection/agent
tail -f logs/autonomous_response.log | \
  aws logs put-log-events --log-group-name /threat-detection/agent
```

---

## Tuning & Optimization

### Adjusting Risk Thresholds

**Too Many False Positives?**
```python
# Increase thresholds (make it harder to trigger actions)
# In threat_fusion_engine.py or autonomous_response_agent.py

# Current: 0.4 for medium
# Try: 0.5 for medium threshold
```

**Missing Some Attacks?**
```python
# Decrease thresholds (make it easier to trigger actions)
# Current: 0.8 for critical
# Try: 0.7 for critical threshold
```

**Adjust Block Duration**
```python
# src/enhanced_main_with_agent.py
self.response_agent = AutonomousResponseAgent(
    security_group_id=security_group_id,
    block_timeout_minutes=15,  # Was 10, now 15 minutes
    monitoring_interval=60
)
```

### Performance Tuning

**Increase Monitoring Frequency**
```python
# Check more often (every 30 seconds instead of 60)
monitoring_interval=30
```

**Batch Process Multiple Threats**
```python
# If handling many threats, group them:
threats = []
# ... collect threats ...
# Process all at once instead of one by one
```

---

## Incident Response

### When an IP is Blocked

**Immediate (< 5 minutes):**
1. ✅ Alert sent to security team
2. ✅ IP added to blocked list
3. ✅ Security Group rule added
4. ✅ Event logged with timestamp

**Short-term (5-10 minutes):**
1. ⬜ Investigate threat pattern
2. ⬜ Check if legitimate traffic
3. ⬜ Determine if false positive
4. ⬜ Monitor attack progression

**Long-term (10+ minutes):**
1. ⬜ Auto-unblock executes (if timeout not extended)
2. ⬜ Log final disposition
3. ⬜ Add to incident database
4. ⬜ Adjust thresholds if needed

### False Positive Detected

```bash
# 1. Immediate unblock
aws ec2 revoke-security-group-ingress \
  --group-id sg-xxxxx \
  --protocol all \
  --cidr 203.0.113.42/32

# 2. Log incident
echo "FALSE POSITIVE: IP 203.0.113.42 blocked at $(date)" >> incident.log

# 3. Adjust thresholds
# Edit risk threshold or network risk baseline

# 4. Re-enable monitoring
# Restart agent with new settings
```

### Confirmed Attack

```bash
# 1. Extend block duration
# Edit block_timeout_minutes: 10 → 60

# 2. Add additional rules
aws ec2 authorize-security-group-egress \
  --group-id sg-xxxxx \
  --protocol all \
  --cidr 203.0.113.42/32

# 3. Escalate
# - Notify SOC/Security team
# - Create incident ticket
# - Update threat intelligence

# 4. Investigation
grep "203.0.113.42" logs/autonomous_response.log
grep "203.0.113.42" logs/threat_alerts.json
```

---

## Maintenance Tasks

### Weekly

```bash
# Monday Morning
# 1. Archive logs
tar -cz logs/ > logs_backup_$(date +%Y-%m-%d).tar.gz
s3 cp logs_backup_*.tar.gz s3://my-bucket/

# 2. Review statistics
python -c "from src.autonomous_response_agent import *; agent = AutonomousResponseAgent('sg-xxxxx'); agent.display_statistics()"

# 3. Check for stuck blocks
grep -c "currently blocked" logs/autonomous_response.log

# 4. Run test suite
python test_autonomous_agent.py
```

### Monthly

```bash
# First of month
# 1. Full log review and analysis
# 2. Threshold adjustment proposals
# 3. Performance metrics review
# 4. Security posture assessment
# 5. Plan any tuning for next month
```

### Quarterly

```bash
# Every 3 months
# 1. Security Group cleanup
# 2. IAM permissions audit
# 3. False positive analysis
# 4. Capacity planning
# 5. Disaster recovery test
```

---

## Escalation Procedures

### Level 1: Minor Issue

**Symptoms:**
- Single IP blocked briefly
- Expected behavior
- No system degradation

**Action:**
- Monitor and log
- No escalation needed
- Add to statistics

**Example:**
```
Risk 0.2 → Log
Risk 0.5 → Alert
Risk 0.7 → Rate limit
```

### Level 2: Moderate Issue

**Symptoms:**
- Multiple IPs blocked in short time
- Possible DDoS attack starting
- Some service slowdown

**Action:**
- Notify security team
- Increase monitoring
- Prepare incident response
- Review thresholds

**Escalation Contact:**
```
On-call Security Engineer:
  Phone: [CONTACT]
  Slack: #security-incidents
```

### Level 3: Major Incident

**Symptoms:**
- 10+ IPs blocked simultaneously
- Clear active attack
- Significant service impact
- Agent overwhelmed

**Action:**
- Trigger major incident response
- Contact incident commander
- Activate war room
- Consider manual intervention

**Escalation Contact:**
```
Incident Commander:
  Phone: [CONTACT]
  Slack: @incident-commander
  War Room: [BRIDGE]
```

---

## Recovery Procedures

### Agent Crash Recovery

```bash
# 1. Check status
ps aux | grep autonomous

# 2. View error log
tail -100 logs/autonomous_response.log | grep ERROR

# 3. Fix issue (example: AWS credentials)
aws sts get-caller-identity  # Verify creds work

# 4. Restart agent
python run.py

# 5. Verify recovery
sleep 10
ps aux | grep autonomous
```

### Security Group Corruption

```bash
# 1. Backup current rules
aws ec2 describe-security-group-rules \
  --filters Name=group-id,Values=sg-xxxxx \
  > sg_backup_$(date +%Y-%m-%d_%H%M%S).json

# 2. View suspicious rules
aws ec2 describe-security-group-rules \
  --filters Name=group-id,Values=sg-xxxxx | jq .SecurityGroupRules[]

# 3. Remove problematic rule
aws ec2 revoke-security-group-ingress \
  --group-id sg-xxxxx \
  --security-group-rule-ids sgr-xxxxx

# 4. Restart agent
python run.py
```

### High False Positive Rate

```bash
# 1. Immediate: Disable autonomous blocking
# Edit enhanced_main_with_agent.py:
ENABLE_AUTONOMOUS_RESPONSE = False

# 2. Collect data for analysis
tail -1000 logs/autonomous_response.log > fp_analysis.log

# 3. Identify pattern
grep "BLOCKED\|ALERT" fp_analysis.log | \
  cut -d'|' -f2 | \
  sort | uniq -c | sort -rn

# 4. Adjust thresholds
# Edit risk calculation or network baseline

# 5. Test with new settings
python test_autonomous_agent.py

# 6. Re-enable with care
ENABLE_AUTONOMOUS_RESPONSE = True
python run.py
```

---

## Troubleshooting Guide

| Issue | Symptom | Root Cause | Fix |
|-------|---------|-----------|-----|
| No blocks occurring | Risk scores high but no IPs blocked | `ENABLE_AUTONOMOUS_RESPONSE = False` | Set to `True` in config |
| Blocks not removing | IPs stuck in block list | Timeout too long or agent crashed | Manually revoke rule or restart agent |
| AWS API errors | Frequent errors in logs | Invalid credentials or SG ID | Verify with `aws sts get-caller-identity` |
| High resource usage | Agent consuming CPU/memory | Logging too verbose | Reduce log level or batch operations |
| False positives | Legitimate IPs getting blocked | Thresholds too aggressiv | Increase thresholds, retrain ML |
| Missing detections | Known attacks not blocked | Thresholds too conservative | Decrease thresholds |
| Slow response | Takes > 5 seconds to block | Network latency to AWS | Monitor AWS API health |
| Duplicate blocks | Same IP blocked multiple times | Check logic failed | Verify blacklist implementation |

---

## Performance Baselines

```
Expected Performance:
  ├─ Agent startup: 2-5 seconds
  ├─ Risk evaluation: <1ms per IP
  ├─ AWS API call: 100-500ms
  ├─ Log write: <10ms
  └─ Total decision-to-block: <3 seconds

Resource Usage:
  ├─ Memory: 50-100MB
  ├─ CPU (idle): <1%
  ├─ CPU (active blocking): 3-5%
  ├─ Network: <1Mbps (for logs + API)
  └─ Disk (per 1000 actions): 50KB

Throughput:
  ├─ Threats processed per cycle: 1-5
  ├─ Blocks per hour: 0-100 (depends on traffic)
  └─ Max concurrent blocks: Limited by SG rules (~500)
```

---

## Contact & Escalation

```
Security Team: security@company.com
On-Call Engineer: [PHONE/SLACK]
Incident Commander: [PHONE/SLACK]
AWS Support: [SUPPORT_ID]

Documentation:
  ├─ Deployment Guide: AUTONOMOUS_AGENT_DEPLOYMENT_GUIDE.md
  ├─ Quick Reference: AGENT_QUICK_REFERENCE.md
  └─ Test Suite: test_autonomous_agent.py
```

---

**Last Updated**: February 28, 2026
**Version**: 2.0
**Status**: Production Ready
