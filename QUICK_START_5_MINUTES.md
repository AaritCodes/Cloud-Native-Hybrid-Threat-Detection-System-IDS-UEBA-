# 5-Minute Quick Start Guide

Get your Autonomous Response Agent running in 5 minutes!

---

## Step 1: Get Your Security Group ID (30 seconds)

```bash
aws ec2 describe-security-groups --region ap-south-1 --query 'SecurityGroups[0].GroupId'
```

Expected output: `"sg-0123456789abcdef0"`

**Save this ID** ← You'll need it in Step 2

---

## Step 2: Update Configuration (1 minute)

Open file: `src/enhanced_main_with_agent.py`

Find line ~235:
```python
SECURITY_GROUP_ID = "sg-0123456789abcdef0"  # TODO: Replace with your SG ID
```

Replace `sg-0123456789abcdef0` with **your actual Security Group ID** from Step 1

Example:
```python
SECURITY_GROUP_ID = "sg-abc1234def567890f"  # ← Your actual ID
```

**Save the file** (Ctrl+S)

---

## Step 3: Verify AWS Credentials (1 minute)

```bash
aws sts get-caller-identity
```

**Should output** something like:
```json
{
    "UserId": "AIDAJ12345678901234",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

If error: See troubleshooting at end

---

## Step 4: Start the System (30 seconds)

```bash
python run.py
```

**Expected output:**
```
🛡️  Hybrid Threat Detection System with Autonomous Response
...
✅ System initialized successfully!
🔄 Starting detection cycles...
```

---

## Step 5: Monitor (1-2 minutes)

### In Terminal 1 (already running `python run.py`):
Watch for output like:
```
===== Hybrid Threat Detection Cycle =====
Running IDS...
Running UEBA...
IP: EC2_INSTANCE
Final Risk: 0.2
Action taken: LOG
```

### In Terminal 2 (new terminal):
```bash
# View live logs
tail -f logs/autonomous_response.log
```

### In Terminal 3 (new terminal):
```bash
# View threats detected
tail -f logs/threat_alerts.json
```

---

## ✅ You're Done!

Your system is now:
- ✅ Monitoring threat levels
- ✅ Making automated decisions
- ✅ Ready to block critical threats
- ✅ Logging all actions

---

## What's It Doing?

Every 60 seconds, the system:

1. **Checks network traffic** (IDS Engine)
   - Monitors for DDoS patterns
   - Uses AWS CloudWatch data

2. **Checks user behavior** (UEBA Engine)
   - Looks for unusual user activity
   - Analyzes AWS CloudTrail logs

3. **Fuses risks** (Threat Fusion)
   - Combines network + user data
   - Calculates final risk score (0-1)

4. **Takes action** (Autonomous Agent)
   - **Risk < 0.4** → 🟢 LOG
   - **0.4 ≤ Risk < 0.6** → 🟡 ALERT
   - **0.6 ≤ Risk < 0.8** → 🟠 RATE LIMIT
   - **Risk ≥ 0.8** → 🔴 BLOCK IP (10 minutes)

---

## Example Actions

### Low Threat (Risk 0.2)
```
📝 LOW THREAT LOGGED | IP: EC2_INSTANCE | Risk: 0.20
```
**Action:** Just log - no alert needed

### Medium Threat (Risk 0.5)
```
⚠️  MEDIUM ALERT | IP: 192.168.1.100 | Risk: 0.50
```
**Action:** Send alert to security team

### High Threat (Risk 0.7)
```
⚡ RATE LIMITING ACTIVATED
🎯 IP Address: 192.168.1.101
📊 Risk Score: 0.70
🔒 Action: Traffic rate limited to 10 req/min
```
**Action:** Throttle traffic + alert

### Critical Threat (Risk 0.9)
```
🚫 CRITICAL THREAT - IP BLOCKED
🎯 Blocked IP: 203.0.113.42
📊 Risk Score: 0.92
🔒 Security Group: sg-xxxxx
⏱️  Auto-unblock in: 10 minutes
```
**Action:** Block immediately for 10 minutes

---

## Troubleshooting (30 seconds)

### ❌ Error: "Failed to initialize AWS client"
```bash
# Fix: Configure AWS
aws configure
# Enter: Access Key ID, Secret Access Key, Region (ap-south-1)
```

### ❌ Error: "No such file or directory: logs/autonomous_response.log"
```bash
# Fix: Create logs directory
mkdir -p logs
python run.py
```

### ❌ Error: "Invalid id: sg-xxxxx"
```bash
# Fix: Get correct Security Group ID
aws ec2 describe-security-groups --region ap-south-1 --query 'SecurityGroups[0].GroupId'
# Update the ID in src/enhanced_main_with_agent.py
```

### ❌ Error: "User is not authorized"
```bash
# Fix: Verify IAM permissions
# Your IAM user needs:
# - ec2:AuthorizeSecurityGroupIngress
# - ec2:RevokeSecurityGroupIngress
# - cloudwatch:GetMetricStatistics
# Contact your AWS admin
```

### ❌ No blocks happening even with high risk
```bash
# Fix: Check if feature is enabled
grep "ENABLE_AUTONOMOUS_RESPONSE" src/enhanced_main_with_agent.py
# Should show: ENABLE_AUTONOMOUS_RESPONSE = True
```

---

## Next Steps

### Immediate
- [ ] Let it run for 5-10 minutes
- [ ] Check `logs/autonomous_response.log`
- [ ] Verify it's working with test threat

### Later Today
- [ ] Run test suite: `python test_autonomous_agent.py`
- [ ] Read `AGENT_QUICK_REFERENCE.md`
- [ ] Review `AUTONOMOUS_AGENT_DEPLOYMENT_GUIDE.md`
- [ ] Adjust thresholds if needed

### This Week
- [ ] Monitor for false positives
- [ ] Fine-tune risk thresholds
- [ ] Set up monitoring/alerting on logs
- [ ] Document your setup

---

## Quick Commands

```bash
# Start the system
python run.py

