"""
Unified Integration Pipeline
N8N  ×  LangChain RAG  ×  LangFuse  →  Hybrid Threat Detection System

This module is the single integration point that wires together:

    ┌──────────────────────────────────────────────────────────────┐
    │  Threat Event (IDS + UEBA risks)                             │
    │         │                                                     │
    │         ▼                                                     │
    │  [1] LangFuse – open detection-cycle trace                   │
    │         │                                                     │
    │         ▼                                                     │
    │  [2] RAG – retrieve threat-intel context from ChromaDB       │
    │         │                                                     │
    │         ▼                                                     │
    │  [3] LLM (Ollama / fallback) – analyse threat with context   │
    │     (wrapped in LangFuse generation span)                    │
    │         │                                                     │
    │         ▼                                                     │
    │  [4] N8N – fire webhook for downstream workflow automation   │
    │         │                                                     │
    │         ▼                                                     │
    │  [5] LangFuse – close trace; score on feedback               │
    └──────────────────────────────────────────────────────────────┘

Usage (standalone)
------------------
    from src.integration_pipeline import IntegrationPipeline

    pipeline = IntegrationPipeline()          # reads env vars for config
    result = pipeline.process_threat(
        threat_level="HIGH",
        final_risk=0.72,
        network_risk=0.80,
        user_risk=0.40,
        ip_address="EC2_INSTANCE",
        network_bytes=1_200_000,
        network_packets=14_500,
    )
    print(result["action"], result["reasoning"])

    # Optional: record outcome for LangFuse scoring
    pipeline.record_outcome(
        trace_id=result["trace_id"],
        outcome="true_positive",
        value=1.0,
    )

    pipeline.shutdown()   # flush LangFuse, etc.

Drop-in replacement inside ``enhanced_main.py``
------------------------------------------------
Replace::

    # Combine risks
    final_risk, level = combine_risks(network_risk, user_risk)

With::

    final_risk, level = combine_risks(network_risk, user_risk)
    pipeline.process_threat(level, final_risk, network_risk, user_risk, ip=ip)

Environment Variables
---------------------
    N8N_WEBHOOK_URL        – N8N webhook endpoint
    LANGFUSE_PUBLIC_KEY    – LangFuse public key
    LANGFUSE_SECRET_KEY    – LangFuse secret key
    OLLAMA_URL             – Ollama base URL (default http://localhost:11434)
    OLLAMA_MODEL           – Ollama model name (default qwen2.5:0.5b)
    RAG_PERSIST_DIR        – ChromaDB persist directory
    INTEGRATION_ENABLED    – Set to "false" to disable all integrations
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Lazy imports so that missing optional dependencies don't crash on import
# ─────────────────────────────────────────────────────────────────────────────

def _import_n8n():
    try:
        from src.n8n_integration import N8NClient
    except ModuleNotFoundError:
        from n8n_integration import N8NClient
    return N8NClient


def _import_rag():
    try:
        from src.rag_threat_intel import ThreatIntelRAG
    except ModuleNotFoundError:
        from rag_threat_intel import ThreatIntelRAG
    return ThreatIntelRAG


def _import_langfuse():
    try:
        from src.langfuse_observer import LangFuseObserver
    except ModuleNotFoundError:
        from langfuse_observer import LangFuseObserver
    return LangFuseObserver


def _import_ollama():
    try:
        from src.ollama_agent import OllamaAgent
    except ModuleNotFoundError:
        from ollama_agent import OllamaAgent
    return OllamaAgent


# ─────────────────────────────────────────────────────────────────────────────
# Pipeline
# ─────────────────────────────────────────────────────────────────────────────

class IntegrationPipeline:
    """
    Orchestrates N8N, LangChain RAG, and LangFuse around every threat event.

    Parameters
    ----------
    n8n_webhook_url:
        N8N webhook URL (overrides N8N_WEBHOOK_URL env var).
    langfuse_public_key / langfuse_secret_key:
        LangFuse credentials (override env vars).
    rag_persist_dir:
        Directory for ChromaDB (overrides RAG_PERSIST_DIR env var).
    ollama_model:
        Ollama model name (overrides OLLAMA_MODEL env var).
    enabled:
        Master on/off switch.
    """

    def __init__(
        self,
        n8n_webhook_url: Optional[str] = None,
        langfuse_public_key: Optional[str] = None,
        langfuse_secret_key: Optional[str] = None,
        rag_persist_dir: Optional[str] = None,
        ollama_model: Optional[str] = None,
        enabled: bool = True,
    ) -> None:
        self.enabled: bool = (
            enabled
            and os.environ.get("INTEGRATION_ENABLED", "true").lower() != "false"
        )

        # ── N8N ──────────────────────────────────────────────────────────────
        N8NClient = _import_n8n()
        self.n8n = N8NClient(webhook_url=n8n_webhook_url)

        # ── RAG ──────────────────────────────────────────────────────────────
        ThreatIntelRAG = _import_rag()
        self.rag = ThreatIntelRAG(persist_dir=rag_persist_dir)

        # ── LangFuse ─────────────────────────────────────────────────────────
        LangFuseObserver = _import_langfuse()
        self.langfuse = LangFuseObserver(
            public_key=langfuse_public_key,
            secret_key=langfuse_secret_key,
        )

        # ── Ollama (optional LLM for RAG-augmented analysis) ─────────────────
        self._ollama_agent = None
        self._ollama_model: str = (
            ollama_model
            or os.environ.get("OLLAMA_MODEL", "qwen2.5:0.5b")
        )
        self._cycle_counter: int = 0

        logger.info(
            "IntegrationPipeline ready | N8N=%s | RAG=%s | LangFuse=%s",
            self.n8n.enabled,
            self.rag.enabled,
            self.langfuse.enabled,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def start_cycle(self, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Call at the beginning of each detection cycle.

        Returns a ``trace_id`` that should be passed to ``process_threat``
        and ``end_cycle`` so all events within a cycle are grouped in LangFuse.
        """
        self._cycle_counter += 1
        trace_id = self.langfuse.start_detection_cycle(
            cycle_number=self._cycle_counter,
            metadata=metadata,
        )
        return trace_id

    def end_cycle(
        self,
        trace_id: str,
        threats_detected: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Call at the end of each detection cycle to close the LangFuse trace."""
        self.langfuse.end_detection_cycle(
            trace_id=trace_id,
            threats_detected=threats_detected,
            metadata=metadata,
        )
        # Send cycle summary to N8N
        self.n8n.send_system_event(
            "detection_cycle",
            metadata={
                "cycle_number": self._cycle_counter,
                "threats_detected": threats_detected,
                **(metadata or {}),
            },
        )

    def process_threat(
        self,
        threat_level: str,
        final_risk: float,
        network_risk: float,
        user_risk: float,
        ip_address: str = "EC2_INSTANCE",
        network_bytes: float = 0,
        network_packets: float = 0,
        parent_trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Full integration pipeline for a single threat event.

        Steps
        -----
        1. Retrieve RAG context (threat intelligence enrichment).
        2. Run LLM analysis with RAG context injected into the prompt.
        3. Send N8N alert webhook.
        4. Return enriched result dict.

        Parameters
        ----------
        threat_level:   Threat level string (LOW/MEDIUM/HIGH/CRITICAL).
        final_risk:     Combined risk score from the fusion engine.
        network_risk:   Raw IDS risk score.
        user_risk:      Raw UEBA risk score.
        ip_address:     Source IP or instance identifier.
        network_bytes:  Traffic volume in bytes.
        network_packets: Packet count.
        parent_trace_id: LangFuse trace ID from ``start_cycle()`` if available.

        Returns
        -------
        Dict with keys: action, confidence, reasoning, rag_context,
        trace_id, n8n_sent.
        """
        start_ts = time.monotonic()

        # Step 1 – RAG enrichment ─────────────────────────────────────────────
        rag_context = self.rag.enrich(
            threat_level=threat_level,
            network_risk=network_risk,
            user_risk=user_risk,
            ip_address=ip_address,
        )

        # Step 2 – LLM analysis with RAG context ──────────────────────────────
        llm_result = self._run_llm_with_observability(
            threat_level=threat_level,
            final_risk=final_risk,
            network_risk=network_risk,
            user_risk=user_risk,
            ip_address=ip_address,
            rag_context=rag_context,
            parent_trace_id=parent_trace_id,
        )

        # Step 3 – N8N alert ───────────────────────────────────────────────────
        n8n_ok = self.n8n.send_threat_alert(
            threat_level=threat_level,
            final_risk=final_risk,
            network_risk=network_risk,
            user_risk=user_risk,
            ip_address=ip_address,
            network_bytes=network_bytes,
            network_packets=network_packets,
            extra_context={
                "rag_context": rag_context[:500] if rag_context else "",
                "ai_action": llm_result.get("action", ""),
                "ai_reasoning": llm_result.get("reasoning", ""),
            },
        )

        # Step 4 – also fire response-action event for non-LOG actions ────────
        action = llm_result.get("action", "LOG")
        if action in ("BLOCK", "RATE_LIMIT", "ALERT"):
            self.n8n.send_response_action(
                action=action,
                ip_address=ip_address,
                risk_score=final_risk,
                reasoning=llm_result.get("reasoning", ""),
            )

        elapsed_ms = int((time.monotonic() - start_ts) * 1000)
        logger.info(
            "IntegrationPipeline.process_threat completed in %dms | "
            "level=%s risk=%.2f action=%s n8n=%s",
            elapsed_ms,
            threat_level,
            final_risk,
            action,
            n8n_ok,
        )

        return {
            "action": action,
            "confidence": llm_result.get("confidence", 0.7),
            "reasoning": llm_result.get("reasoning", ""),
            "rag_context": rag_context,
            "trace_id": llm_result.get("trace_id", ""),
            "n8n_sent": n8n_ok,
            "elapsed_ms": elapsed_ms,
        }

    def record_outcome(
        self,
        trace_id: str,
        outcome: str,
        value: float,
        comment: str = "",
    ) -> None:
        """
        Feed back a decision outcome to LangFuse for quality scoring.

        Call this whenever you later confirm whether a threat was real or a
        false positive (e.g. from analyst review or SOC ticketing system).

        Parameters
        ----------
        trace_id:   Returned by ``process_threat`` in ``result["trace_id"]``.
        outcome:    ``"true_positive"``, ``"false_positive"``,
                    ``"true_negative"``, or ``"missed_attack"``.
        value:      Quality score in [0, 1].
        comment:    Free-text explanation.
        """
        self.langfuse.score_decision(trace_id, outcome, value, comment)

    def shutdown(self) -> None:
        """Flush all pending LangFuse events before process exit."""
        self.langfuse.flush()
        logger.info("IntegrationPipeline shut down.")

    # ─────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _get_ollama_agent(self):
        """Lazy-load the Ollama agent (avoids start-up cost when Ollama is down)."""
        if self._ollama_agent is None:
            try:
                OllamaAgent = _import_ollama()
                self._ollama_agent = OllamaAgent(model=self._ollama_model)
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning(
                    "IntegrationPipeline: could not initialise OllamaAgent: %s", exc
                )
        return self._ollama_agent

    def _run_llm_with_observability(
        self,
        threat_level: str,
        final_risk: float,
        network_risk: float,
        user_risk: float,
        ip_address: str,
        rag_context: str,
        parent_trace_id: Optional[str],
    ) -> Dict[str, Any]:
        """
        Build a RAG-augmented prompt, call the LLM, and wrap the call in a
        LangFuse generation span.

        Falls back gracefully when Ollama or LangFuse is unavailable.
        """
        prompt = _build_rag_augmented_prompt(
            threat_level, final_risk, network_risk, user_risk, ip_address, rag_context
        )

        metadata = {
            "threat_level": threat_level,
            "final_risk": round(final_risk, 4),
            "network_risk": round(network_risk, 4),
            "user_risk": round(user_risk, 4),
        }

        with self.langfuse.observe_llm_call(
            name="rag_threat_analysis",
            prompt=prompt,
            model=self._ollama_model,
            metadata=metadata,
            parent_trace_id=parent_trace_id,
        ) as ctx:
            agent = self._get_ollama_agent()
            if agent is not None:
                start = time.monotonic()
                try:
                    result = agent.analyze_and_decide(
                        network_risk=network_risk,
                        user_risk=user_risk,
                        ip_address=ip_address,
                        context={"rag_context": rag_context[:1000]},
                    )
                    elapsed = int((time.monotonic() - start) * 1000)
                    ctx.set_output(
                        f"Action: {result.get('action')} | "
                        f"Reasoning: {result.get('reasoning', '')[:200]}"
                    )
                    result["trace_id"] = ctx.trace_id
                    result["llm_latency_ms"] = elapsed
                    return result
                except Exception as exc:  # pylint: disable=broad-except
                    logger.warning("LLM call failed in pipeline: %s", exc)
                    ctx.set_output(f"ERROR: {exc}")

            # Fallback – rule-based decision when Ollama is unavailable
            fallback = _rule_based_decision(final_risk)
            ctx.set_output(f"FALLBACK Action: {fallback['action']}")
            fallback["trace_id"] = ctx.trace_id
            return fallback


# ─────────────────────────────────────────────────────────────────────────────
# Prompt builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_rag_augmented_prompt(
    threat_level: str,
    final_risk: float,
    network_risk: float,
    user_risk: float,
    ip_address: str,
    rag_context: str,
) -> str:
    """Return a prompt that embeds retrieved threat-intel context."""
    context_section = (
        f"\n\nTHREAT INTELLIGENCE CONTEXT (retrieved via RAG):\n{rag_context}\n"
        if rag_context
        else ""
    )
    return (
        f"You are a cybersecurity AI agent. Analyse the following threat and "
        f"recommend one of: LOG, ALERT, RATE_LIMIT, BLOCK.\n\n"
        f"THREAT DATA:\n"
        f"  Threat Level : {threat_level}\n"
        f"  Combined Risk: {final_risk:.2f}\n"
        f"  Network Risk : {network_risk:.2f}\n"
        f"  User Risk    : {user_risk:.2f}\n"
        f"  Source       : {ip_address}"
        f"{context_section}\n"
        f"Respond with: Action: [ACTION]"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Rule-based fallback
# ─────────────────────────────────────────────────────────────────────────────

def _rule_based_decision(final_risk: float) -> Dict[str, Any]:
    """Return a deterministic decision when the LLM is unavailable."""
    if final_risk >= 0.8:
        action, reasoning = "BLOCK", "Critical risk – immediate block required."
    elif final_risk >= 0.6:
        action, reasoning = "RATE_LIMIT", "High risk – rate-limiting applied."
    elif final_risk >= 0.4:
        action, reasoning = "ALERT", "Medium risk – security team notified."
    else:
        action, reasoning = "LOG", "Low risk – event logged for review."

    return {
        "action": action,
        "confidence": 0.7,
        "reasoning": reasoning,
        "risk_assessment": "CRITICAL" if final_risk >= 0.8 else (
            "HIGH" if final_risk >= 0.6 else (
                "MEDIUM" if final_risk >= 0.4 else "LOW"
            )
        ),
        "agent_type": "rule_based_fallback",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Quick smoke-test
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)

    pipeline = IntegrationPipeline()

    trace_id = pipeline.start_cycle(metadata={"test": True})

    result = pipeline.process_threat(
        threat_level="HIGH",
        final_risk=0.72,
        network_risk=0.80,
        user_risk=0.40,
        ip_address="EC2_INSTANCE",
        network_bytes=1_200_000,
        network_packets=14_500,
        parent_trace_id=trace_id,
    )

    pipeline.end_cycle(trace_id, threats_detected=1)

    print("\n=== Integration Pipeline Result ===")
    for k, v in result.items():
        if k == "rag_context":
            print(f"  rag_context: {'<populated>' if v else '<empty>'}")
        else:
            print(f"  {k}: {v}")

    pipeline.shutdown()
