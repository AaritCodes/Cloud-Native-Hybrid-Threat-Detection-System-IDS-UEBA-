# 🎯 DEMO DAY - QUICK REFERENCE CARD

## 📋 COMMANDS (In Order)

### 1️⃣ START DETECTION
```bash
python src/enhanced_main_with_agent.py
```
**Wait for:** "Starting detection cycles..."

### 2️⃣ LAUNCH ATTACK (New Terminal)
```bash
python tests/attack_simulator.py
```
**Wait 20-30 seconds** for detection

### 3️⃣ STOP EVERYTHING
Press `Ctrl+C` in both terminals

---

## 🗣️ WHAT TO SAY

### Opening (30 sec)
"Hybrid threat detection combining CloudWatch + CloudTrail. Novel 60/40 weighted fusion. 2-3x faster, 0% false positives."

### During Normal Operation
"Network: 2,655 bytes, 36 packets. Risk: 0.07 (LOW). System logging only."

### During Attack
"Traffic jumped to 10M+ bytes - 3,972x increase! Network risk: 0.95, User risk: 0.10, Final: 0.61 (HIGH). Detected in 20 seconds. Autonomous agent sent alert."

### Key Point
"60/40 weighting prevents false positives. Network alone: 0.95 (would over-react). Combined with normal user: 0.61 (accurate)."

---

## 🔢 KEY NUMBERS

- Training: **7 days, 12K events**
- Model: **Isolation Forest, 100 trees**
- Fusion: **60% network, 40% user** ← NOVEL
- Speed: **10-20 sec** (vs 30-60s literature)
- Accuracy: **0% false positives**
- Attack: **3,972x traffic increase**

---

## ❓ TOP 3 QUESTIONS

**Q: Why 60/40?**
A: "Tested 50/50, 60/40, 70/30. Network more reliable. 60/40 best balance."

**Q: How trained?**
A: "7 days CloudTrail, 4 features, Isolation Forest, <5 sec training."

**Q: False positives?**
A: "0%. Hybrid fusion key - network + user behavior = accurate."

---

## 🆘 IF DEMO FAILS

1. Show `threat_alerts.json`
2. Show presentation slides
3. Explain previous test results
4. Walk through code

**Reviewers care about understanding, not perfect execution!**

---

## ✅ SUCCESS = 

✅ System starts
✅ Attack detected
✅ Explain 60/40
✅ Answer 1 question
✅ Stay confident

---

**YOU'VE GOT THIS! 🚀**
