"""
ReAct Agentic Threat Agent

Implements the Observe → Think → Act → Reflect reasoning loop using
a local Ollama LLM with tool-calling capabilities and persistent memory.

This replaces the simple single-shot prompt with a multi-step reasoning
chain where the agent can:
  1. Observe the current threat data
  2. Think about what information it needs
  3. Call tools to gather context (IP reputation, history, baseline, etc.)
  4. Reason about all gathered information
  5. Decide on an action with confidence and explanation
  6. Reflect on its decision for future learning

Author: Aarit Haldar
Date: March 2026
"""

import requests
import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Lazy imports to avoid circular dependencies
_decision_store = None
_agent_tools = None


def _get_store():
    global _decision_store
    if _decision_store is None:
        try:
            from src.decision_store import DecisionStore
        except ModuleNotFoundError:
            from decision_store import DecisionStore
        _decision_store = DecisionStore()
    return _decision_store


def _get_tools():
    global _agent_tools
    if _agent_tools is None:
        try:
            import src.agent_tools as tools
        except ModuleNotFoundError:
            import agent_tools as tools
        _agent_tools = tools
    return _agent_tools


class AgenticThreatAgent:
    """
    ReAct-based agentic AI for threat detection and response.

    Reasoning loop:
        OBSERVE → THINK → [TOOL_CALL → OBSERVE]* → DECIDE → REFLECT

    The agent can call up to 3 tools per reasoning cycle to gather
    context before making its final decision.

    Uses:
        - Ollama for local LLM inference (free, offline, private)
        - DecisionStore for persistent memory and learning
        - AgentTools for environment interaction (IP rep, history, etc.)
    """

    MAX_TOOL_CALLS = 3  # Safety limit per reasoning cycle

    def __init__(
        self,
        model: str = "qwen2.5:0.5b",
        base_url: str = "http://localhost:11434",
        temperature: float = 0.3,
        max_tokens: int = 400,
    ):
        """
        Initialize the agentic threat agent.

        Args:
            model: Ollama model name
            base_url: Ollama API base URL
            temperature: LLM temperature (lower = more consistent)
            max_tokens: Max tokens per LLM response
        """
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model = self._resolve_model(model)
        self.ollama_available = self._check_ollama()
        self.reasoning_trace: List[Dict] = []  # Full trace for debugging

    # ── Model resolution ────────────────────────────────────────────

    def _resolve_model(self, preferred: str) -> str:
        """Pick the best available model, preferring the user's choice."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code != 200:
                return preferred
            available = [m["name"] for m in resp.json().get("models", [])]
            if not available:
                return preferred
            # Exact match
            if preferred in available:
                return preferred
            # Match without tag (e.g. llama3 matches llama3:latest)
            base = preferred.split(":")[0]
            for m in available:
                if m.startswith(base):
                    logger.info(f"Resolved model '{preferred}' → '{m}'")
                    return m
            # Preferred not found — pick fastest available small model
            fast_preference = ["phi3:mini", "phi3", "phi", "mistral", "llama3:latest"]
            for candidate in fast_preference:
                for m in available:
                    if m.startswith(candidate.split(":")[0]):
                        logger.info(f"Model '{preferred}' unavailable. Using '{m}' instead.")
                        return m
            # Last resort: first available
            logger.info(f"Model '{preferred}' unavailable. Using '{available[0]}'.")
            return available[0]
        except Exception:
            return preferred

    # ── Connection check ───────────────────────────────────────────

    def _check_ollama(self) -> bool:
        """Verify Ollama is running and model is available."""
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                if self.model in models:
                    logger.info(f"Ollama connected. Model: {self.model}")
                    return True
                else:
                    logger.warning(
                        f"Model '{self.model}' not found. Available: {models}. "
                        f"Run: ollama pull {self.model}"
                    )
                    # Try without tag
                    base_model = self.model.split(":")[0]
                    for m in models:
                        if m.startswith(base_model):
                            self.model = m
                            logger.info(f"Using available model: {self.model}")
                            return True
                    return False
            return False
        except requests.exceptions.ConnectionError:
            logger.warning("Cannot connect to Ollama. Agent will use rule-based fallback.")
            return False

    # ── Main entry point ───────────────────────────────────────────

    def analyze_and_decide(
        self,
        network_risk: float,
        user_risk: float,
        ip_address: str,
        context: Optional[Dict] = None,
    ) -> Dict:
        """
        Full ReAct reasoning cycle.

        Args:
            network_risk: Network anomaly risk (0-1)
            user_risk: User behavior risk (0-1)
            ip_address: Source IP address
            context: Additional situational context

        Returns:
            Dict with action, confidence, reasoning, tool_calls, reflection
        """
        if context is None:
            context = {}

        final_risk = 0.6 * network_risk + 0.4 * user_risk
        self.reasoning_trace = []  # Reset for this cycle

        # ── Phase 1: OBSERVE ───────────────────────────────────────
        observation = self._observe(network_risk, user_risk, final_risk, ip_address, context)
        self.reasoning_trace.append({"phase": "OBSERVE", "data": observation})

        if not self.ollama_available:
            return self._rule_based_fallback(network_risk, user_risk, final_risk, ip_address)

        # ── Phase 2: THINK + TOOL CALLS ────────────────────────────
        tool_results = {}
        try:
            tool_results = self._think_and_gather(observation, ip_address, network_risk, user_risk)
        except Exception as e:
            logger.warning(f"Think phase failed: {e}")

        # ── Phase 3: DECIDE ────────────────────────────────────────
        try:
            decision = self._decide(observation, tool_results, final_risk)
        except Exception as e:
            logger.warning(f"Decide phase failed: {e}. Using fallback.")
            decision = self._rule_based_fallback(network_risk, user_risk, final_risk, ip_address)

        # ── Phase 4: REFLECT + PERSIST ─────────────────────────────
        self._reflect_and_store(decision, network_risk, user_risk, final_risk, ip_address)

        return decision

    # ── Phase 1: OBSERVE ───────────────────────────────────────────

    def _observe(
        self,
        network_risk: float,
        user_risk: float,
        final_risk: float,
        ip_address: str,
        context: Dict,
    ) -> str:
        """Build the observation string for the LLM."""
        return f"""CURRENT THREAT OBSERVATION:
