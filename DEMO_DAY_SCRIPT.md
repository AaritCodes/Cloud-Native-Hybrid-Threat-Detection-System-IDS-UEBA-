# 🎯 Demo Day Script - Step by Step

## ⏰ Timeline: 5-7 Minutes Total

---

## 📋 Pre-Demo Checklist (Do This Before Demo Starts)

### 1. Test AWS Connection
```bash
aws sts get-caller-identity
```
✅ Should show your AWS account

### 2. Verify Files Exist
```bash
ls src/
ls models/
ls tests/
```
✅ Should see all Python files

### 3. Close All Terminals
- Close any running processes
- Start fresh

---

## 🎬 DEMO SCRIPT (Follow This Exactly)

### Part 1: Introduction (30 seconds)

**Say:**
> "I've built a hybrid threat detection system that combines network monitoring with user behavior analytics. It uses AWS CloudWatch for network metrics and CloudTrail for user activity. The novel contribution is a 60/40 weighted fusion algorithm that's 2-3x faster than existing solutions with zero false positives."

**Show:**
- Open `presentation/AICS_Project_Review_Presentation.pptx`
- Show title slide with team names

---

### Part 2: System Architecture (30 seconds)

**Say:**
> "The system has three main components: IDS engine monitors network traffic, UEBA engine analyzes user behavior using Isolation Forest ML model, and the threat fusion engine combines them with 60% weight to network and 40% to user behavior."

**Show:**
- Slide 6 & 7 (Proposed Methodology)

---

### Part 3: Live Demo - Normal Operation (1 minute)

**Terminal 1 - Start Detection System:**
```bash
python src/enhanced_main_with_agent.py
```

**Say while it's starting:**
> "Let me show you the system running in real-time. This is monitoring my EC2 instance on AWS."

**Wait for output, then explain:**
> "You can see:
> - Network traffic: 2,655 bytes, 36 packets - this is normal
> - Network risk: 0.05 (5%)
> - User risk: 0.10 (10%)
> - Final risk: 0.07 (7%) - LOW threat
> - Autonomous agent action: LOG only
> 
> The system is monitoring every 10 seconds and logging normal activity."

---

### Part 4: Live Demo - Attack Detection (2 minutes)

**Open NEW Terminal (Terminal 2) - Launch Attack:**
```bash
python tests/attack_simulator.py
```

**Say:**
> "Now I'm launching a DDoS attack with 300 concurrent threads targeting my EC2 instance. Watch Terminal 1..."

**Wait 20-30 seconds, watch Terminal 1 for detection**

**Point out in Terminal 1:**
> "Look at the detection:
> - Network traffic jumped to 10+ million bytes, 120,000+ packets
> - That's a 3,972x increase!
> - Network risk: 0.95 (95% - CRITICAL)
> - User risk: 0.10 (still normal - confirms external attack)
> - Final risk: 0.61 (61% - HIGH threat)
> 
> Notice the hybrid fusion: Network alone is 0.95, but combined with normal user behavior (0.10), the final risk is 0.61. This prevents false positives while still detecting the threat."

**Show the autonomous response:**
> "The autonomous response agent evaluated the threat and took action:
> - HIGH threat (0.6-0.8) triggers rate limiting and alerts
> - Email notification sent to security team
> - If it was CRITICAL (>0.8), it would automatically block the IP via AWS Security Group"

---

### Part 5: Show Results (1 minute)

**Terminal 3 - Check Current Traffic:**
```bash
python -c "from src.ids_engine import IDSEngine; ids = IDSEngine(); print(f'Traffic: {ids.get_metric(\"NetworkIn\"):,.0f} bytes, {ids.get_metric(\"NetworkPacketsIn\"):,.0f} packets')"
```

**Say:**
> "Current traffic is still elevated at 10+ million bytes. The system detected this within 20 seconds of attack start."

**Show Alert Log:**
```bash
type threat_alerts.json
```

**Say:**
> "Here's the alert history showing all detected threats with timestamps, risk scores, and threat levels."

---

### Part 6: Key Results (1 minute)

**Say:**
> "Key results:
> - Detection time: 10-20 seconds (literature: 30-60 seconds) - 2-3x faster
> - False positive rate: 0% (literature: 15-20%)
> - Attack detected: 3,972x traffic increase
> - Autonomous response: Graduated actions based on severity
> 
> The novel 60/40 weighting is crucial - it prevents over-reaction to network spikes while still catching real attacks."

**Show:**
- Slide 8 & 9 (Dataset Description with results)

---

### Part 7: Cleanup & Questions (30 seconds)

**Stop processes:**
```bash
# Press Ctrl+C in Terminal 1 (detection system)
# Press Ctrl+C in Terminal 2 (attack simulator)
```

**Say:**
> "That's the complete system. Happy to answer questions about the dataset, model training, fusion algorithm, or autonomous response."

---

## 🎯 Quick Commands Reference Card

**Print this and keep it handy:**

