"""Quick test for the AgenticThreatAgent."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agentic_threat_agent import AgenticThreatAgent
from datetime import datetime
import json

agent = AgenticThreatAgent(model="llama3:latest")
print(f"Ollama available: {agent.ollama_available}")

# Test with whatever is available (Ollama or rule-based fallback)
result = agent.analyze_and_decide(
    network_risk=0.85,
    user_risk=0.30,
    ip_address="203.0.113.42",
    context={"time": datetime.now().isoformat()}
)
print(f"Action: {result['action']}")
print(f"Confidence: {result['confidence']}")
print(f"Agent type: {result['agent_type']}")
print(f"Reasoning: {result['reasoning']}")
print(f"Decision ID: {result.get('decision_id', 'none')}")

# Test feedback loop
if "decision_id" in result:
    stats = agent.record_outcome(result["decision_id"], "true_positive", "Confirmed DDoS")
    print(f"Feedback recorded. Stats: {json.dumps(stats, indent=2)}")

# Show stats
stats = agent.get_statistics()
print(f"Total decisions in DB: {stats['total_decisions']}")
print(f"Accuracy: {json.dumps(stats['accuracy'], indent=2)}")
