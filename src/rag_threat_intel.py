"""
LangChain RAG – Threat Intelligence Enrichment

Builds a local, persistent vector store (ChromaDB) seeded with threat
intelligence knowledge and exposes a single helper,
``ThreatIntelRAG.enrich()``, that retrieves the most relevant context
chunks for a given threat event.

The retrieved context is injected into the LLM prompt so the agent can
reason with up-to-date attack patterns and remediation guidance.

Dependencies (optional)
-----------------------
    pip install langchain>=0.3.0 langchain-community>=0.3.27 chromadb>=0.5.0

When these packages are not installed the module gracefully falls back to
returning an empty context string; the rest of the pipeline is unaffected.

Usage
-----
    from src.rag_threat_intel import ThreatIntelRAG

    rag = ThreatIntelRAG()           # builds/loads the vector store once
    context = rag.enrich(
        threat_level="HIGH",
        network_risk=0.82,
        user_risk=0.35,
        ip_address="203.0.113.42",
    )
    print(context)

Environment Variables
---------------------
    RAG_PERSIST_DIR   – Directory for ChromaDB persistence (default: ./.chroma_db)
    RAG_TOP_K         – Number of chunks to retrieve per query (default: 3)
    RAG_ENABLED       – Set to "false" to disable without changing code
"""

from __future__ import annotations

import logging
import os
from typing import List, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Optional-import guard
# ─────────────────────────────────────────────────────────────────────────────

try:
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import SentenceTransformerEmbeddings
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document

    _LANGCHAIN_AVAILABLE = True
except ImportError:
    _LANGCHAIN_AVAILABLE = False
    logger.info(
        "LangChain / ChromaDB not installed – RAG enrichment disabled. "
        "Install with: pip install langchain langchain-community chromadb"
    )

# ─────────────────────────────────────────────────────────────────────────────
# Threat intelligence knowledge base (static seed documents)
# ─────────────────────────────────────────────────────────────────────────────