- IP Address: {ip_address}
- Network Risk: {network_risk:.3f} (0=normal, 1=critical)
- User Risk: {user_risk:.3f} (0=normal, 1=critical)
- Combined Risk (60/40 fusion): {final_risk:.3f}
- Timestamp: {context.get('time', datetime.now().isoformat())}
- Day: {context.get('day_of_week', datetime.now().strftime('%A'))}
- Business Hours: {context.get('business_hours', 'unknown')}
- Recent Attacks (1h): {context.get('recent_attacks', 'unknown')}
- Active Blocks: {context.get('active_blocks', 'unknown')}

RULE-BASED RECOMMENDATION: {self._rule_action(final_risk)}"""

    # ── Phase 2: THINK + TOOL CALLS ────────────────────────────────

    def _think_and_gather(
        self,
        observation: str,
        ip_address: str,
        network_risk: float,
        user_risk: float,
    ) -> Dict:
        """
        Ask the LLM what tools it wants to call, then execute them.
        """
        # Compact tool list (shorter prompt = faster inference)
        tool_names = list(_get_tools().TOOL_REGISTRY.keys())
        tool_list = ", ".join(tool_names)

        think_prompt = f"""THREAT: IP={ip_address} NetRisk={network_risk:.2f} UserRisk={user_risk:.2f} Combined={0.6*network_risk+0.4*user_risk:.2f}

Available tools: {tool_list}
Pick 0-3 tools to gather context. Format:
THINKING: <reason>
TOOL_CALLS:
- tool_name(arg=val)

