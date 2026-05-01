# Cloud-Native Hybrid Threat Detection System with Agentic AI Autonomous Response

Aarit Haldar, Priyanshu Sithole, Jay Bhagat  
Department of Computer Science and Engineering  
Dayananda Sagar College of Engineering, Bengaluru, India

## Abstract

This work presents a practical cloud-native threat detection system that combines two different views of risk: network anomalies (IDS) and user-behavior anomalies (UEBA). Instead of trusting either stream in isolation, we compute a fused score and then pass that score into an agentic decision layer that can explain its actions.

Our motivation came from a familiar SOC problem: analysts were spending too much time validating alerts that were technically correct but operationally weak. A sudden network spike may look dangerous but still be business traffic, while user drift without infrastructure evidence can be noisy. We built this system to reduce that gap between statistical anomaly and actionable response.

The implementation uses local model inference through Ollama, a bounded Observe-Think-Act-Decide loop, explicit policy thresholds, and deterministic fallback behavior if the LLM is unavailable. In scenario-driven evaluation (normal, suspicious, DDoS-like, and compromised-account behavior), the system produced stable action tiers (LOG, ALERT, RATE_LIMIT, BLOCK) aligned with security policy and operational safety.

## Keywords

intrusion detection, UEBA, risk fusion, cloud security, agentic AI, local LLM inference, autonomous response

## I. Introduction

Cloud environments changed the shape of security operations. Workloads scale quickly, identities are short-lived, and telemetry volume is high enough that analysts often cannot correlate everything in time. In our own testing setup, single-stream detection repeatedly showed the same weakness: it catches outliers, but it does not always tell us which outliers deserve immediate mitigation.

The central idea of this project is simple: combine independent signals before taking action. We fuse network anomaly risk and user-behavior risk, then ask an agentic layer to reason over that fused state using controlled tools. The system is not meant to replace analysts. It is meant to reduce triage pressure and produce clearer, auditable first decisions.

We also focused on operational trust. Autonomous controls are only useful when teams can understand why they fired, reverse them safely, and inspect what evidence was used. For that reason, we built policy tiers, tool limits, memory logging, and fallback logic into the core design instead of adding them later as patches.

## II. Related Work and Positioning

Isolation Forest and other unsupervised methods remain attractive in security because complete labeled attack data is rare. They help detect unusual patterns quickly, but in practice they often stop at scoring. Analysts still have to answer harder questions: Is this urgent? Is this likely malicious? Should we block or just watch?

Hybrid IDS approaches improve coverage by combining models, yet many implementations remain modality-centered. Some are good at network detection but weak on identity context. Others model behavior drift well but lag on fast infrastructure abuse.

Recent agentic or copilot-style security systems improved explainability, but several depend on hosted LLM services. That creates recurring cost and data-governance concerns for student teams and small SOC environments. In contrast, our system runs local inference and uses policy-bound decision logic. The practical contribution is not one novel algorithm; it is the end-to-end integration of fusion, bounded agentic reasoning, and safe response orchestration.

## III. System Architecture

The architecture is split into four layers.

1. Telemetry ingestion: network and identity events are collected from cloud-relevant sources.
2. Parallel detection: IDS and UEBA engines produce normalized risk scores.
3. Fusion and policy: the system computes fused risk and evaluates response thresholds.
4. Agentic reasoning and execution: the agent gathers extra evidence when needed, explains the decision, and triggers the response class.

This separation helped us avoid tight coupling. Each module can evolve independently as long as it respects the same input/output contract. It also made rollback safer: if one model version behaves poorly, we can revert that module without changing the entire pipeline.

A practical design choice was deterministic fallback. If Ollama or a tool path fails, the system still produces a rule-based action from fused risk. This means autonomy adds value but does not become a single operational dependency.

## IV. Data Pipeline and Feature Engineering

We found early that feature discipline mattered more than model novelty. Raw cloud counters were noisy, so we transformed network telemetry into window-based descriptors: rate change, burstiness, variance, and packet-flow irregularity indicators.

For UEBA, we captured behavior transitions rather than isolated events. Useful features included role-switch cadence, unusual API call sequences, privilege-use spread, and service novelty for each identity profile.

We also added environment context that helped reduce false alarms:

- criticality tier of target service
- whether the event happened during a maintenance/change window
- known automation identity flags
- recent incident density

Finally, we tagged low-quality windows (missing, delayed, or malformed records) and fed those tags into confidence handling. This prevented sparse telemetry from silently dominating high-impact actions.

## V. Fusion Logic and Response Policy

The fused risk is calculated as:

R_final = 0.6 * R_network + 0.4 * R_user

We tested alternatives during development, including near-equal weighting. In our scenario runs, 60/40 gave a better operational balance: faster response to infrastructure-side attacks with enough user context to avoid unnecessary hard blocks.

### Table I. Response thresholds

| Risk range | Level | Action |
|---|---|---|
| < 0.40 | LOW | LOG |
| 0.40-0.60 | MEDIUM | ALERT |
| 0.60-0.80 | HIGH | RATE_LIMIT |
| >= 0.80 | CRITICAL | BLOCK |

