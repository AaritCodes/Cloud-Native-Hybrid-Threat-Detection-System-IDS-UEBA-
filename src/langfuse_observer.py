"""
LangFuse Observability Layer for the Hybrid Threat Detection System

Wraps every LLM call (Ollama / OpenAI) with LangFuse tracing so you get:
  • Full prompt / response capture
  • Token usage and latency metrics
  • Per-decision quality scores (fed back after outcome is known)
  • Session-level traces for each detection cycle

The module is entirely optional – when LangFuse is not installed or
LANGFUSE_ENABLED=false, all public helpers become no-ops and return
neutral values so the rest of the pipeline continues unaffected.

Dependencies (optional)
-----------------------
    pip install langfuse>=2.0.0

Usage
-----
    from src.langfuse_observer import LangFuseObserver

    obs = LangFuseObserver()

    # Wrap a single LLM call
    trace_id, generation_id = obs.start_llm_trace(
        name="threat_analysis",
        prompt="Analyze this threat...",
        model="qwen2.5:0.5b",
        metadata={"network_risk": 0.85, "threat_level": "HIGH"},
    )
    response = call_llm(prompt)           # your existing LLM call
    obs.end_llm_trace(
        trace_id=trace_id,
        generation_id=generation_id,
        output=response,
        latency_ms=250,
    )

    # Later, when the outcome is known, score the decision
    obs.score_decision(trace_id, outcome="true_positive", value=1.0)

Environment Variables
---------------------
    LANGFUSE_PUBLIC_KEY   – LangFuse project public key
    LANGFUSE_SECRET_KEY   – LangFuse project secret key
    LANGFUSE_HOST         – LangFuse API host (default: https://cloud.langfuse.com)
    LANGFUSE_ENABLED      – Set to "false" to disable without changing code
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Optional-import guard
# ─────────────────────────────────────────────────────────────────────────────

try:
    from langfuse import Langfuse  # type: ignore

    _LANGFUSE_AVAILABLE = True
except ImportError:
    _LANGFUSE_AVAILABLE = False
    logger.info(
        "LangFuse not installed – observability disabled. "
        "Install with: pip install langfuse"
    )


class LangFuseObserver:
    """
    Thin wrapper around the LangFuse Python SDK.

    All methods are safe to call even when LangFuse is unavailable or
    misconfigured – they simply return placeholder values and log a warning.

    Parameters
    ----------
    public_key:
        LangFuse project public key (can also be set via LANGFUSE_PUBLIC_KEY).
    secret_key:
        LangFuse project secret key (can also be set via LANGFUSE_SECRET_KEY).
    host:
        LangFuse API host.  Defaults to the cloud offering.
    enabled:
        Hard-disable switch (useful for unit tests / CI).
    """

    def __init__(
        self,
        public_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        host: Optional[str] = None,
        enabled: bool = True,
    ) -> None:
        self._public_key = public_key or os.environ.get("LANGFUSE_PUBLIC_KEY", "")
        self._secret_key = secret_key or os.environ.get("LANGFUSE_SECRET_KEY", "")
        self._host = host or os.environ.get(
            "LANGFUSE_HOST", "https://cloud.langfuse.com"
        )
        self.enabled: bool = (
            _LANGFUSE_AVAILABLE
            and enabled
            and os.environ.get("LANGFUSE_ENABLED", "true").lower() != "false"
            and bool(self._public_key)
            and bool(self._secret_key)
        )

        self._client: Optional[Langfuse] = None
        # In-memory store mapping trace_id → Langfuse trace object
        self._traces: Dict[str, Any] = {}

        if self.enabled:
            try:
                self._client = Langfuse(
                    public_key=self._public_key,
                    secret_key=self._secret_key,
                    host=self._host,
                )
                logger.info(
                    "LangFuseObserver: connected to %s", self._host
                )
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning(
                    "LangFuseObserver: failed to initialise client: %s. "
                    "Observability disabled.",
                    exc,
                )
                self.enabled = False
        else:
            if not self._public_key or not self._secret_key:
                logger.info(
                    "LangFuseObserver: LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY "
                    "not set – observability disabled."
                )

    # ─────────────────────────────────────────────────────────────────────────
    # Trace lifecycle
    # ─────────────────────────────────────────────────────────────────────────

    def start_detection_cycle(
        self,
        cycle_number: int,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Open a LangFuse *trace* for a complete detection cycle.

        Returns a ``trace_id`` string that should be threaded through all
        subsequent spans/generations in the same cycle.
        """
        trace_id = str(uuid.uuid4())

        if not self.enabled or self._client is None:
            return trace_id

        try:
            trace = self._client.trace(
                id=trace_id,
                name=f"detection_cycle_{cycle_number}",
                metadata={
                    "cycle_number": cycle_number,
                    **(metadata or {}),
                },
                tags=["threat_detection", "ids", "ueba"],
            )
            self._traces[trace_id] = trace
            logger.debug("LangFuse trace started: %s", trace_id)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("LangFuse start_detection_cycle error: %s", exc)

        return trace_id

    def end_detection_cycle(
        self,
        trace_id: str,
        threats_detected: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Close (update) the detection-cycle trace with summary metrics."""
        if not self.enabled or trace_id not in self._traces:
            return
        try:
            trace = self._traces[trace_id]
            trace.update(
                output={
                    "threats_detected": threats_detected,
                    **(metadata or {}),
                }
            )
            self._traces.pop(trace_id, None)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("LangFuse end_detection_cycle error: %s", exc)

    # ─────────────────────────────────────────────────────────────────────────
    # LLM call tracing
    # ─────────────────────────────────────────────────────────────────────────

    def start_llm_trace(
        self,
        name: str,
        prompt: str,
        model: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
        parent_trace_id: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Record the *start* of an LLM call.

        Returns
        -------
        (trace_id, generation_id) – both are UUIDs that must be passed to
        ``end_llm_trace`` so the span can be closed.
        """
        trace_id = parent_trace_id or str(uuid.uuid4())
        generation_id = str(uuid.uuid4())

        if not self.enabled or self._client is None:
            return trace_id, generation_id

        try:
            # Reuse existing trace or create a new one
            if trace_id not in self._traces:
                trace = self._client.trace(
                    id=trace_id,
                    name=name,
                    metadata=metadata or {},
                    tags=["llm", "threat_analysis"],
                )
                self._traces[trace_id] = trace
            else:
                trace = self._traces[trace_id]

            generation = trace.generation(
                id=generation_id,
                name=name,
                model=model,
                input=prompt,
                metadata=metadata or {},
                start_time=datetime.now(tz=timezone.utc),
            )
            # Store generation on the trace object for retrieval in end_llm_trace
            if not hasattr(trace, "_generations"):
                trace._generations = {}
            trace._generations[generation_id] = generation

            logger.debug(
                "LangFuse generation started: trace=%s gen=%s",
                trace_id,
                generation_id,
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("LangFuse start_llm_trace error: %s", exc)

        return trace_id, generation_id

    def end_llm_trace(
        self,
        trace_id: str,
        generation_id: str,
        output: str,
        latency_ms: int = 0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record the *end* of an LLM call (close the generation span)."""
        if not self.enabled:
            return

        trace = self._traces.get(trace_id)
        if trace is None:
            return

        try:
            generations: Dict[str, Any] = getattr(trace, "_generations", {})
            generation = generations.get(generation_id)
            if generation is None:
                return

            generation.end(
                output=output,
                end_time=datetime.now(tz=timezone.utc),
                usage={
                    "input": prompt_tokens,
                    "output": completion_tokens,
                    "total": prompt_tokens + completion_tokens,
                },
                metadata={
                    "latency_ms": latency_ms,
                    **(metadata or {}),
                },
            )
            logger.debug(
                "LangFuse generation ended: trace=%s gen=%s latency=%dms",
                trace_id,
                generation_id,
                latency_ms,
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("LangFuse end_llm_trace error: %s", exc)

    # ─────────────────────────────────────────────────────────────────────────
    # Decision scoring
    # ─────────────────────────────────────────────────────────────────────────

    def score_decision(
        self,
        trace_id: str,
        outcome: str,
        value: float,
        comment: str = "",
    ) -> None:
        """
        Attach a quality *score* to a completed trace.

        Parameters
        ----------
        trace_id:
            The trace produced by ``start_llm_trace`` or ``start_detection_cycle``.
        outcome:
            Short label, e.g. ``"true_positive"``, ``"false_positive"``,
            ``"true_negative"``, ``"missed_attack"``.
        value:
            Numeric score in [0, 1].  1.0 = correct decision, 0.0 = wrong.
        comment:
            Free-text explanation for the score.
        """
        if not self.enabled or self._client is None:
            return

        try:
            self._client.score(
                trace_id=trace_id,
                name=outcome,
                value=value,
                comment=comment or f"Outcome: {outcome}",
            )
            logger.debug(
                "LangFuse score recorded: trace=%s outcome=%s value=%.2f",
                trace_id,
                outcome,
                value,
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("LangFuse score_decision error: %s", exc)

    # ─────────────────────────────────────────────────────────────────────────
    # Context-manager convenience wrapper
    # ─────────────────────────────────────────────────────────────────────────

    def observe_llm_call(
        self,
        name: str,
        prompt: str,
        model: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
        parent_trace_id: Optional[str] = None,
    ) -> "_ObserveContext":
        """
        Context manager for instrumenting an LLM call with a single ``with`` block.

        Example
        -------
            with obs.observe_llm_call("threat_analysis", prompt, model="phi3") as ctx:
                response = call_ollama(prompt)
                ctx.set_output(response)
        """
        return _ObserveContext(
            observer=self,
            name=name,
            prompt=prompt,
            model=model,
            metadata=metadata,
            parent_trace_id=parent_trace_id,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Flush
    # ─────────────────────────────────────────────────────────────────────────

    def flush(self) -> None:
        """Flush pending events to LangFuse (call on application shutdown)."""
        if self.enabled and self._client is not None:
            try:
                self._client.flush()
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("LangFuse flush error: %s", exc)


# ─────────────────────────────────────────────────────────────────────────────
# Context manager helper
# ─────────────────────────────────────────────────────────────────────────────

class _ObserveContext:
    """Internal context manager returned by ``LangFuseObserver.observe_llm_call``."""

    def __init__(
        self,
        observer: LangFuseObserver,
        name: str,
        prompt: str,
        model: str,
        metadata: Optional[Dict[str, Any]],
        parent_trace_id: Optional[str],
    ) -> None:
        self._obs = observer
        self._name = name
        self._prompt = prompt
        self._model = model
        self._metadata = metadata
        self._parent_trace_id = parent_trace_id
        self._trace_id: str = ""
        self._generation_id: str = ""
        self._output: str = ""
        self._start_ms: float = 0.0

    def __enter__(self) -> "_ObserveContext":
        self._start_ms = time.monotonic() * 1000
        self._trace_id, self._generation_id = self._obs.start_llm_trace(
            name=self._name,
            prompt=self._prompt,
            model=self._model,
            metadata=self._metadata,
            parent_trace_id=self._parent_trace_id,
        )
        return self

    def set_output(self, output: str) -> None:
        """Call inside the ``with`` block to record the LLM response."""
        self._output = output

    @property
    def trace_id(self) -> str:
        return self._trace_id

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        latency = int(time.monotonic() * 1000 - self._start_ms)
        self._obs.end_llm_trace(
            trace_id=self._trace_id,
            generation_id=self._generation_id,
            output=self._output or ("ERROR: " + str(exc_val) if exc_type else ""),
            latency_ms=latency,
        )
        return False  # do not suppress exceptions


# ─────────────────────────────────────────────────────────────────────────────
# Quick smoke-test
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    obs = LangFuseObserver()

    if obs.enabled:
        trace_id, gen_id = obs.start_llm_trace(
            name="smoke_test",
            prompt="Is this traffic a DDoS attack?",
            model="phi3:mini",
            metadata={"test": True},
        )
        time.sleep(0.05)
        obs.end_llm_trace(
            trace_id=trace_id,
            generation_id=gen_id,
            output="Action: BLOCK. High network risk.",
            latency_ms=50,
        )
        obs.score_decision(trace_id, "true_positive", 1.0, "Confirmed DDoS")
        obs.flush()
        print("LangFuse smoke-test complete. Check your LangFuse dashboard.")
    else:
        print(
            "LangFuse observability is disabled.\n"
            "Set LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY to enable it."
        )
