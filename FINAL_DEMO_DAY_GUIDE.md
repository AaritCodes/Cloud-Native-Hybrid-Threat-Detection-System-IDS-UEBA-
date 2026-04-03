# 🚀 Final Demo Day Guide

**Author:** Aarit Haldar
**USN:** ENG24CY0073
**Project:** Cloud-Native Hybrid Threat Detection System

This is your master document for demo day. It contains everything you need: the setup checklist, the exact commands to run, your script of what to say, and the answers to the toughest questions you might be asked.

---

## 1. The 30-Second Elevator Pitch
"I built a hybrid threat detection system for AWS that combines network monitoring and user behavior analytics using a novel 60/40 weighted fusion algorithm. It detects threats 2-3x faster than existing solutions with zero false positives during testing, and includes an autonomous response agent that automatically blocks attacks."

---

## 2. Pre-Demo Checklist

1. **Activate Environment:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
2. **Check AWS credentials:**
   ```powershell
   aws sts get-caller-identity
   ```
3. **Ensure Ollama is running:**
   ```powershell
   curl http://localhost:11434/api/tags
   ```
   *(If not running, start it in a separate terminal with `ollama serve`)*
4. **Prepare Two Terminals:** Terminal 1 for Detection, Terminal 2 for Attack Simulation.

---

## 3. Demo Execution Walkthrough

**Recommended Approach:** Show the baseline pure-rule system first, and then show the AI agentic upgrade.

### DEMO A: Traditional Baseline (Rule-Based, No AI)

**Terminal 1:** Start Detection
```powershell
python src/enhanced_main.py
```

🎤 **What to say:**
> "This is our baseline system — IDS plus UEBA combined with the 60/40 fusion algorithm. It's monitoring network traffic and user behavior on our AWS EC2 instance. Right now everything is normal."

**Terminal 2:** Launch Attack Simulator
```powershell
python tests/attack_simulator.py
```

🎤 **Wait 15 seconds, point to Terminal 1, and say:**
> "The system caught the DDoS attack in ~15 seconds — traffic jumped 364x. The fusion algorithm computed a HIGH risk of 0.61 and sent an alert. But notice: there's no explanation of *why*, no automatic response action, and no ability to learn from this event. It just fires an alert."

*(Stop both terminals with `Ctrl+C`)*

---

### DEMO B: Agentic AI System (ReAct + Tool-Calling)

**Terminal 1:** Start AI Detection
```powershell
python src/enhanced_main_with_agent.py
```

🎤 **What to say:**
> "Same system, but now with the Agentic AI layer. Notice the AI is *explaining its reasoning* in plain English and calling tools to check the IP reputation and network baseline. All of this runs locally using Ollama and Llama 3."

**Terminal 2:** Launch Attack Simulator
```powershell
python tests/attack_simulator.py
```

🎤 **Wait 15 seconds, point to Terminal 1, and say:**
> "Same attack, same risk score (0.61) — but look at the difference. The AI gathered intelligence first: it checked IP reputation and past threats. It explains that this is an external DDoS because user behavior is normal. Most importantly, it actually *took action* — applying rate limiting automatically instead of just warning us. Every decision is stored in an SQLite database for the adaptive threshold learning."

---

## 4. Side-by-Side Architectural Summary

| DEMO A: Traditional (Rule-Based) | DEMO B: Agentic AI (ReAct) |
|---|---|
| **Action taken:** Alert sent (that's it) | **Action taken:** RATE_LIMIT + Alert |
| **Explanation:** (none) | **Explanation:** Explicit English analysis of network vs user risk |
| **Tools used:** (none) | **Tools:** `check_ip_reputation`, `get_similar_threats` |
| **Memory:** None (resets every run) | **Memory:** SQLite DB (persists forever) |
| **Learning:** None | **Learning:** Feedback loop, adapts over time |
| **Cost to Run:** $0 | **Cost to Run:** $0 (Local Ollama) |

---

## 5. Technical Defense & Q&A

### How the 60/40 Fusion Algorithm Works
**Q: "Why 60/40 weighting and not 50/50?"**
**A:** "I tested different weight combinations: 50/50, 60/40, and 70/30. 60/40 gave the best balance: fast detection with 0% false positives in my testing. Network signals get 60% because they're more reliable for detecting external attacks rapidly. User behavior gets 40% to provide context. For example, during a DDoS attack, network risk is 0.95 but user risk is 0.10. At 60/40, final risk is 0.61 (Rate Limit). If we used 50/50, it would be lower and slower to respond."

**Final Risk = (0.6 × Network Risk) + (0.4 × User Risk)**
- `< 0.4` → **LOG**
- `0.4–0.6` → **ALERT**
- `0.6–0.8` → **RATE_LIMIT**
- `≥ 0.8` → **BLOCK IP**

### Algorithm Selection
**Q: "Why did you use Isolation Forest instead of Neural Networks?"**
**A:** "Isolation Forest is exceptionally well-suited for anomaly detection with limited data. It's unsupervised so I don't need labeled attack data, it's fast (<10ms inference), and doesn't require massive datasets or GPUs. Deep learning is overkill for classifying simple numerical cloud metrics and would increase inference latency."

### The "Honest" AI Defense
**Q: "Isn't the AI just a gimmick or hallucinating?"**
**A:** "The AI provides decision *augmentation*, not the core detection. The 60/40 math does the actual detection. The AI adds explainability - it tells you WHY a mathematical decision was made. For security teams, this is critical for trust and auditing. Furthermore, because the AI is just an enhancement layer, the system has fallback logic: if the LLM crashes, the system securely defaults back to Rule-Based responses."

### False Positives Caveat
**Q: "Can you really guarantee 0% false positives?"**
**A:** "We achieved 0% false positives in our *controlled testing scenarios* with simulated DDoS attacks and baseline traffic. While the 60/40 fusion is specifically designed to minimize false positives by combining signals, a true production deployment would naturally require validation across a wider variety of legitimate traffic spikes (e.g. Black Friday events) and diverse attack types."

---

## 6. Emergency Troubleshooting

- **`No module named 'src'`** → You are not in the root directory. Run: `cd "unified threat detection"`
- **AWS credentials not found** → Run `aws configure`
- **Ollama connection failed** → Run `ollama serve`
- **AI Agent very slow** → The first run takes ~10 seconds to load the model into VRAM. Subsequent inferences are 1-3 seconds.
- **Security group permission denied** → Ensure your AWS IAM role has `ec2:AuthorizeSecurityGroupIngress`.