# View live logs (new terminal)
tail -f logs/autonomous_response.log

# View threats (new terminal)
tail -f logs/threat_alerts.json

# Run tests
python test_autonomous_agent.py

# Check AWS credentials
aws sts get-caller-identity

# List security groups
aws ec2 describe-security-groups --region ap-south-1

# View blocked IPs
grep "IP BLOCKED" logs/autonomous_response.log

# Stop the system
# Press Ctrl+C in the terminal running python run.py
```

---

## Key Files to Know

```
Your Project/
├─ run.py                              ← Start here!
├─ src/
│  ├─ autonomous_response_agent.py     ← Core agent
│  ├─ enhanced_main_with_agent.py      ← Integration
│  ├─ ids_engine.py                    ← Network detection
│  ├─ ueba_engine.py                   ← User behavior
│  ├─ threat_fusion_engine.py          ← Risk combination
│  └─ alert_system.py                  ← Notifications
├─ logs/
│  ├─ autonomous_response.log          ← Agent logs
│  └─ threat_alerts.json               ← Alerts
├─ AGENT_QUICK_REFERENCE.md            ← Operator guide
├─ AUTONOMOUS_AGENT_DEPLOYMENT_GUIDE.md ← Full setup
├─ OPERATIONS_RUNBOOK.md               ← Incident response
└─ test_autonomous_agent.py            ← Test suite
```

---

## Success Indicators

### ✅ System is working if you see:

1. **In run.py output:**
   ```
   ✅ System initialized successfully!
   ```

2. **In logs/autonomous_response.log:**
   ```
   ✅ AWS EC2 client initialized for region: ap-south-1
   🚀 Autonomous Response Agent initialized
   ```

3. **Periodic detection cycles:**
   ```
   ===== Hybrid Threat Detection Cycle =====
   Running IDS...
   Running UEBA...
   ```

4. **Log entries from agent:**
   ```
   📝 LOW THREAT LOGGED | IP: ...
   or
   ⚠️  MEDIUM ALERT | IP: ...
   or
   🚫 IP BLOCKED | IP: ...
   ```

---

## Need Help?

1. **Quick answers**: See `AGENT_QUICK_REFERENCE.md`
2. **Setup issues**: See `AUTONOMOUS_AGENT_DEPLOYMENT_GUIDE.md`
3. **Operations**: See `OPERATIONS_RUNBOOK.md`
4. **Detailed info**: See `IMPLEMENTATION_SUMMARY.md`
5. **Testing**: Run `python test_autonomous_agent.py`

---

## The Bottom Line

You now have an **autonomous security system** that:

- 🔄 Continuously monitors threats (every 60 seconds)
- 🤖 Makes decisions automatically (no manual intervention)
- 🔒 Blocks attacks instantly (< 3 seconds)
- 📝 Logs everything (full audit trail)
- ✅ Works 24/7 (no human required)

**Status: LIVE AND PROTECTING YOUR INFRASTRUCTURE** 🛡️

---

**Questions?** Read the other documentation files or contact your security team.

*Happy threat hunting!* 🚀