A key point is that the fused score is not the whole decision. It is the policy anchor. The agentic layer can request supporting evidence, but the allowed actions stay inside approved response classes.

## VI. Agentic Decision Layer

The agent follows a constrained Observe-Think-Act-Decide flow.

- Observe: read network risk, user risk, fused score, context, and confidence metadata.
- Think: determine if extra evidence is needed and pick tools from a whitelist.
- Act/Decide: produce action, confidence, and compact rationale.
- Reflect: store decision trace and outcome metadata for later analysis.

Implementation guardrails were important:

- maximum tool budget per cycle (to control latency and noisy chains)
- tool whitelist only (no arbitrary execution)
- explicit fallback to deterministic policy action if the LLM path fails
- structured logging of evidence, tool calls, and final justification

In the current code path, this safety posture is reflected by bounded tool calling and persistent storage in the decision layer.

## VII. Implementation Notes

The project is implemented in Python with modular components for IDS, UEBA, fusion, autonomous response, and dashboarding. Local LLM inference is handled through Ollama; this kept testing cost low and helped avoid external data exposure.

We intentionally designed deployment to be staged:

1. Detection-only mode
2. Assisted mode (agent explains but does not enforce)
3. Autonomous mode (policy-bound actions enabled)

This rollout model made evaluation and debugging more practical. During testing, when the model service was unavailable, rule-based fallback kept the system functional and auditable.

## VIII. Experimental Setup and Results

We used scenario-driven validation rather than only abstract model metrics, because our main goal was policy-correct action under realistic SOC pressure.

### Evaluated scenarios

1. Normal traffic baseline
2. Suspicious but non-critical behavior
3. DDoS-like high network anomaly with low user anomaly
4. Compromised-account pattern with high network and high user anomaly

### Table II. Scenario outcomes

| Scenario | Risk (N/U) | Fused | Output |
|---|---|---|---|
| Normal | 0.05 / 0.10 | 0.07 | LOG |
| Suspicious | 0.50 / 0.40 | 0.46 | ALERT |
| DDoS | 0.95 / 0.10 | 0.61 | RATE_LIMIT |
| Compromised | 0.95 / 0.90 | 0.93 | BLOCK |

The main behavior we cared about was contextual consistency. For example, high network risk alone should not always trigger full blocking. In the DDoS-like case, the system selected RATE_LIMIT, which matched policy intent and reduced unnecessary hard disruption. When both risk streams were high, the system escalated to BLOCK as expected.

Ablation-style checks also gave useful insight. Without memory feedback, we observed repeated false-positive patterns in similar contexts. Without tool calls, explanations became generic and less confidence-calibrated.

## IX. What Did Not Work Well Initially

Early iterations were too clean mathematically and too weak operationally. We saw three recurring issues:

1. Threshold-only decisions produced correct labels but poor analyst confidence when rationale was missing.
2. Unbounded reasoning attempts increased latency and occasionally overcomplicated simple cases.
3. Overly aggressive controls on medium confidence events caused avoidable service disruption.

These observations pushed us toward bounded tools, concise rationale templates, and safer escalation defaults.

## X. Limitations and Responsible Use

This system is not a silver bullet. Results were obtained in controlled scenarios and should not be interpreted as universal performance across all cloud environments.

Known limitations:

- threat patterns can drift over time, requiring periodic retuning
- telemetry quality varies by environment and affects confidence
- local LLM reasoning quality depends on model size and prompt discipline

Responsible operation requires human oversight, post-incident review, and explicit policy governance for high-impact actions.

## XI. Conclusion

This project demonstrates that practical autonomous response in cloud security is feasible when three pieces are co-designed: fused statistical detection, bounded reasoning, and policy-governed execution.

The contribution is not just higher detection sensitivity. It is better decision quality under operational constraints: faster triage, clearer explanations, safer action tiers, and resilient fallback behavior.

In short, the system moves from isolated anomaly scores to accountable, context-aware security decisions that can be reviewed and improved over time.

## References

[1] F. T. Liu, K. M. Ting, and Z.-H. Zhou, "Isolation Forest," IEEE ICDM, 2008.  
[2] S. Yao et al., "ReAct: Synergizing Reasoning and Acting in Language Models," ICLR, 2023.  
[3] S. Baral, S. Saha, and A. Haque, "Autonomous Cyber Incident Response Using Reasoning and Action," IEEE IWCMC, 2025.  
[4] X. Lin, G. Avina, and J. Santoyo, "Reducing False Alerts in Cybersecurity Threat Detection Using Generative AI," 2025.  
[5] C. Djidjev, "siForest: Detecting Network Anomalies with Set-Structured Isolation Forest," arXiv, 2025.  
[6] S. Zehra et al., "DeSFAM: AI-Driven Framework for Securing Cloud Containers," IEEE Access, 2025.  
[7] AWS, "CloudTrail User Guide," 2025.  
[8] NIST SP 800-94, "Guide to Intrusion Detection and Prevention Systems."  
[9] ENISA, "Threat Landscape Report," 2025.  
[10] MITRE ATT&CK for Enterprise, MITRE Corporation.
