# N8N + LangChain RAG + LangFuse Integration Guide

This document describes how the Hybrid Threat Detection System is fused with
three powerful external platforms:

| Platform | Role |
|----------|------|
| **N8N** | Workflow automation – route threat alerts to Slack, JIRA, PagerDuty, SIEM |
| **LangChain RAG** | Retrieval-Augmented Generation – enrich LLM prompts with threat intelligence |
| **LangFuse** | LLM observability – trace, monitor, and score every AI decision |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│  Existing Hybrid Threat Detection System                            │
│                                                                     │
│  IDS Engine (CloudWatch) ──┐                                        │
│                             ├──► Threat Fusion Engine (60/40)       │
│  UEBA Engine (CloudTrail) ─┘           │                           │
│                                        │ threat_level, risks        │
│                                        ▼                           │
│                             ┌─────────────────────┐               │
│                             │  IntegrationPipeline │               │
│                             │  (src/integration_   │               │
│                             │   pipeline.py)        │               │
│                             └────────┬────────────┘               │
│                                      │                              │
│              ┌───────────────────────┼───────────────────────┐    │
│              ▼                       ▼                        ▼    │
│       ┌────────────┐        ┌──────────────┐        ┌──────────┐  │
│       │  LangChain │        │   LangFuse   │        │   N8N    │  │
│       │  RAG       │        │  Observer    │        │  Client  │  │
│       │  (vector   │        │  (trace LLM  │        │  (webhook│  │
│       │  store)    │        │   calls)     │        │   push)  │  │
│       └────────────┘        └──────────────┘        └──────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Threat detected** – IDS + UEBA scores are combined by the fusion engine.
2. **RAG enrichment** – `ThreatIntelRAG.enrich()` queries a local ChromaDB
   vector store and returns the most relevant threat-intel paragraphs (DDoS
   patterns, MITRE ATT&CK techniques, remediation steps, etc.).
3. **LLM analysis** – The Ollama agent receives a RAG-augmented prompt and
   returns a recommended action (LOG / ALERT / RATE_LIMIT / BLOCK).
   The entire call is wrapped in a **LangFuse generation span**.
4. **N8N notification** – A JSON payload is POSTed to the configured N8N
   webhook, triggering downstream workflows (Slack DM, JIRA ticket, etc.).
5. **Feedback loop** – When an analyst confirms a decision (true/false
   positive), `pipeline.record_outcome()` sends a quality score to LangFuse
   for continuous model monitoring.

---

## Quick Start

### 1. Install Dependencies

```bash
# Core integration packages
pip install langchain langchain-community>=0.3.27 chromadb sentence-transformers langfuse

# Or install everything at once
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file (never commit this to git):

```bash
# N8N
N8N_WEBHOOK_URL=https://your-n8n.example.com/webhook/threat-detection

# LangFuse
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com   # omit if using cloud.langfuse.com

# Ollama (already running locally)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:0.5b

# RAG vector store location (optional)
RAG_PERSIST_DIR=.chroma_db
```

### 3. Use the Integration Pipeline

Add the pipeline to your detection loop in `enhanced_main.py`:

```python
from src.integration_pipeline import IntegrationPipeline
from src.threat_fusion_engine import combine_risks

# Initialise once
pipeline = IntegrationPipeline()

# Inside run_detection_cycle():
final_risk, level = combine_risks(network_risk, user_risk)

if final_risk > 0.3:
    trace_id = pipeline.start_cycle(metadata={"cycle": self.stats["total_cycles"]})
    result = pipeline.process_threat(
        threat_level=level,
        final_risk=final_risk,
        network_risk=network_risk,
        user_risk=user_risk,
        ip_address=ip,
        network_bytes=network_bytes,
        network_packets=network_packets,
        parent_trace_id=trace_id,
    )
    pipeline.end_cycle(trace_id, threats_detected=1)
    print(f"AI Action: {result['action']} | N8N sent: {result['n8n_sent']}")

# On shutdown:
pipeline.shutdown()
```

### 4. Disable Individual Integrations

Each integration can be disabled without code changes:

```bash
# Disable N8N
N8N_ENABLED=false python src/enhanced_main.py

# Disable RAG
RAG_ENABLED=false python src/enhanced_main.py

# Disable LangFuse
LANGFUSE_ENABLED=false python src/enhanced_main.py

# Disable all integrations at once
INTEGRATION_ENABLED=false python src/enhanced_main.py
```

---

## N8N Setup

### Creating a Threat Alert Workflow

1. Open your N8N instance (`http://localhost:5678` for local installs).
2. Create a **New Workflow**.
3. Add a **Webhook** trigger node:
   - Method: `POST`
   - Path: `/threat-detection`
   - Copy the generated URL → set as `N8N_WEBHOOK_URL`.
4. Add downstream nodes, for example:
   - **Slack** → post to `#security-alerts` channel.
   - **JIRA** → create a ticket with `threat_level` as priority.
   - **PagerDuty** → page on-call for CRITICAL alerts.
   - **HTTP Request** → forward to SIEM / Splunk / Elastic.
5. Use an **IF** node to filter by `threat_level` (e.g. only page for CRITICAL).

### Webhook Payload Shape

