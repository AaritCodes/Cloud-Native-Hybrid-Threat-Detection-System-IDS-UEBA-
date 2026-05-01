# 🛡️ Complete Setup Guide — Hybrid Threat Detection System

Everything you need to install and configure on a **fresh Windows laptop** to run this project.

---

## 1. System-Level Prerequisites (Install First)

| # | Software | Why Needed | Install Command / Link |
|---|----------|------------|------------------------|
| 1 | **Python 3.10+** | Core runtime | [python.org/downloads](https://www.python.org/downloads/) — ✅ tick "Add to PATH" |
| 2 | **Git** | Clone the repo | [git-scm.com](https://git-scm.com/download/win) |
| 3 | **AWS CLI v2** | AWS credentials & region setup | [AWS CLI installer](https://awscli.amazonaws.com/AWSCLIV2.msi) |
| 4 | **Ollama** *(optional)* | Local LLM for Agentic AI reasoning | [ollama.ai](https://ollama.ai/) |

> [!IMPORTANT]
> After installing Python, **restart your terminal** so `python` and `pip` are on your PATH.

---

## 2. Clone the Repository

```powershell
git clone https://github.com/AaritCodes/Cloud-Native-Hybrid-Threat-Detection-System-IDS-UEBA-.git
cd Cloud-Native-Hybrid-Threat-Detection-System-IDS-UEBA-
```

---

## 3. Create a Virtual Environment

```powershell
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your prompt.

---

## 4. Install Python Dependencies

### 4a. All-in-one (recommended)

```powershell
pip install -r requirements.txt
```

This installs **everything** listed below in one shot.

### 4b. Breakdown of what's inside `requirements.txt`

#### Core Dependencies (REQUIRED — the system won't run without these)

| Package | Version | Purpose |
|---------|---------|---------|
| `boto3` | ≥ 1.26.0 | AWS SDK — CloudWatch metrics, CloudTrail logs, EC2 Security Groups |
| `pandas` | ≥ 2.0.0 | Data manipulation for detection engines |
| `numpy` | ≥ 1.24.0 | Numerical computing for ML models |
| `scikit-learn` | ≥ 1.3.0 | Isolation Forest ML model (UEBA engine) |
| `joblib` | ≥ 1.3.0 | Loading pre-trained `.pkl` model files |
| `requests` | ≥ 2.31.0 | HTTP requests (Ollama API, N8N webhooks, attack simulator) |
| `python-dateutil` | ≥ 2.8.2 | Date/time utilities |

```powershell
pip install boto3 pandas numpy scikit-learn joblib requests python-dateutil
```

#### Dashboard Dependencies (REQUIRED for the Web UI)

| Package | Version | Purpose |
|---------|---------|---------|
| `flask` | ≥ 3.0.0 | Web dashboard server (`web_dashboard.py`) |
| `dash` | ≥ 2.14.0 | Alternative Plotly dashboard (`dashboard.py`) |
| `plotly` | ≥ 5.18.0 | Interactive charts in the Dash dashboard |
| `matplotlib` | ≥ 3.9.0 | Plot generation for model diagnostics |
| `seaborn` | ≥ 0.13.0 | Statistical visualization |

```powershell
pip install flask dash plotly matplotlib seaborn
```

#### LangChain RAG Dependencies (OPTIONAL — Threat Intelligence enrichment)

| Package | Version | Purpose |
|---------|---------|---------|
| `langchain` | ≥ 0.3.0 | RAG orchestration framework |
| `langchain-community` | ≥ 0.3.27 | ChromaDB & SentenceTransformer integrations |
| `chromadb` | ≥ 0.5.0 | Local vector store for threat intelligence |
| `sentence-transformers` | ≥ 2.2.0 | Embedding model (`all-MiniLM-L6-v2`) |

```powershell
pip install langchain langchain-community chromadb sentence-transformers
```

> [!NOTE]
> These are optional. The system falls back gracefully if not installed — RAG enrichment is simply skipped.

#### LangFuse Observability (OPTIONAL — LLM tracing)

| Package | Version | Purpose |
|---------|---------|---------|
| `langfuse` | ≥ 2.0.0 | Traces LLM calls, records quality scores |

```powershell
pip install langfuse
```

> [!NOTE]
> Also optional. Requires `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` environment variables to be set.

#### Python Standard Library (already included — no install needed)

These modules are used but come with Python:
`sqlite3`, `json`, `os`, `sys`, `threading`, `time`, `logging`, `datetime`, `collections`, `dataclasses`, `uuid`, `warnings`

---

## 5. AWS Configuration

> [!IMPORTANT]
> AWS credentials are **mandatory** — the entire system reads live data from AWS CloudWatch/CloudTrail and modifies Security Groups.

### 5a. Configure AWS CLI

```powershell
aws configure
```

Enter:
| Prompt | Value |
|--------|-------|
| AWS Access Key ID | Your IAM user access key |
| AWS Secret Access Key | Your IAM user secret key |
| Default region name | `ap-south-1` |
| Default output format | `json` |

### 5b. Required IAM Permissions

Your IAM user/role needs these permissions:

| Service | Permissions |
|---------|-------------|
| **CloudWatch** | `cloudwatch:GetMetricData`, `cloudwatch:GetMetricStatistics` |
| **CloudTrail** | `cloudtrail:LookupEvents` |
| **EC2** | `ec2:AuthorizeSecurityGroupIngress`, `ec2:RevokeSecurityGroupIngress`, `ec2:DescribeSecurityGroups` |

### 5c. Verify AWS Setup

```powershell
aws sts get-caller-identity
```

You should see your account ID, user ARN, etc.

### 5d. PEM Key (if SSH-ing to EC2)

Place your `.pem` key file (e.g. `Aarit.pem`) in the project root.

---

## 6. Ollama Setup (Optional — for Agentic AI)

### 6a. Install Ollama

Download from [ollama.ai](https://ollama.ai/) and install.

### 6b. Pull a Model

```powershell
ollama pull qwen2.5:0.5b
```

Other supported models: `phi3:mini`, `llama3`, `mistral`

### 6c. Start Ollama Server

```powershell
ollama serve
```

> [!TIP]
> If Ollama is not running, the system automatically falls back to **rule-based decisions** — no crash.

---

## 7. Environment Variables (Optional)

| Variable | Purpose | Default |
|----------|---------|---------|
| `OLLAMA_URL` | Ollama API endpoint | `http://localhost:11434` |
| `OLLAMA_MODEL` | LLM model to use | `qwen2.5:0.5b` |
| `N8N_WEBHOOK_URL` | N8N automation webhook | *(disabled if empty)* |
| `RAG_PERSIST_DIR` | ChromaDB storage directory | `.chroma_db` |
| `RAG_ENABLED` | Enable/disable RAG | `true` |
| `LANGFUSE_PUBLIC_KEY` | LangFuse project public key | *(disabled if empty)* |
| `LANGFUSE_SECRET_KEY` | LangFuse project secret key | *(disabled if empty)* |
| `LANGFUSE_HOST` | LangFuse API host | `https://cloud.langfuse.com` |

Set them in PowerShell:
```powershell
$env:OLLAMA_URL = "http://localhost:11434"
$env:OLLAMA_MODEL = "qwen2.5:0.5b"
```

---

## 8. Configuration Files

Copy the template and fill in your values:

```powershell
copy config\integration_config.json.template config\integration_config.json
copy config\alert_config.json.template config\alert_config.json
```

Edit `config/alert_config.json` with your SMTP/email settings if you want email alerts.

---

## 9. Running the System

### Terminal 1 — Start Ollama (optional)
```powershell
ollama serve
```

### Terminal 2 — Start Main Detection Engine
```powershell
cd "C:\Users\aarit\Downloads\unified threat detection"
venv\Scripts\activate
python src\enhanced_main_with_agent.py
```

### Terminal 3 — Start Web Dashboard
```powershell
cd "C:\Users\aarit\Downloads\unified threat detection"
venv\Scripts\activate
python src\web_dashboard.py
```
Open **http://localhost:5000** in your browser.

### Terminal 4 — Run Attack Simulation (demo)
```powershell
cd "C:\Users\aarit\Downloads\unified threat detection"
venv\Scripts\activate
python tests\attack_simulator.py
```

---

## 10. Quick Verification Checklist

| Check | Command |
|-------|---------|
| Python installed | `python --version` → should be 3.10+ |
| Pip works | `pip --version` |
| AWS configured | `aws sts get-caller-identity` |
| Ollama running | `curl http://localhost:11434/api/tags` |
| Venv activated | Look for `(venv)` in prompt |
| Dependencies OK | `pip list` — check for boto3, flask, scikit-learn, etc. |
| System starts | `python src\enhanced_main_with_agent.py` — no import errors |

---

## Summary — Minimum vs Full Install

| Tier | What You Get | Packages to Install |
|------|-------------|---------------------|
| **Minimum** | Detection + Dashboard + Rule-based response | `boto3 pandas numpy scikit-learn joblib requests python-dateutil flask` |
| **+ AI Reasoning** | Above + Ollama Agentic AI | + Ollama app + `ollama pull qwen2.5:0.5b` |
| **+ RAG** | Above + Threat Intel enrichment | + `langchain langchain-community chromadb sentence-transformers` |
| **+ Observability** | Above + LLM call tracing | + `langfuse` |
| **Full** | Everything | `pip install -r requirements.txt` + Ollama + AWS CLI |
