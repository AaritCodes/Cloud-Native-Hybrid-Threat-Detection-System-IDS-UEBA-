"""
Agent Tools — callable functions the agentic AI can invoke
during its reasoning loop to gather information.

Each tool is a plain function that returns a dict.
The ReAct agent picks which tools to call based on its reasoning.

Author: Aarit Haldar
Date: March 2026
"""

import logging
import json
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ────────────────────────────────────────────────────────────────────
# Lazy import: DecisionStore is imported inside functions so that
# the module can be imported without side-effects.
# ────────────────────────────────────────────────────────────────────

_decision_store = None


def _get_store():
    """Lazy-load the DecisionStore singleton."""
    global _decision_store
    if _decision_store is None:
        try:
            from src.decision_store import DecisionStore
        except ModuleNotFoundError:
            from decision_store import DecisionStore
        _decision_store = DecisionStore()
    return _decision_store


# ════════════════════════════════════════════════════════════════════
# TOOL DEFINITIONS — each dict describes the tool for the LLM prompt
# ════════════════════════════════════════════════════════════════════

TOOL_DEFINITIONS = [
    {
        "name": "check_ip_reputation",
        "description": (
            "Look up the reputation and history of an IP address. "
            "Returns past events, blocks, average risk, and a reputation "
            "score (0 = malicious, 1 = benign)."
        ),
        "parameters": {"ip_address": "string — the IP to look up"},
    },
    {
        "name": "get_attack_history",
        "description": (
            "Retrieve past threat decisions for a specific IP address. "
            "Shows what actions were taken before and their outcomes."
        ),
        "parameters": {"ip_address": "string — the IP to query", "limit": "int — max results (default 10)"},
    },
    {
        "name": "get_similar_threats",
        "description": (
            "Find past decisions with similar network_risk and user_risk "
            "scores. Useful for seeing how similar situations were handled."
        ),
        "parameters": {
            "network_risk": "float 0-1",
            "user_risk": "float 0-1",
        },
    },
    {
        "name": "get_network_baseline",
        "description": (
            "Get the current network traffic baseline and recent threat "
            "statistics. Helps assess whether current traffic is abnormal."
        ),
        "parameters": {},
    },
    {
        "name": "correlate_recent_events",
        "description": (
            "Find all threat events in the last N minutes. Useful for "
            "detecting coordinated or multi-vector attacks."
        ),
        "parameters": {"minutes": "int — look-back window (default 60)"},
    },
    {
        "name": "get_accuracy_stats",
        "description": (
            "Get the agent's historical accuracy metrics (precision, "
            "recall, F1). Helps calibrate confidence in decisions."
        ),
        "parameters": {},
    },
    {
        "name": "get_adaptive_thresholds",
        "description": (
            "Get suggested risk thresholds adjusted based on past "
            "false-positive and missed-attack rates."
        ),
        "parameters": {},
    },
    {
        "name": "check_ip_external",
        "description": (
            "Query an external threat intelligence API (AbuseIPDB) for "
            "an IP address. Requires ABUSEIPDB_API_KEY env var."
        ),
        "parameters": {"ip_address": "string — the IP to check externally"},
    },
]


# ════════════════════════════════════════════════════════════════════
# TOOL IMPLEMENTATIONS
# ════════════════════════════════════════════════════════════════════


def check_ip_reputation(ip_address: str) -> Dict:
    """
    Look up internal reputation for an IP.

    Returns:
        Reputation profile or a 'not found' message.
    """
    store = _get_store()
    rep = store.get_ip_reputation(ip_address)
    if not rep:
        return {
            "ip_address": ip_address,
            "status": "unknown",
            "message": "IP not seen before. No historical data.",
            "reputation_score": 0.5,
        }

    return {
        "ip_address": ip_address,
        "status": "known",
        "first_seen": rep.get("first_seen"),
        "last_seen": rep.get("last_seen"),
        "total_events": rep.get("total_events", 0),
        "total_blocks": rep.get("total_blocks", 0),
        "total_alerts": rep.get("total_alerts", 0),
        "avg_risk": rep.get("avg_risk", 0.0),
        "max_risk": rep.get("max_risk", 0.0),
        "reputation_score": rep.get("reputation_score", 0.5),
        "assessment": _interpret_reputation(rep.get("reputation_score", 0.5)),
    }