Or if none needed:
THINKING: <reason>
TOOL_CALLS: none"""

        logger.info("THINK phase: selecting tools...")
        response_text = self._call_ollama(think_prompt, max_tokens=200)
        self.reasoning_trace.append({"phase": "THINK", "prompt_summary": "tool selection", "response": response_text})

        # Parse tool calls from the response
        tool_calls = self._parse_tool_calls(response_text, ip_address, network_risk, user_risk)

        # Execute tools
        tool_results = {}
        tools_mod = _get_tools()
        for tool_name, args in tool_calls[: self.MAX_TOOL_CALLS]:
            logger.info(f"Agent calling tool: {tool_name}({args})")
            result = tools_mod.execute_tool(tool_name, args)
            tool_results[tool_name] = result
            self.reasoning_trace.append({"phase": "TOOL_CALL", "tool": tool_name, "args": args, "result": result})

        return tool_results

    def _parse_tool_calls(
        self,
        response: str,
        ip_address: str,
        network_risk: float,
        user_risk: float,
    ) -> List[Tuple[str, Dict]]:
        """
        Parse tool calls from the LLM response.
        Handles various output formats gracefully.
        """
        calls = []
        valid_tools = _get_tools().TOOL_REGISTRY.keys()

        # Pattern: tool_name(arg1=val1, arg2=val2)
        pattern = r"(\w+)\(([^)]*)\)"
        matches = re.findall(pattern, response)

        for tool_name, args_str in matches:
            if tool_name not in valid_tools:
                continue

            # Parse arguments
            args = {}
            if args_str.strip():
                for part in args_str.split(","):
                    part = part.strip()
                    if "=" in part:
                        key, val = part.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        # Type coercion
                        try:
                            val = float(val)
                            if val == int(val):
                                val = int(val)
                        except ValueError:
                            pass
                        args[key] = val

            # Inject known values for common parameters
            if "ip_address" in str(_get_tools().TOOL_REGISTRY[tool_name].__code__.co_varnames):
                args.setdefault("ip_address", ip_address)
            if "network_risk" in str(_get_tools().TOOL_REGISTRY[tool_name].__code__.co_varnames):
                args.setdefault("network_risk", network_risk)
            if "user_risk" in str(_get_tools().TOOL_REGISTRY[tool_name].__code__.co_varnames):
                args.setdefault("user_risk", user_risk)

            calls.append((tool_name, args))

        # If no tools were parsed but the text mentions tool names, try simple matching
        if not calls:
            for tool_name in valid_tools:
                if tool_name in response.lower():
                    args = {}
                    if "ip" in tool_name:
                        args["ip_address"] = ip_address
                    if "similar" in tool_name:
                        args["network_risk"] = network_risk
                        args["user_risk"] = user_risk
                    calls.append((tool_name, args))

        return calls

    # ── Phase 3: DECIDE ────────────────────────────────────────────

    def _decide(self, observation: str, tool_results: Dict, final_risk: float) -> Dict:
        """
        Final decision with all gathered context.
        """
        # Format tool results for the prompt (keep compact for faster inference)
        if tool_results:
            context_lines = ["INTEL:"]
            for tool_name, result in tool_results.items():
                # Extract only the most relevant fields to keep prompt short
                compact = self._compact_tool_result(tool_name, result)
                context_lines.append(f"[{tool_name}]: {compact}")
            gathered = "\n".join(context_lines)
        else:
            gathered = "No additional intelligence gathered."

        decide_prompt = f"""THREAT: Combined risk={final_risk:.2f}. Rule says: {self._rule_action(final_risk)}
{gathered}

Rules: LOG<0.4, ALERT 0.4-0.6, RATE_LIMIT 0.6-0.8, BLOCK>=0.8.
You may override if intelligence justifies it.