_THREAT_INTEL_DOCS: List[str] = [
    # ── DDoS / volumetric attacks ────────────────────────────────────────────
    """DDoS (Distributed Denial of Service) Attack Patterns:
Volumetric DDoS attacks flood the target with massive amounts of traffic,
exhausting bandwidth. Common signatures include a sudden spike in
NetworkIn bytes (>1 million bytes/5 min), high packet counts
(>10,000 packets/5 min), and a high bytes-per-packet ratio suggesting
UDP flood. Recommended response: rate-limit or block the offending
source at the network perimeter immediately. Use AWS WAF or Security
Groups to add an ingress deny rule. Contact upstream ISP for BGP
blackholing in extreme cases.""",

    """SYN Flood Attack:
A SYN flood sends a barrage of TCP SYN packets without completing
the handshake, exhausting the server's half-open connection table.
Indicators: very high packet counts, low bytes-per-packet (<100 bytes),
network risk > 0.7. Mitigation: Enable SYN cookies on the EC2 instance
(sysctl net.ipv4.tcp_syncookies=1), use AWS Shield Standard, apply
NACLs to block the source subnet.""",

    """HTTP/HTTPS Application Layer DDoS:
Targets web servers with large numbers of HTTP GET/POST requests.
Harder to distinguish from legitimate traffic. Indicators: high request
rate, user risk elevation due to unusual API patterns, correlation of
network and behavioral anomalies. Response: enable AWS WAF rate-based
rules, deploy Amazon CloudFront, investigate CloudTrail for API abuse.""",

    # ── Insider / UEBA patterns ──────────────────────────────────────────────
    """Insider Threat Patterns:
Insiders typically exhibit: unusual access times (midnight/weekends),
bulk data downloads (high NetworkOut), access to sensitive resources
outside normal scope, and privilege escalation attempts visible in
CloudTrail as AssumeRole or CreateUser API calls. User risk > 0.6
combined with low network risk suggests insider activity rather than
external attack.""",

    """Credential Compromise / Account Takeover:
Signs include: logins from new geographies, rapid API calls across
multiple services, attempts to disable CloudTrail logging, and access
key exfiltration patterns. CloudTrail events to watch: ConsoleLogin from
unusual IP, CreateAccessKey, PutUserPolicy, DeleteTrail. Response:
revoke affected keys immediately, enable MFA, review IAM policy changes.""",

    # ── Ransomware / malware ─────────────────────────────────────────────────
    """Ransomware Indicators in Cloud Environments:
Early indicators: large numbers of S3 GetObject/PutObject calls (data
staging), unusual KMS decrypt activity, EC2 instance store writes
spiking. Network side: high outbound traffic as data is exfiltrated.
Response: isolate the instance (remove from security group), snapshot EBS
volumes for forensics, activate incident response runbook, notify AWS
Security.""",

    # ── Port scanning / reconnaissance ───────────────────────────────────────
    """Network Reconnaissance and Port Scanning:
Low-volume but broad connection attempts across many ports from a single
IP. Network risk is moderate (0.3–0.6); packet counts elevated relative
to bytes. Often precedes a focused attack. Response: block the scanning
IP in Security Groups, review VPC flow logs for scope, update threat
intelligence feeds.""",

    # ── Lateral movement ─────────────────────────────────────────────────────
    """Lateral Movement in AWS:
After initial compromise attackers move laterally using: EC2 instance
metadata service (IMDS) to steal instance role credentials, VPC peering
misconfigurations, or compromised IAM roles. Indicators: inter-VPC
traffic spikes, IAM AssumeRole chains, unusual Describe* API calls across
regions. Mitigation: enforce IMDSv2, least-privilege IAM, enable AWS
GuardDuty for cross-account anomaly detection.""",

    # ── Response procedures ──────────────────────────────────────────────────
    """Graduated Threat Response Procedure:
- Risk < 0.4 (LOW): Log event, continue monitoring.
- Risk 0.4–0.6 (MEDIUM): Alert security team, increase monitoring frequency.
- Risk 0.6–0.8 (HIGH): Rate-limit source, open incident ticket, notify on-call.
- Risk > 0.8 (CRITICAL): Block source immediately via Security Group,
  page incident commander, begin forensic collection, consider instance
  isolation.
Always document every action taken in the incident log for post-incident
review and regulatory compliance.""",

    """AWS Security Best Practices:
1. Enable CloudTrail in all regions with log file validation.
2. Use VPC Flow Logs for network-level forensics.
3. Enable AWS Config for configuration drift detection.
4. Apply least-privilege IAM policies; rotate access keys every 90 days.
5. Use AWS Security Hub for aggregated findings.
6. Enable Amazon GuardDuty for ML-based threat detection.
7. Implement MFA for all IAM users.
8. Use AWS Shield Advanced for DDoS protection on critical workloads.""",

    # ── MITRE ATT&CK cloud techniques ────────────────────────────────────────
    """MITRE ATT&CK Cloud Techniques (summary):
T1078 – Valid Accounts: adversaries use stolen credentials.
T1098 – Account Manipulation: adding keys or permissions.
T1526 – Cloud Service Discovery: enumerating cloud resources.
T1530 – Data from Cloud Storage: S3 bucket exfiltration.
T1537 – Transfer Data to Cloud Account: exfil to attacker-owned bucket.
T1562 – Impair Defenses: disabling CloudTrail/GuardDuty.
Detection: monitor CloudTrail for these API patterns and correlate with
network anomalies for high-fidelity alerts.""",
]