def get_attack_history(ip_address: str, limit: int = 10) -> Dict:
    """
    Retrieve past decisions for an IP.
    """
    store = _get_store()
    decisions = store.get_ip_decisions(ip_address, limit=limit)
    if not decisions:
        return {
            "ip_address": ip_address,
            "total_past_decisions": 0,
            "message": "No past decisions found for this IP.",
        }

    summary = []
    for d in decisions:
        summary.append({
            "timestamp": d["timestamp"],
            "action": d["action"],
            "final_risk": d["final_risk"],
            "outcome": d.get("outcome", "pending"),
            "reasoning": d.get("reasoning", ""),
        })

    return {
        "ip_address": ip_address,
        "total_past_decisions": len(decisions),
        "history": summary,
    }


def get_similar_threats(network_risk: float, user_risk: float) -> Dict:
    """
    Find similar past threats by risk scores.
    """
    store = _get_store()
    decisions = store.get_similar_decisions(network_risk, user_risk)
    if not decisions:
        return {
            "query": {"network_risk": network_risk, "user_risk": user_risk},
            "total_similar": 0,
            "message": "No similar threats found in history.",
        }

    # Group by action to see what was done in similar cases
    action_counts: Dict[str, int] = {}
    outcome_counts: Dict[str, int] = {}
    for d in decisions:
        action_counts[d["action"]] = action_counts.get(d["action"], 0) + 1
        outcome = d.get("outcome") or "pending"
        outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1

    return {
        "query": {"network_risk": network_risk, "user_risk": user_risk},
        "total_similar": len(decisions),
        "action_distribution": action_counts,
        "outcome_distribution": outcome_counts,
        "most_common_action": max(action_counts, key=action_counts.get),
        "sample_decisions": [
            {
                "timestamp": d["timestamp"],
                "action": d["action"],
                "final_risk": d["final_risk"],
                "outcome": d.get("outcome", "pending"),
            }
            for d in decisions[:5]
        ],
    }


def get_network_baseline() -> Dict:
    """
    Get network traffic baseline & recent activity summary.
    """
    store = _get_store()
    recent = store.get_recent_decisions(hours=1)
    all_time = store.get_total_decisions()

    if not recent:
        return {
            "status": "quiet",
            "recent_events_1h": 0,
            "total_events_all_time": all_time,
            "message": "No recent threat events. Network appears normal.",
        }

    risks = [d["final_risk"] for d in recent]
    actions = [d["action"] for d in recent]
    unique_ips = list(set(d["ip_address"] for d in recent))

    return {
        "status": "active" if len(recent) > 5 else "normal",
        "recent_events_1h": len(recent),
        "total_events_all_time": all_time,
        "avg_risk_1h": round(sum(risks) / len(risks), 4),
        "max_risk_1h": round(max(risks), 4),
        "unique_ips_1h": unique_ips,
        "actions_1h": {a: actions.count(a) for a in set(actions)},
        "assessment": "Elevated activity" if len(recent) > 5 else "Normal activity",
    }


def correlate_recent_events(minutes: int = 60) -> Dict:
    """
    Correlate events in the last N minutes to detect coordinated attacks.
    """
    store = _get_store()
    hours = max(minutes / 60, 0.1)
    recent = store.get_recent_decisions(hours=int(hours) or 1)

    # Filter to exact minute window
    cutoff = datetime.now() - timedelta(minutes=minutes)
    filtered = [d for d in recent if d["timestamp"] >= cutoff.isoformat()]

    if not filtered:
        return {
            "window_minutes": minutes,
            "total_events": 0,
            "message": "No events in the specified window.",
        }

    ips = [d["ip_address"] for d in filtered]
    unique_ips = list(set(ips))
    actions = [d["action"] for d in filtered]

    # Detect coordinated patterns
    is_coordinated = len(unique_ips) > 3 and len(filtered) > 5
    has_escalation = "BLOCK" in actions and "ALERT" in actions

    return {
        "window_minutes": minutes,
        "total_events": len(filtered),
        "unique_source_ips": unique_ips,
        "actions": {a: actions.count(a) for a in set(actions)},
        "is_potentially_coordinated": is_coordinated,
        "has_escalation_pattern": has_escalation,
        "assessment": "Possible coordinated attack" if is_coordinated else "Independent events",
    }


def get_accuracy_stats() -> Dict:
    """
    Get agent decision accuracy statistics.
    """
    store = _get_store()
    return store.get_accuracy_stats()


def get_adaptive_thresholds() -> Dict:
    """
    Get suggested risk thresholds based on historical accuracy.
    """
    store = _get_store()
    return store.get_adaptive_thresholds()