```
┌─────────────────────────────────────────────────────────┐
│              DEMO DAY COMMANDS                          │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 1. START DETECTION:                                     │
│    python src/enhanced_main_with_agent.py               │
│                                                         │
│ 2. LAUNCH ATTACK (new terminal):                        │
│    python tests/attack_simulator.py                     │
│                                                         │
│ 3. CHECK TRAFFIC:                                       │
│    python -c "from src.ids_engine import IDSEngine;    │
│    ids = IDSEngine(); print(f'Traffic:                 │
│    {ids.get_metric(\"NetworkIn\"):,.0f} bytes')"        │
│                                                         │
│ 4. SHOW ALERTS:                                         │
│    type threat_alerts.json                              │
│                                                         │
│ 5. STOP (in each terminal):                             │
│    Ctrl+C                                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 💡 Tips for Success

### Before Demo:
1. ✅ Test AWS connection: `aws sts get-caller-identity`
2. ✅ Close all terminals
3. ✅ Have presentation open
4. ✅ Have this script open
5. ✅ Take a deep breath!

### During Demo:
1. 🗣️ Speak clearly and confidently
2. ⏸️ Pause after each command to let it run
3. 👉 Point at the screen when explaining results
4. 😊 Smile and make eye contact
5. 🎯 Stick to the script

### If Something Goes Wrong:
1. **AWS connection fails**: Show the presentation slides instead
2. **Attack doesn't trigger**: Show the previous test results in `threat_alerts.json`
3. **System crashes**: Restart and show logs: `type threat_alerts.log`
4. **Forgot command**: Look at this script (it's okay!)

---

## 📊 Key Numbers to Remember

Memorize these for questions:

- **Training**: 7 days, 12,000 CloudTrail events
- **Features**: 4 (hour, day, activity_volume, service_diversity)
- **Model**: Isolation Forest, n_estimators=100, contamination=0.1
- **Fusion**: 60% network, 40% user (NOVEL)
- **Detection**: 10-20 seconds (2-3x faster than literature)
- **Accuracy**: 0% false positives, 100% true positives
- **Attack**: 3,972x traffic increase detected

---

## 🎤 Elevator Pitch (30 seconds)

If asked to summarize:

> "I built the first AWS-native hybrid threat detection system that combines CloudWatch network monitoring with CloudTrail user behavior analytics. The novel contribution is a 60/40 weighted fusion algorithm that's 2-3x faster than existing solutions with zero false positives. I validated it with a real DDoS attack that generated a 3,972x traffic increase, which the system detected in 20 seconds. The system includes an autonomous response agent that takes graduated actions from logging to automatic IP blocking based on threat severity."

---

## ❓ Common Questions & Answers

### Q: "Why 60/40 weighting?"
**A:** "Empirically tested 50/50, 60/40, 70/30. Network signals are more reliable for external attacks. 60/40 gave best balance - catches attacks without false positives."

### Q: "How did you train the model?"
**A:** "Collected 7 days of CloudTrail logs, extracted 4 behavioral features, trained Isolation Forest with 100 estimators and 0.1 contamination. Takes under 5 seconds to train."

### Q: "What about false positives?"
**A:** "Zero percent in testing. The hybrid fusion is key - network spike alone might be legitimate traffic, but combined with user behavior analysis, we accurately identify real threats."

### Q: "How does autonomous response work?"
**A:** "Graduated response based on risk: LOW logs only, MEDIUM sends alerts, HIGH applies rate limiting, CRITICAL automatically blocks IP via AWS Security Group using boto3. Blocks auto-expire after 10 minutes."

### Q: "Can you show the code?"
**A:** "Yes! [Open `src/threat_fusion_engine.py`] Here's the fusion algorithm - it's just 10 lines. Final risk equals 0.6 times network risk plus 0.4 times user risk."

---

## 📁 Files to Have Ready

Keep these files open in tabs:

1. `presentation/AICS_Project_Review_Presentation.pptx` - Main presentation
2. `DEMO_DAY_SCRIPT.md` - This file (your guide)
3. `QUICK_ANSWERS_CHEAT_SHEET.md` - For questions
4. `src/threat_fusion_engine.py` - To show code if asked
5. `threat_alerts.json` - Backup results

---

## ⏱️ Timing Breakdown

```
Introduction:           30 sec
Architecture:           30 sec
Normal Operation:       1 min
Attack Detection:       2 min
Show Results:           1 min
Key Results:            1 min
Questions:              Rest of time
─────────────────────────────
Total:                  6 min
```

---

## 🎯 Success Criteria

You'll know the demo went well if:

✅ System starts without errors
✅ Attack is detected within 30 seconds
✅ You explain the 60/40 weighting
✅ You show the risk scores changing
✅ You answer at least one question confidently
✅ You smile and seem confident

---

## 🚀 Final Checklist

**Morning of Demo:**
- [ ] Read QUICK_ANSWERS_CHEAT_SHEET.md
- [ ] Test AWS connection
- [ ] Close all terminals
- [ ] Open presentation
- [ ] Print this script
- [ ] Arrive 10 minutes early
- [ ] Deep breath - you've got this!

---

## 💪 Confidence Boosters

Remember:
- ✅ You built a working system
- ✅ You have real results
- ✅ You validated with actual attack
- ✅ You have novel contributions
- ✅ You're 2-3x faster than literature
- ✅ You have 0% false positives

**You've got this! 🚀**

---

## 📞 Emergency Backup Plan

If live demo fails completely:

1. Show presentation slides
2. Show `threat_alerts.json` file
3. Explain: "I have test results from previous runs showing..."
4. Walk through the code in `src/threat_fusion_engine.py`
5. Show the architecture diagram in presentation

The reviewers care more about your understanding than perfect execution!

---

**Good luck tomorrow! You're going to do great! 🎉**