class ThreatIntelRAG:
    """
    RAG-based threat intelligence enrichment using LangChain + ChromaDB.

    The vector store is built once from ``_THREAT_INTEL_DOCS`` and persisted
    to disk so subsequent runs avoid re-embedding.

    Parameters
    ----------
    persist_dir:
        Directory where ChromaDB stores its data.
    top_k:
        Number of document chunks to return per query.
    embedding_model:
        SentenceTransformer model name for embedding.
        ``all-MiniLM-L6-v2`` is fast (~20 MB) and works offline.
    """

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        top_k: int = 3,
        embedding_model: str = "all-MiniLM-L6-v2",
    ) -> None:
        self.persist_dir: str = persist_dir or os.environ.get(
            "RAG_PERSIST_DIR", ".chroma_db"
        )
        self.top_k: int = int(os.environ.get("RAG_TOP_K", top_k))
        self.enabled: bool = (
            _LANGCHAIN_AVAILABLE
            and os.environ.get("RAG_ENABLED", "true").lower() != "false"
        )
        self._vectorstore: Optional[object] = None

        if self.enabled:
            try:
                self._vectorstore = self._build_or_load(embedding_model)
                logger.info("ThreatIntelRAG: vector store ready (%s)", self.persist_dir)
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("ThreatIntelRAG: failed to initialise vector store: %s", exc)
                self.enabled = False

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def enrich(
        self,
        threat_level: str = "MEDIUM",
        network_risk: float = 0.5,
        user_risk: float = 0.5,
        ip_address: str = "",
        query_override: Optional[str] = None,
    ) -> str:
        """
        Return a string of relevant threat intelligence context.

        Parameters
        ----------
        threat_level:   Detected threat level string (LOW/MEDIUM/HIGH/CRITICAL).
        network_risk:   Numeric risk score from the IDS engine (0-1).
        user_risk:      Numeric risk score from the UEBA engine (0-1).
        ip_address:     Source IP (used to build a richer query).
        query_override: Provide a custom retrieval query instead of auto-building one.

        Returns
        -------
        A plain-text string with the retrieved context, ready to inject into
        an LLM prompt. Returns an empty string when RAG is disabled or fails.
        """
        if not self.enabled or self._vectorstore is None:
            return ""

        query = query_override or self._build_query(
            threat_level, network_risk, user_risk, ip_address
        )

        try:
            docs: List[Document] = self._vectorstore.similarity_search(
                query, k=self.top_k
            )
            if not docs:
                return ""

            chunks = [d.page_content.strip() for d in docs]
            header = "=== Threat Intelligence Context (RAG) ==="
            footer = "=" * len(header)
            return "\n".join([header, *chunks, footer])

        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("ThreatIntelRAG.enrich() failed: %s", exc)
            return ""

    def add_documents(self, texts: List[str]) -> None:
        """
        Add new threat intelligence documents to the vector store at runtime.

        This allows the system to ingest fresh threat feeds (e.g. CISA alerts,
        vendor bulletins) without rebuilding the entire store.
        """
        if not self.enabled or self._vectorstore is None:
            logger.warning("ThreatIntelRAG: cannot add documents – RAG is disabled.")
            return

        docs = _texts_to_documents(texts)
        self._vectorstore.add_documents(docs)
        logger.info("ThreatIntelRAG: added %d document(s) to vector store.", len(docs))

    # ─────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _build_or_load(self, embedding_model: str):
        """Return existing Chroma store or create a new one from seed docs."""
        embeddings = SentenceTransformerEmbeddings(model_name=embedding_model)

        # If persist_dir already contains a Chroma database, load it
        chroma_meta = os.path.join(self.persist_dir, "chroma.sqlite3")
        if os.path.exists(chroma_meta):
            logger.info(
                "ThreatIntelRAG: loading existing vector store from %s",
                self.persist_dir,
            )
            return Chroma(
                persist_directory=self.persist_dir,
                embedding_function=embeddings,
            )

        # Otherwise build from seed documents
        logger.info(
            "ThreatIntelRAG: building new vector store in %s", self.persist_dir
        )
        docs = _texts_to_documents(_THREAT_INTEL_DOCS)
        return Chroma.from_documents(
            documents=docs,
            embedding=embeddings,
            persist_directory=self.persist_dir,
        )

    @staticmethod
    def _build_query(
        threat_level: str,
        network_risk: float,
        user_risk: float,
        ip_address: str,
    ) -> str:
        """Construct a natural-language retrieval query from threat metrics."""
        parts = [f"Threat level: {threat_level}."]

        if network_risk > 0.7:
            parts.append("High network anomaly, possible DDoS or port scan.")
        elif network_risk > 0.4:
            parts.append("Moderate network traffic anomaly.")

        if user_risk > 0.7:
            parts.append("High user behaviour anomaly, possible insider threat or credential compromise.")
        elif user_risk > 0.4:
            parts.append("Moderate user behaviour deviation.")

        if network_risk > 0.7 and user_risk > 0.5:
            parts.append("Combined high risk – coordinated attack likely.")

        return " ".join(parts)


# ─────────────────────────────────────────────────────────────────────────────
# Module-level helpers
# ─────────────────────────────────────────────────────────────────────────────

def _texts_to_documents(texts: List[str]) -> "List[Document]":
    """Split raw text strings into LangChain Document chunks."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=80)
    docs: List[Document] = []
    for text in texts:
        chunks = splitter.split_text(text)
        docs.extend([Document(page_content=c) for c in chunks])
    return docs


# ─────────────────────────────────────────────────────────────────────────────
# Quick smoke-test
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    rag = ThreatIntelRAG()

    if rag.enabled:
        result = rag.enrich(
            threat_level="HIGH",
            network_risk=0.85,
            user_risk=0.30,
            ip_address="203.0.113.42",
        )
        print(result if result else "(no context retrieved)")
    else:
        print(
            "RAG is disabled. Install langchain, langchain-community, chromadb "
            "to enable it:\n"
            "  pip install langchain langchain-community>=0.3.27 chromadb"
        )