def check_ip_external(ip_address: str) -> Dict:
    """
    Check an IP against AbuseIPDB (requires ABUSEIPDB_API_KEY env var).
    Falls back gracefully if the key is missing or the API is unreachable.
    """
    api_key = os.environ.get("ABUSEIPDB_API_KEY")
    if not api_key:
        return {
            "ip_address": ip_address,
            "source": "AbuseIPDB",
            "status": "unavailable",
            "message": "ABUSEIPDB_API_KEY not set. External threat intel skipped.",
        }

    try:
        resp = requests.get(
            "https://api.abuseipdb.com/api/v2/check",
            headers={"Key": api_key, "Accept": "application/json"},
            params={"ipAddress": ip_address, "maxAgeInDays": 90},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json().get("data", {})
            return {
                "ip_address": ip_address,
                "source": "AbuseIPDB",
                "status": "found",
                "abuse_confidence_score": data.get("abuseConfidenceScore", 0),
                "total_reports": data.get("totalReports", 0),
                "country": data.get("countryCode", "unknown"),
                "isp": data.get("isp", "unknown"),
                "is_tor": data.get("isTor", False),
                "last_reported": data.get("lastReportedAt"),
            }
        else:
            return {
                "ip_address": ip_address,
                "source": "AbuseIPDB",
                "status": "error",
                "message": f"API returned {resp.status_code}",
            }
    except Exception as e:
        return {
            "ip_address": ip_address,
            "source": "AbuseIPDB",
            "status": "error",
            "message": str(e),
        }


# ════════════════════════════════════════════════════════════════════
# TOOL DISPATCHER — maps tool names to functions
# ════════════════════════════════════════════════════════════════════

TOOL_REGISTRY = {
    "check_ip_reputation": check_ip_reputation,
    "get_attack_history": get_attack_history,
    "get_similar_threats": get_similar_threats,
    "get_network_baseline": get_network_baseline,
    "correlate_recent_events": correlate_recent_events,
    "get_accuracy_stats": get_accuracy_stats,
    "get_adaptive_thresholds": get_adaptive_thresholds,
    "check_ip_external": check_ip_external,
}


def execute_tool(tool_name: str, args: Dict) -> Dict:
    """
    Execute a tool by name with the given arguments.

    Args:
        tool_name: Name of the tool to call
        args: Dict of keyword arguments

    Returns:
        Tool result as a dict, or error dict
    """
    func = TOOL_REGISTRY.get(tool_name)
    if func is None:
        return {"error": f"Unknown tool: {tool_name}. Available: {list(TOOL_REGISTRY.keys())}"}

    try:
        result = func(**args)
        return result
    except TypeError as e:
        return {"error": f"Invalid arguments for {tool_name}: {e}"}
    except Exception as e:
        logger.error(f"Tool {tool_name} failed: {e}")
        return {"error": f"Tool execution failed: {e}"}


def get_tools_description() -> str:
    """
    Get a formatted string describing all available tools,
    suitable for inclusion in an LLM prompt.
    """
    lines = ["AVAILABLE TOOLS (you may call 0-3 tools before deciding):"]
    for i, tool in enumerate(TOOL_DEFINITIONS, 1):
        params_str = ", ".join(f"{k}: {v}" for k, v in tool["parameters"].items()) if tool["parameters"] else "none"
        lines.append(f"  {i}. {tool['name']}({params_str})")
        lines.append(f"     → {tool['description']}")
    return "\n".join(lines)


# ════════════════════════════════════════════════════════════════════
# Helper
# ════════════════════════════════════════════════════════════════════


def _interpret_reputation(score: float) -> str:
    """Human-readable reputation assessment."""
    if score < 0.2:
        return "MALICIOUS — high-confidence bad actor"
    elif score < 0.4:
        return "SUSPICIOUS — has a history of malicious activity"
    elif score < 0.6:
        return "NEUTRAL — insufficient data to assess"
    elif score < 0.8:
        return "MOSTLY BENIGN — occasional low-risk activity"
    else:
        return "BENIGN — no history of malicious activity"


# Quick test
if __name__ == "__main__":
    print(get_tools_description())
    print()
    print("Testing check_ip_reputation for unknown IP:")
    print(json.dumps(check_ip_reputation("10.0.0.1"), indent=2))
    print()
    print("Testing get_network_baseline:")
    print(json.dumps(get_network_baseline(), indent=2))
