# Demo Day Commands
## Two Demo Modes: Traditional vs Agentic AI

**Author:** Aarit Haldar  
**Date:** March 2, 2026

---

## Overview

This guide shows **two ways** to run the system:

| | **Demo A: Traditional (Rule-Based)** | **Demo B: Agentic AI (ReAct Agent)** |
|---|---|---|
| **Command** | `python src/enhanced_main.py` | `python src/enhanced_main_with_agent.py` |
| **Decision method** | Fixed thresholds (0.4 / 0.6 / 0.8) | LLM reasoning + tool-calling + memory |
| **Explainability** | Numbers only | Plain-English reasoning |
| **Learning** | None | Persistent memory, feedback loop, adaptive thresholds |
| **Cost** | $0 | $0 (local Ollama) |
| **Requires Ollama?** | No | Yes (falls back to rules if unavailable) |

**Recommended approach:** Run Demo A first, then Demo B. This shows the professor what you started with and what you built on top.

---

## Pre-Demo Checklist

```bash
# 1. Activate virtual environment
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# 2. Check Python
python --version   # 3.8+

# 3. Check AWS credentials
aws sts get-caller-identity

# 4. (Demo B only) Check Ollama is running
curl http://localhost:11434/api/tags
# Should list llama3:latest

# 5. (Demo B only) If Ollama not running
ollama serve          # Start Ollama
ollama pull llama3    # Download model (one-time, ~4.7 GB)
```

---

---

# DEMO A: Traditional System (Rule-Based, No AI)

> **Use this to show the baseline — pure IDS + UEBA + 60/40 Fusion + Alerting.**
> **No AI agent. No autonomous blocking. Just detection + alerts.**

---

## A1. Start Detection (Terminal 1)

```bash
python src/enhanced_main.py
```

**What this runs:**
- IDS Engine → CloudWatch network metrics
- UEBA Engine → CloudTrail user behavior logs
- 60/40 Weighted Fusion → combines both into a final risk score
- Alert System → email + console + file logging
- **No AI agent, no autonomous response, no memory**

**Expected Output (Normal Traffic):**

```
Initializing Enhanced Hybrid Threat Detection System...
System initialized successfully!
Email alerts configured for HIGH/CRITICAL threats
Dashboard available at: http://localhost:8050 (run dashboard.py)
Starting detection cycles...

===== Hybrid Threat Detection Cycle =====
Running IDS...
IDS Done
Running UEBA...
UEBA Done

IP: EC2_INSTANCE
Network Risk: 0.05
User Risk: 0.10
Final Risk: 0.07
Threat Level: LOW
Network Traffic: 15,249 bytes, 72 packets
```

**What to say:**
> "This is our baseline system — IDS plus UEBA combined with the 60/40 fusion algorithm. It's monitoring network traffic and user behavior on our AWS EC2 instance. Right now everything is normal — risk is 0.07."

---

## A2. Launch Attack (Terminal 2)

```bash
python tests/attack_simulator.py
```

Sends 300 concurrent HTTP threads for 60 seconds. Generates 1000x–4000x normal traffic.

---

## A3. Watch Detection (Terminal 1)

**Expected Output During Attack:**

```
===== Hybrid Threat Detection Cycle =====

IP: EC2_INSTANCE
Network Risk: 0.95
User Risk: 0.10
Final Risk: 0.61
Threat Level: HIGH
Network Traffic: 5,547,892 bytes, 65,432 packets

======================================================================
SECURITY ALERT - HIGH
======================================================================
Time: 2026-03-02 10:05:32
IP Address: EC2_INSTANCE
Risk Score: 0.61
Network Risk: 0.95
User Risk: 0.10
Action: Alert notification sent
======================================================================
```

**What to point out:**

1. **Detection works** — caught the DDoS in ~15 seconds
2. **60/40 fusion** — network 0.95 + user 0.10 → final 0.61 (HIGH, not CRITICAL)
3. **Alert sent** — but that's all it does
4. **No explanation** — just numbers and a label
5. **No automatic action** — no rate limiting, no blocking
6. **No memory** — every cycle starts from scratch, no learning

