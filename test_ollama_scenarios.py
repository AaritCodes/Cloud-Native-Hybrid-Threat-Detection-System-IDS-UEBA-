"""
Test Ollama AI Agent with Different Threat Scenarios
"""

from src.ollama_agent import OllamaAgent
from datetime import datetime

print("="*70)
print("Testing Ollama AI Agent with Different Threat Scenarios")
print("="*70)

# Initialize agent
agent = OllamaAgent(model="llama3:latest")

# Test scenarios
scenarios = [
    {
        "name": "Normal Traffic",
        "network_risk": 0.05,
        "user_risk": 0.10,
        "context": {
            'time': datetime.now().isoformat(),
            'day_of_week': 'Monday',
            'business_hours': True,
            'recent_attacks': 0,
            'user_importance': 'normal'
        },
        "expected": "LOG"
    },
    {
        "name": "Medium Threat - Suspicious Activity",
        "network_risk": 0.50,
        "user_risk": 0.40,
        "context": {
            'time': datetime.now().isoformat(),
            'day_of_week': 'Wednesday',
            'business_hours': True,
            'recent_attacks': 1,
            'user_importance': 'normal'
        },
        "expected": "ALERT"
    },
    {
        "name": "High Threat - DDoS Attack",
        "network_risk": 0.95,
        "user_risk": 0.10,
        "context": {
            'time': datetime.now().isoformat(),
            'day_of_week': 'Friday',
            'business_hours': True,
            'recent_attacks': 2,
            'user_importance': 'high'
        },
        "expected": "RATE_LIMIT"
    },
    {
        "name": "Critical Threat - Compromised Account",
        "network_risk": 0.95,
        "user_risk": 0.90,
        "context": {
            'time': datetime.now().isoformat(),
            'day_of_week': 'Saturday',
            'business_hours': False,
            'recent_attacks': 5,
            'user_importance': 'high'
        },
        "expected": "BLOCK"
    }
]

# Test each scenario
for i, scenario in enumerate(scenarios, 1):
    print(f"\n{'='*70}")
    print(f"Scenario {i}: {scenario['name']}")
    print(f"{'='*70}")
    print(f"Network Risk: {scenario['network_risk']:.2f}")
    print(f"User Risk: {scenario['user_risk']:.2f}")
    print(f"Context: {scenario['context']['day_of_week']}, "
          f"Business Hours: {scenario['context']['business_hours']}")
    print(f"\nExpected Action: {scenario['expected']}")
    print(f"\nAI Analysis:")
    print("-" * 70)
    
    # Get AI decision
    decision = agent.analyze_and_decide(
        network_risk=scenario['network_risk'],
        user_risk=scenario['user_risk'],
        ip_address=f"192.168.1.{i}",
        context=scenario['context']
    )
    
    # Display results
    print(f"Action: {decision['action']}")
    print(f"Confidence: {decision.get('confidence', 'N/A')}")
    print(f"Risk Assessment: {decision.get('risk_assessment', 'N/A')}")
    print(f"Reasoning: {decision.get('reasoning', 'N/A')}")
    
    # Check if matches expected
    match = "✅ MATCH" if decision['action'] == scenario['expected'] else "⚠️  DIFFERENT"
    print(f"\nResult: {match}")

# Show final statistics
print(f"\n{'='*70}")
print("Final Statistics")
print(f"{'='*70}")
stats = agent.get_statistics()
print(f"Total Decisions: {stats['total_decisions']}")
print(f"Model: {stats['model']}")
print(f"\nActions Taken:")
for action, count in stats.get('actions', {}).items():
    print(f"  {action}: {count}")

print(f"\n{'='*70}")
print("✅ Testing Complete!")
print(f"{'='*70}")