Respond EXACTLY:
ACTION: [LOG/ALERT/RATE_LIMIT/BLOCK]
CONFIDENCE: [0.0-1.0]
RISK_LEVEL: [LOW/MEDIUM/HIGH/CRITICAL]
REASONING: [1-2 sentences]"""

        logger.info("DECIDE phase: making final decision...")
        response_text = self._call_ollama(decide_prompt, max_tokens=150)
        self.reasoning_trace.append({"phase": "DECIDE", "response": response_text})

        # Parse the structured response
        decision = self._parse_decision(response_text, final_risk, tool_results)
        return decision

    def _parse_decision(self, response: str, final_risk: float, tool_results: Dict) -> Dict:
        """Parse the LLM's decision response into a structured dict."""
        action = self._extract_field(response, "ACTION", self._rule_action(final_risk))
        confidence = self._extract_float(response, "CONFIDENCE", 0.8)
        risk_level = self._extract_field(response, "RISK_LEVEL", self._rule_risk_level(final_risk))
        reasoning = self._extract_field(response, "REASONING", f"Combined risk {final_risk:.2f}")

        # Validate action
        valid_actions = {"LOG", "ALERT", "RATE_LIMIT", "BLOCK"}
        if action not in valid_actions:
            # Try to find a valid action in the response
            for a in valid_actions:
                if a in response.upper():
                    action = a
                    break
            else:
                action = self._rule_action(final_risk)

        return {
            "action": action,
            "confidence": min(1.0, max(0.0, confidence)),
            "reasoning": reasoning,
            "risk_assessment": risk_level,
            "recommended_duration": 10,
            "tools_used": list(tool_results.keys()),
            "agent_type": "ReAct-Agentic",
            "model": self.model,
        }

    # ── Phase 4: REFLECT + PERSIST ─────────────────────────────────

    def _reflect_and_store(
        self,
        decision: Dict,
        network_risk: float,
        user_risk: float,
        final_risk: float,
        ip_address: str,
    ):
        """
        Store the decision in persistent memory and optionally reflect.
        """
        store = _get_store()
        try:
            decision_id = store.store_decision(
                ip_address=ip_address,
                network_risk=network_risk,
                user_risk=user_risk,
                final_risk=final_risk,
                action=decision["action"],
                confidence=decision.get("confidence", 0.0),
                reasoning=decision.get("reasoning", ""),
                risk_assessment=decision.get("risk_assessment", ""),
                ai_model=f"ollama/{self.model}",
                context={
                    "tools_used": decision.get("tools_used", []),
                    "reasoning_steps": len(self.reasoning_trace),
                },
            )
            decision["decision_id"] = decision_id
            logger.info(f"Decision #{decision_id} persisted to database")
        except Exception as e:
            logger.warning(f"Failed to persist decision: {e}")

        self.reasoning_trace.append({
            "phase": "REFLECT",
            "decision": decision["action"],
            "persisted": "decision_id" in decision,
        })

    # ── Feedback loop ──────────────────────────────────────────────

    def record_outcome(self, decision_id: int, outcome: str, notes: str = "") -> Dict:
        """
        Record the outcome of a past decision — this is the learning signal.

        Args:
            decision_id: ID from the decision store
            outcome: 'true_positive', 'false_positive', 'missed_attack', 'benign'
            notes: Optional notes

        Returns:
            Updated accuracy stats
        """
        store = _get_store()
        success = store.record_outcome(decision_id, outcome, notes)
        if success:
            stats = store.get_accuracy_stats()
            logger.info(
                f"Outcome recorded for decision #{decision_id}: {outcome}. "
                f"Overall accuracy: {stats.get('accuracy', 'N/A')}"
            )
            return stats
        return {"error": "Failed to record outcome"}

    # ── Rule-based fallback ────────────────────────────────────────

    def _rule_based_fallback(
        self,
        network_risk: float,
        user_risk: float,
        final_risk: float,
        ip_address: str,
    ) -> Dict:
        """
        Fallback to rule-based decision when Ollama is unavailable.
        Still persists the decision to the store.
        """
        action = self._rule_action(final_risk)
        decision = {
            "action": action,
            "confidence": 0.7,
            "reasoning": f"Rule-based fallback (Ollama unavailable). Combined risk {final_risk:.2f} maps to {action}.",
            "risk_assessment": self._rule_risk_level(final_risk),
            "recommended_duration": 10,
            "tools_used": [],
            "agent_type": "rule-based-fallback",
            "model": "none",
        }

        # Still persist
        self._reflect_and_store(decision, network_risk, user_risk, final_risk, ip_address)
        return decision

    # ── LLM communication ──────────────────────────────────────────

    def _call_ollama(self, prompt: str, max_tokens: int | None = None) -> str:
        """Send a prompt to Ollama and return the response text."""
        tokens = max_tokens or self.max_tokens
        try:
            resp = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": tokens,
                        "top_k": 20,
                        "top_p": 0.7,
                    },
                },
                timeout=180,
            )
            if resp.status_code == 200:
                return resp.json().get("response", "")
            else:
                logger.warning(f"Ollama returned {resp.status_code}")
                return ""
        except requests.exceptions.ReadTimeout:
            logger.warning(
                f"Ollama timed out (180s). Model '{self.model}' may be too slow. "
                "Consider using a smaller model like phi3:mini."
            )
            return ""
        except requests.exceptions.ConnectionError:
            logger.warning("Cannot connect to Ollama. Is 'ollama serve' running?")
            self.ollama_available = False
            return ""
        except Exception as e:
            logger.warning(f"Ollama call failed: {e}")
            return ""

    # ── Parsing helpers ────────────────────────────────────────────

    def _extract_field(self, text: str, field: str, default: str) -> str:
        """Extract a named field from structured text."""
        pattern = rf"{field}:\s*(.+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip().strip("[]")
            # Remove trailing content after newline
            value = value.split("\n")[0].strip()
            return value
        return default

    def _extract_float(self, text: str, field: str, default: float) -> float:
        """Extract a float value from structured text."""
        pattern = rf"{field}:\s*([\d.]+)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                pass
        return default

    @staticmethod
    def _compact_tool_result(tool_name: str, result: Dict) -> str:
        """Summarise a tool result into a short string for the LLM prompt."""
        if not isinstance(result, dict):
            return str(result)[:120]
        # Pick the most useful keys depending on tool
        if "reputation_score" in result:
            return (
                f"status={result.get('status')}, reputation={result.get('reputation_score')}, "
                f"events={result.get('total_events',0)}, blocks={result.get('total_blocks',0)}, "
                f"assessment={result.get('assessment','')}"
            )
        if "total_past_decisions" in result:
            return f"past_decisions={result.get('total_past_decisions',0)}, message={result.get('message','')}"
        if "most_common_action" in result:
            return (
                f"similar={result.get('total_similar',0)}, "
                f"most_common_action={result.get('most_common_action','')}, "
                f"actions={result.get('action_distribution',{})}"
            )
        if "recent_events_1h" in result:
            return f"status={result.get('status')}, events_1h={result.get('recent_events_1h',0)}"
        # Generic fallback — keep it short
        summary = json.dumps(result, default=str)
        return summary[:200] + ("..." if len(summary) > 200 else "")

    @staticmethod
    def _rule_action(final_risk: float) -> str:
        """Simple threshold-based action."""
        if final_risk < 0.4:
            return "LOG"
        elif final_risk < 0.6:
            return "ALERT"
        elif final_risk < 0.8:
            return "RATE_LIMIT"
        else:
            return "BLOCK"

    @staticmethod
    def _rule_risk_level(final_risk: float) -> str:
        """Simple threshold-based risk level."""
        if final_risk < 0.4:
            return "LOW"
        elif final_risk < 0.6:
            return "MEDIUM"
        elif final_risk < 0.8:
            return "HIGH"
        else:
            return "CRITICAL"

    # ── Statistics & debugging ─────────────────────────────────────

    def get_statistics(self) -> Dict:
        """Get agent and decision store statistics."""
        store = _get_store()
        accuracy = store.get_accuracy_stats()
        thresholds = store.get_adaptive_thresholds()
        return {
            "model": self.model,
            "ollama_available": self.ollama_available,
            "agent_type": "ReAct-Agentic",
            "total_decisions": store.get_total_decisions(),
            "accuracy": accuracy,
            "adaptive_thresholds": thresholds,
        }

    def get_reasoning_trace(self) -> List[Dict]:
        """Get the full reasoning trace from the last decision."""
        return self.reasoning_trace