**What to say:**
> "The system detected the DDoS attack — traffic jumped 364x. The fusion algorithm correctly computed a HIGH risk of 0.61 and sent an alert. But notice: there's no explanation of *why*, no automatic response action, and no ability to learn from this event. It just fires and forgets."

---

## A4. Stop

Press `Ctrl+C` in both terminals.

**Expected statistics:**

```
SYSTEM STATISTICS
==================================================
Detection Cycles: 4
Threats Detected: 1
Total Alerts: 1
   - HIGH: 1
==================================================
System stopped gracefully.
```

---

---

# DEMO B: Agentic AI System (ReAct + Tool-Calling + Memory)

> **Use this to show the full upgrade — everything from Demo A, plus:**
> - **ReAct reasoning loop** (Observe → Think → Tool-Call → Decide → Reflect)
> - **Tool-calling** (IP reputation, attack history, network baseline, similar threats)
> - **Persistent memory** (SQLite database stores every decision)
> - **Autonomous response** (graduated: LOG → ALERT → RATE_LIMIT → BLOCK)
> - **Feedback loop** (record outcomes → adaptive thresholds)

---

## B1. Start Detection with Agent (Terminal 1)

```bash
python src/enhanced_main_with_agent.py
```

**Expected Output (Normal Traffic):**

```
======================================================================
Hybrid Threat Detection System with Autonomous Response
======================================================================
Security Group: sg-096157899840a1547
Autonomous Response: ENABLED
======================================================================

Initializing Enhanced Hybrid Threat Detection System with Autonomous Response...
Agentic AI Agent initialized (ReAct + tool-calling + memory)
System initialized successfully!
Starting detection cycles...

===== Hybrid Threat Detection Cycle =====

IP: EC2_INSTANCE
Network Risk: 0.05
User Risk: 0.10
Final Risk: 0.07
Threat Level: LOW

Autonomous Response Agent evaluating threat...
Agentic AI analyzing threat (ReAct reasoning)...

AI Reasoning: This appears to be normal baseline traffic with low risk
indicators. IP has no prior malicious history. No action required
beyond standard logging.
AI Recommendation: LOG
Tools consulted: check_ip_reputation, get_network_baseline

Autonomous action taken: LOG
```

**What to say:**
> "Same system, but now with the Agentic AI layer. Notice two new things: the AI is *explaining its reasoning* in plain English, and it tells us which tools it consulted — it checked the IP reputation and the network baseline before deciding. All of this runs locally using Ollama and Llama 3."

---

## B2. Launch Attack (Terminal 2)

```bash
python tests/attack_simulator.py
```

---

## B3. Watch Detection (Terminal 1)

**Expected Output During Attack:**

```
===== Hybrid Threat Detection Cycle =====

IP: EC2_INSTANCE
Network Risk: 0.95
User Risk: 0.10
Final Risk: 0.61
Threat Level: HIGH

Autonomous Response Agent evaluating threat...
Agentic AI analyzing threat (ReAct reasoning)...

AI Reasoning: The network risk of 0.95 indicates a severe traffic anomaly
(364x increase from baseline). However, user behavior remains normal at
0.10, suggesting an external DDoS attack rather than compromised
credentials. IP reputation check shows no prior malicious history.
Based on the 60/40 fusion score of 0.61, rate limiting is the
appropriate graduated response to protect resources while avoiding
false-positive IP blocks.
AI Recommendation: RATE_LIMIT
Tools consulted: check_ip_reputation, get_similar_threats, get_network_baseline

======================================================================
RATE LIMITING ACTIVATED
======================================================================
IP Address: EC2_INSTANCE
Risk Score: 0.61
Action: Traffic rate limited to 10 req/min
Duration: 5 minutes
======================================================================

======================================================================
SECURITY ALERT - HIGH
======================================================================
Time: 2026-03-02 10:05:32
IP Address: EC2_INSTANCE
Risk Score: 0.61
Network Risk: 0.95
User Risk: 0.10
Action: Alert notification sent
======================================================================

Autonomous action taken: RATE_LIMIT
```

