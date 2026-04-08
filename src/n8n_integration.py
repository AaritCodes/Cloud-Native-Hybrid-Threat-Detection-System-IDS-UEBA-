"""
N8N Workflow Integration for Hybrid Threat Detection System

Sends structured threat events to N8N via webhooks so that N8N can
orchestrate downstream automations (Slack/Teams notifications, JIRA
ticket creation, PagerDuty escalations, SIEM ingestion, etc.).

All HTTP calls are non-blocking and errors are silently logged so
that a missing or unreachable N8N instance never disrupts detection.

Usage
-----
    from src.n8n_integration import N8NClient

    client = N8NClient(webhook_url="https://your-n8n.example.com/webhook/threat-detection")
    client.send_threat_alert(
        threat_level="HIGH",
        final_risk=0.72,
        network_risk=0.80,
        user_risk=0.40,
        ip_address="EC2_INSTANCE",
        network_bytes=1_200_000,
        network_packets=14_500,
        extra_context={"rag_context": "...", "ai_reasoning": "..."},
    )

Environment Variables
---------------------
    N8N_WEBHOOK_URL  – Base webhook URL (overrides the constructor argument)
    N8N_TIMEOUT      – HTTP timeout in seconds (default: 5)
    N8N_ENABLED      – Set to "false" to disable without changing code
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import requests

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Event type constants
# ─────────────────────────────────────────────────────────────────────────────

EVENT_THREAT_ALERT = "threat_alert"
EVENT_BLOCK_IP = "block_ip"
EVENT_RATE_LIMIT = "rate_limit"
EVENT_SYSTEM_START = "system_start"
EVENT_SYSTEM_STOP = "system_stop"
EVENT_DETECTION_CYCLE = "detection_cycle"


class N8NClient:
    """
    Lightweight HTTP client for pushing events to one or more N8N webhook URLs.

    Parameters
    ----------
    webhook_url:
        Default webhook endpoint (can be overridden per-call or via env var).
    timeout:
        Seconds before an HTTP request is abandoned (default 5).
    enabled:
        When False every send_* call is a no-op (useful for local dev/CI).
    """

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        timeout: int = 5,
        enabled: bool = True,
    ) -> None:
        self.webhook_url: str = (
            webhook_url
            or os.environ.get("N8N_WEBHOOK_URL", "")
        )
        self.timeout: int = int(os.environ.get("N8N_TIMEOUT", timeout))
        self.enabled: bool = (
            os.environ.get("N8N_ENABLED", "true").lower() != "false"
            and enabled
        )

        if self.enabled and not self.webhook_url:
            logger.warning(
                "N8NClient: no webhook URL configured. "
                "Set N8N_WEBHOOK_URL or pass webhook_url= to the constructor. "
                "N8N integration is disabled until a URL is provided."
            )
            self.enabled = False

    # ─────────────────────────────────────────────────────────────────────────
    # Public helpers
    # ─────────────────────────────────────────────────────────────────────────

    def send_threat_alert(
        self,
        threat_level: str,
        final_risk: float,
        network_risk: float,
        user_risk: float,
        ip_address: str = "EC2_INSTANCE",
        network_bytes: float = 0,
        network_packets: float = 0,
        extra_context: Optional[Dict[str, Any]] = None,
        webhook_url: Optional[str] = None,
    ) -> bool:
        """
        Fire a *threat_alert* event to N8N.

        Returns True when the webhook accepted the payload (HTTP 2xx),
        False otherwise (no exception is raised).
        """
        payload: Dict[str, Any] = {
            "event_type": EVENT_THREAT_ALERT,
            "timestamp": _utc_now(),
            "threat_level": threat_level,
            "final_risk": round(final_risk, 4),
            "network_risk": round(network_risk, 4),
            "user_risk": round(user_risk, 4),
            "ip_address": ip_address,
            "network_bytes": network_bytes,
            "network_packets": network_packets,
        }
        if extra_context:
            payload["context"] = extra_context

        return self._post(payload, webhook_url)

    def send_response_action(
        self,
        action: str,
        ip_address: str,
        risk_score: float,
        reasoning: str = "",
        duration_minutes: int = 0,
        webhook_url: Optional[str] = None,
    ) -> bool:
        """
        Notify N8N that the autonomous agent took a response action
        (BLOCK, RATE_LIMIT, ALERT, LOG).
        """
        event_type = EVENT_BLOCK_IP if action == "BLOCK" else (
            EVENT_RATE_LIMIT if action == "RATE_LIMIT" else EVENT_THREAT_ALERT
        )
        payload: Dict[str, Any] = {
            "event_type": event_type,
            "timestamp": _utc_now(),
            "action": action,
            "ip_address": ip_address,
            "risk_score": round(risk_score, 4),
            "reasoning": reasoning,
            "duration_minutes": duration_minutes,
        }
        return self._post(payload, webhook_url)

    def send_system_event(
        self,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        webhook_url: Optional[str] = None,
    ) -> bool:
        """
        Send a generic system lifecycle event (start, stop, cycle stats).
        """
        payload: Dict[str, Any] = {
            "event_type": event_type,
            "timestamp": _utc_now(),
        }
        if metadata:
            payload["metadata"] = metadata
        return self._post(payload, webhook_url)

    # ─────────────────────────────────────────────────────────────────────────
    # Internal
    # ─────────────────────────────────────────────────────────────────────────

    def _post(
        self,
        payload: Dict[str, Any],
        override_url: Optional[str] = None,
    ) -> bool:
        """POST *payload* as JSON to the configured (or overridden) webhook URL."""
        if not self.enabled:
            return False

        url = override_url or self.webhook_url
        if not url:
            return False

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"},
            )
            if response.ok:
                logger.debug(
                    "N8N webhook accepted event '%s' (HTTP %s)",
                    payload.get("event_type"),
                    response.status_code,
                )
                return True

            logger.warning(
                "N8N webhook returned HTTP %s for event '%s': %s",
                response.status_code,
                payload.get("event_type"),
                response.text[:200],
            )
            return False

        except requests.exceptions.Timeout:
            logger.warning(
                "N8N webhook timed out after %ss (event: %s)",
                self.timeout,
                payload.get("event_type"),
            )
        except requests.exceptions.ConnectionError as exc:
            logger.warning("N8N webhook connection error: %s", exc)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("N8N webhook unexpected error: %s", exc)

        return False


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _utc_now() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(tz=timezone.utc).isoformat()


# ─────────────────────────────────────────────────────────────────────────────
# Quick smoke-test
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # Replace with your N8N webhook URL to run a live test
    TEST_URL = os.environ.get("N8N_WEBHOOK_URL", "")

    client = N8NClient(webhook_url=TEST_URL or None)

    if client.enabled:
        ok = client.send_threat_alert(
            threat_level="HIGH",
            final_risk=0.72,
            network_risk=0.80,
            user_risk=0.40,
            extra_context={"source": "smoke_test"},
        )
        print(f"Threat alert sent: {ok}")

        ok = client.send_response_action(
            action="RATE_LIMIT",
            ip_address="203.0.113.42",
            risk_score=0.72,
            reasoning="Sustained high network risk.",
            duration_minutes=15,
        )
        print(f"Response action sent: {ok}")
    else:
        print("N8N integration disabled (no webhook URL). Set N8N_WEBHOOK_URL to test.")