# ════════════════════════════════════════════════════════════════════
# CLI Test
# ════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    print("=" * 70)
    print("  ReAct Agentic Threat Agent — Test")
    print("=" * 70)

    agent = AgenticThreatAgent(model="qwen2.5:0.5b")

    # ── Test 1: Low risk ────────────────────────────────
    print("\n--- Test 1: Low Risk ---")
    result = agent.analyze_and_decide(
        network_risk=0.10,
        user_risk=0.05,
        ip_address="10.0.0.50",
        context={"time": datetime.now().isoformat(), "business_hours": True},
    )
    print(f"Action: {result['action']} | Confidence: {result['confidence']:.2f}")
    print(f"Reasoning: {result['reasoning']}")
    print(f"Tools used: {result.get('tools_used', [])}")

    # ── Test 2: Critical risk ──────────────────────────
    print("\n--- Test 2: Critical Risk ---")
    result = agent.analyze_and_decide(
        network_risk=0.95,
        user_risk=0.80,
        ip_address="203.0.113.42",
        context={"time": datetime.now().isoformat(), "recent_attacks": 3},
    )
    print(f"Action: {result['action']} | Confidence: {result['confidence']:.2f}")
    print(f"Reasoning: {result['reasoning']}")
    print(f"Tools used: {result.get('tools_used', [])}")

    # ── Test 3: Record outcome (feedback loop) ─────────
    if "decision_id" in result:
        print(f"\n--- Recording outcome for decision #{result['decision_id']} ---")
        stats = agent.record_outcome(result["decision_id"], "true_positive", "Confirmed DDoS")
        print(f"Accuracy stats: {stats}")

    # ── Show overall stats ─────────────────────────────
    print("\n--- Agent Statistics ---")
    stats = agent.get_statistics()
    print(json.dumps(stats, indent=2, default=str))

    # ── Show reasoning trace ───────────────────────────
    print("\n--- Last Reasoning Trace ---")
    for step in agent.get_reasoning_trace():
        print(f"  [{step['phase']}]", end="")
        if "tool" in step:
            print(f" → {step['tool']}({step.get('args', {})})")
        elif "response" in step:
            preview = str(step["response"])[:80]
            print(f" → {preview}...")
        else:
            print()