**What to point out (compare to Demo A):**

1. **Same detection** — 15 seconds, same risk scores
2. **But now: full reasoning** — tells you *why* it chose RATE_LIMIT
3. **Tool-calling** — AI queried IP reputation, similar past threats, network baseline
4. **Autonomous action** — actually applied rate limiting (Demo A only sent an alert)
5. **Context-aware** — recognized external attack vs compromised account
6. **Persistent** — this decision is stored in SQLite for future learning

**What to say:**
> "Same attack, same risk scores — but now look at the difference. The AI gathered intelligence first: it checked IP reputation, found similar past threats, and checked the network baseline. Then it explained that this is an external DDoS because user behavior is normal. And it actually *took action* — it applied rate limiting automatically. Every decision gets stored in a database, so the system learns over time."

---

## B4. Stop & See Statistics

Press `Ctrl+C` in Terminal 1.

**Expected Output:**

```
SYSTEM STATISTICS
==================================================
Uptime: 0:03:45
Detection Cycles: 4
Threats Detected: 1
Autonomous Actions: 1

AUTONOMOUS RESPONSE STATISTICS
   - IPs Blocked: 0
   - IPs Unblocked: 0
   - Rate Limits Applied: 1

AGENTIC AI LEARNING METRICS
   - Agent Type: ReAct-Agentic
   - Model: llama3:latest
   - Total Decisions in Memory: 4
   - Accuracy: 100.0%
   - Precision: 100.0%
   - Recall: 100.0%
==================================================
System stopped gracefully.
```

**What to say:**
> "The statistics now include AI learning metrics — accuracy, precision, recall — computed from recorded outcomes. As the system processes more events and receives feedback, these thresholds adapt. The more it runs, the smarter it gets."

---

---

# Side-by-Side Comparison

Show this to clearly contrast what changed:

```
┌──────────────────────────────────────┬──────────────────────────────────────┐
│   DEMO A: Traditional (Rule-Based)   │   DEMO B: Agentic AI (ReAct)         │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ Command:                             │ Command:                             │
│ python src/enhanced_main.py          │ python src/enhanced_main_with_agent.py│
│                                      │                                      │
│ Network Risk: 0.95                   │ Network Risk: 0.95                   │
│ User Risk: 0.10                      │ User Risk: 0.10                      │
│ Final Risk: 0.61                     │ Final Risk: 0.61                     │
│                                      │                                      │
│ Action: Alert sent (that's it)       │ Action: RATE_LIMIT + Alert           │
│ Explanation: (none)                  │ Explanation: "364x traffic increase,  │
│                                      │  external attack, user behavior      │
│                                      │  normal, graduated response"         │
│                                      │                                      │
│ Tools used: (none)                   │ Tools: check_ip_reputation,          │
│                                      │  get_similar_threats,                │
│                                      │  get_network_baseline                │
│                                      │                                      │
│ Memory: None (resets every run)      │ Memory: SQLite DB (persists forever) │
│ Learning: None                       │ Learning: Feedback loop, adapts      │
│ Autonomous action: None              │ Autonomous action: Rate limiting     │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

---

# Architecture Comparison

### Demo A: Traditional Pipeline
```
CloudWatch → IDS Engine (network risk)
CloudTrail → UEBA Engine (user risk)
         ↓
   60/40 Fusion → Risk Score
         ↓
   Fixed Thresholds → Alert
         ↓
       (done)
```

### Demo B: Agentic AI Pipeline
```
CloudWatch → IDS Engine (network risk)
CloudTrail → UEBA Engine (user risk)
         ↓
   60/40 Fusion → Risk Score
         ↓
   ┌─────────────────────────────────────────┐
   │  ReAct Agent (Ollama / Llama 3)         │
   │                                         │
   │  OBSERVE → risk scores + context        │
   │  THINK   → what tools do I need?        │
   │  TOOLS   → IP reputation, history,      │
   │             baseline, similar threats    │
   │  DECIDE  → action + reasoning           │
   │  REFLECT → persist to SQLite            │
   └─────────────┬───────────────────────────┘
                 ↓
   Autonomous Response → LOG / ALERT / RATE_LIMIT / BLOCK
                 ↓
   Feedback Loop → record_outcome() → adaptive thresholds
