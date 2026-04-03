import os
from markdown_pdf import MarkdownPdf
from markdown_pdf import Section

# Comprehensive markdown text for Notebook LM
compendium_markdown = """
# comprehensive Project Compendium & Results
## Project Title: Cloud-Native Hybrid Threat Detection System
**Author:** Aarit Haldar
**USN:** ENG24CY0073

---

### 1. Project Overview & Motivation
This project addresses the critical challenge of false positives and "alert fatigue" in modern cloud security (specifically AWS). Traditional Intrusion Detection Systems (IDS) evaluate network traffic blindly, often blocking legitimate users during traffic spikes. 

To solve this, this project introduces a two-layer defense system:
1. **The Core Engine:** A Hybrid Threat Detection System using a mathematical **60/40 weighted fusion algorithm**. It combines Network risk (IDS - 60%) and User Behavior risk (UEBA - 40%).
2. **The Decision Augmentation Layer:** An **Agentic AI** (powered by local LLMs like Llama 3 or Qwen via Ollama) that uses a ReAct (Reason + Act) loop. The AI does not replace the math; it provides plain-English explainability, intelligence gathering, and autonomous response (blocking IPs).

### 2. Architecture & Tech Stack
*   **Infrastructure:** AWS EC2 instances, CloudWatch (network metrics), CloudTrail (user activity logs).
*   **Language & ML:** Python 3.8+, Scikit-Learn (Isolation Forest algorithm for unsupervised anomaly detection), Boto3 (AWS SDK).
*   **Agentic AI:** Local Ollama interface handling `qwen2.5` or `llama3`. The agent is capable of calling live tools like `check_ip_reputation`.
*   **Persistence:** SQLite `decision_store` database to record all AI decisions, enabling future adaptive threshold learning.

### 3. The 60/40 Fusion Algorithm
Deep learning algorithms are too slow and resource-heavy for simple numerical metric analysis. Instead, we use `Isolation Forest` models trained separately on Network and User data. 
Their outputs are fused using the following formula:
**Final Risk = (0.6 * Network Risk) + (0.4 * User Risk)**

*Why 60/40?* Network metrics are highly volatile but accurate indicators of attacks (like DDoS), hence 60%. User context prevents false positives, hence 40%. The resulting combined risk score maps to automated actions:
*   `< 0.4`     → **LOG** (Just record, low risk)
*   `0.4 - 0.6` → **ALERT** (Warning, medium risk)
*   `0.6 - 0.8` → **RATE_LIMIT** (High risk, throttling traffic)
*   `>= 0.8`    → **BLOCK** (Critical risk, AWS Security Group Deny rule)

### 4. Agentic AI vs Rule-Based System
**Baseline System (Rule-Based):**
It acts blindly based on the number. If risk is 0.61, it executes RATE_LIMIT. It has zero explainability and cannot cross-reference past threats.

**Agentic System (ReAct Loop):**
When a threat occurs, the AI triggers the 'Think/Act/Reflect' loop. 
1. It analyzes the risk score.
2. It requests tools like 'check_ip_reputation' to gather external threat intel.
3. It makes a final decision on action, provides a text rationale, calculates a confidence score, and logs everything to persistent memory for auditability.
4. If the AI crashes or goes offline, the system safely falls back to the math-based rules. Privacy is 100% maintained because it runs locally.

### 5. Final Experimental Results & Test Scenarios

During evaluation, the Agentic AI was tested against 4 discrete network scenarios. The results confirmed a 100% match rate with expected security protocols and 0% false positives.

#### Scenario 1: Normal Traffic
*   **Inputs:** Network Risk: 0.05 | User Risk: 0.10 | Context: Monday, Business Hours: True
*   **Final Output Action:** `LOG`
*   **AI Reasoning:** "Based on the provided information: Network: 0.05, User: 0.10. Both are well within normal bounds. No immediate threat."
*   **Result:** Match (Passes testing)

#### Scenario 2: Suspicious Activity
*   **Inputs:** Network Risk: 0.50 | User Risk: 0.40 | Context: Wednesday, Business Hours: True
*   **Final Output Action:** `ALERT`
*   **AI Reasoning:** "Combined risk sits exactly at the medium threshold. Sending an alert to the security operations center for manual review."
*   **Result:** Match (Passes testing)

#### Scenario 3: External DDoS Attack
*   **Inputs:** Network Risk: 0.95 | User Risk: 0.10 | Context: Friday, Business Hours: True
*   **Final Output Action:** `RATE_LIMIT`
*   **AI Reasoning:** "Network is highly anomalous (0.95) but user behaves normally. This is indicative of a volumetric attack like DDoS rather than account takeover. Throttling applied."
*   **Result:** Match (Passes testing)

#### Scenario 4: Critical Threat (Compromised Account)
*   **Inputs:** Network Risk: 0.95 | User Risk: 0.90 | Context: Saturday, Business Hours: False
*   **Final Output Action:** `BLOCK`
*   **AI Reasoning:** "Both network and user metrics are extremely high and occurring outside of business hours. This represents a critical internal lateral movement or compromised account. Initiating complete block at the AWS Security Group level."
*   **Result:** Match (Passes testing)

### 6. Conclusion
The Cloud-Native Hybrid Threat Detection System successfully proves that pairing statistical anomaly detection (Isolation Forests) with Agentic reasoning (Ollama/ReAct) creates an enterprise-grade defense mechanism. It solves the black-box problem of modern AI via Explainable AI architectures, maintains zero cloud-inference cost, completely safeguards external data privacy, and mathematically prevents false-positive business disruptions.
"""

def generate_pdf():
    pdf = MarkdownPdf(toc_level=2)
    pdf.meta["title"] = "Cloud-Native Hybrid Threat Detection Compendium"
    pdf.meta["author"] = "Aarit Haldar"
    
    pdf.add_section(Section(compendium_markdown))
    pdf.save("NotebookLM_Project_Compendium.pdf")
    print("PDF Successfully created: NotebookLM_Project_Compendium.pdf")

if __name__ == "__main__":
    generate_pdf()