```json
{
  "event_type": "threat_alert",
  "timestamp": "2026-04-08T12:34:56+00:00",
  "threat_level": "HIGH",
  "final_risk": 0.72,
  "network_risk": 0.80,
  "user_risk": 0.40,
  "ip_address": "EC2_INSTANCE",
  "network_bytes": 1200000,
  "network_packets": 14500,
  "context": {
    "rag_context": "DDoS mitigation: block the source…",
    "ai_action": "RATE_LIMIT",
    "ai_reasoning": "Sustained high network risk."
  }
}
```

For `block_ip` events:

```json
{
  "event_type": "block_ip",
  "timestamp": "...",
  "action": "BLOCK",
  "ip_address": "203.0.113.42",
  "risk_score": 0.91,
  "reasoning": "DDoS detected.",
  "duration_minutes": 60
}
```

---

## LangChain RAG Setup

The RAG module ships with a built-in threat-intelligence knowledge base that
covers:

- DDoS / SYN flood / application-layer attacks
- Insider threat patterns
- Credential compromise / account takeover
- Ransomware indicators in cloud environments
- Port scanning / reconnaissance
- Lateral movement in AWS
- Graduated response procedures
- AWS security best practices
- MITRE ATT&CK cloud techniques

### Adding Custom Threat Intelligence

```python
from src.rag_threat_intel import ThreatIntelRAG

rag = ThreatIntelRAG()

# Add CISA advisory or vendor bulletin
rag.add_documents([
    """CVE-2026-XXXX – Apache Log4j Remote Code Execution:
    Affected versions: 2.0-beta9 to 2.14.1. Attacker sends a crafted
    JNDI lookup string in any logged field. Mitigation: upgrade to 2.17.1+
    or set log4j2.formatMsgNoLookups=true."""
])
```

### Vector Store Persistence

The ChromaDB vector store is persisted to `.chroma_db/` (configurable via
`RAG_PERSIST_DIR`). On the first run it embeds all seed documents using the
`all-MiniLM-L6-v2` SentenceTransformer model (~22 MB, downloaded once).
Subsequent runs load the existing store instantly.

---

## LangFuse Setup

### Cloud (Recommended)

1. Sign up at [cloud.langfuse.com](https://cloud.langfuse.com) (free tier
   supports up to 50k observations/month).
2. Create a project → copy **Public Key** and **Secret Key**.
3. Set `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY`.

### Self-Hosted

```bash
# Docker Compose (from LangFuse docs)
git clone https://github.com/langfuse/langfuse.git
cd langfuse
docker compose up -d
# Access at http://localhost:3000
```

Set `LANGFUSE_HOST=http://localhost:3000`.

### What Gets Traced

| Span | Name | Contents |
|------|------|----------|
| Trace | `detection_cycle_N` | Full cycle metadata |
| Generation | `rag_threat_analysis` | RAG-augmented prompt + LLM response |
| Score | `true_positive` / `false_positive` | Quality feedback from analyst |

### Scoring Decisions

```python
# After analyst confirms the threat was real
pipeline.record_outcome(
    trace_id=result["trace_id"],
    outcome="true_positive",
    value=1.0,
    comment="Confirmed DDoS from firewall logs.",
)

# After analyst marks a false positive
pipeline.record_outcome(
    trace_id=result["trace_id"],
    outcome="false_positive",
    value=0.0,
    comment="Legitimate backup job, not an attack.",
)
```

---

## Testing

Run the integration unit tests (no external services required):

```bash
python -m pytest tests/test_integration_pipeline.py -v
```

Run all tests:

```bash
python -m pytest tests/ -v
```

---

## Troubleshooting

### N8N

| Problem | Solution |
|---------|----------|
| `N8NClient: no webhook URL configured` | Set `N8N_WEBHOOK_URL` env var |
| `N8N webhook returned HTTP 404` | Verify the webhook path in N8N matches the URL |
| Alerts not appearing in N8N | Check that the workflow is **Active** in N8N |

### LangChain RAG

| Problem | Solution |
|---------|----------|
| `LangChain / ChromaDB not installed` | `pip install langchain langchain-community>=0.3.27 chromadb` |
| Slow first run | First run downloads the embedding model (~22 MB) |
| `Permission denied` on `.chroma_db/` | Change `RAG_PERSIST_DIR` to a writable directory |

### LangFuse

| Problem | Solution |
|---------|----------|
| `LANGFUSE_PUBLIC_KEY not set` | Set the env var; traces will be silently skipped otherwise |
| Events not appearing in dashboard | Call `pipeline.shutdown()` to flush pending events |
| `Connection refused` on self-hosted | Verify `LANGFUSE_HOST` and that the container is running |

---

## File Reference

| File | Description |
|------|-------------|
| `src/n8n_integration.py` | N8N webhook HTTP client |
| `src/rag_threat_intel.py` | LangChain RAG vector store and enrichment |
| `src/langfuse_observer.py` | LangFuse LLM observability layer |
| `src/integration_pipeline.py` | Unified pipeline tying all three together |
| `config/integration_config.json.template` | Configuration template |
| `tests/test_integration_pipeline.py` | Unit tests for all integration modules |
| `requirements.txt` | Updated with optional integration packages |