```

---

# BONUS: Test AI Agent Standalone

```bash
python tests/test_agentic_agent.py
```

Tests the ReAct agent directly — sends sample threats, shows reasoning + tool calls, records a feedback outcome, and prints accuracy metrics. Good for a quick demo of the AI without needing the full system running.

---

# Talking Script

### Opening (30 sec)

> "I built a hybrid threat detection system with two modes: a traditional rule-based system, and an agentic AI upgrade. Let me show you both."

### Demo A (1.5 min)

> "This is the baseline — IDS, UEBA, and 60/40 fusion. It detects the DDoS attack in 15 seconds and sends an alert. But all you get is numbers — no explanation, no automatic response, no learning."

### Transition (15 sec)

> "Now let me show you the same system with Agentic AI."

### Demo B (2 min)

> "Same detection, same risk scores — but now the AI agent kicks in. It follows a ReAct reasoning loop: observes the threat, calls tools to check IP reputation and past history, then makes an informed decision with a full English explanation. It automatically applied rate limiting and stored this decision in a database for future learning."

### Key Differentiators (30 sec)

> "Three things make the AI version special:
> 1. **Explainable** — it tells you *why*, not just *what*
> 2. **Tool-calling** — it gathers evidence before deciding, like a real analyst
> 3. **Learning** — it remembers past decisions and adapts thresholds
>
> And it all runs locally with Ollama — zero cost, fully private."

### Closing (15 sec)

> "So I built both: a solid traditional system *and* an agentic AI layer on top. The result is faster detection, smarter responses, and explainable decisions."

---

# 60/40 Fusion Explained (If Asked)

```
Final Risk = (0.6 × Network Risk) + (0.4 × User Risk)

DDoS attack:        (0.6 × 0.95) + (0.4 × 0.10) = 0.61 → RATE_LIMIT
Compromised account: (0.6 × 0.95) + (0.4 × 0.90) = 0.93 → BLOCK
Normal traffic:      (0.6 × 0.05) + (0.4 × 0.10) = 0.07 → LOG

Thresholds:
  < 0.4  → LOG
  0.4–0.6 → ALERT
  0.6–0.8 → RATE_LIMIT
  ≥ 0.8  → BLOCK
```

---

# Troubleshooting

| Problem | Solution |
|---|---|
| `No module named 'src'` | Run from project root: `cd "unified threat detection"` |
| `AWS credentials not found` | Run `aws configure` |
| `Ollama connection failed` | Run `ollama serve` then `ollama pull llama3` |
| `AI agent slow (>10s)` | First call loads model; subsequent calls are 1-3s |
| `Unicode errors on Windows` | Cosmetic only, results still work |
| `Security Group permission denied` | Check IAM has `ec2:AuthorizeSecurityGroupIngress` |

---

# Quick Reference

| Action | Command |
|---|---|
| **Demo A**: Traditional system | `python src/enhanced_main.py` |
| **Demo B**: Agentic AI system | `python src/enhanced_main_with_agent.py` |
| Launch attack | `python tests/attack_simulator.py` |
| Test AI agent standalone | `python tests/test_agentic_agent.py` |
| Check Ollama status | `curl http://localhost:11434/api/tags` |
| View decision database | `python -c "from src.decision_store import DecisionStore; s=DecisionStore(); print(s.get_accuracy_stats())"` |
| View logs | `cat logs/autonomous_response.log` |
| View saved alerts | `cat logs/threat_alerts.json` |

---

**Author:** Aarit Haldar  
**Date:** March 2, 2026  
**Institution:** Engineering College  
**USN:** ENG24CY0073
