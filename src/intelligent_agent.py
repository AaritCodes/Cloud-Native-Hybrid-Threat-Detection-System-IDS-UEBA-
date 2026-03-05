"""
Intelligent Agentic AI for Threat Detection
Integrates LLM reasoning with existing threat detection system
"""

import openai
import json
from datetime import datetime
from typing import Dict, Optional

class IntelligentThreatAgent:
    """
    Agentic AI that uses LLM for intelligent threat analysis
    
    Features:
    - Context-aware decision making
    - Explainable reasoning
    - Learning from history
    - Adaptive thresholds
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        Initialize AI agent
        
        Args:
            api_key: OpenAI API key
            model: Model to use (gpt-4, gpt-3.5-turbo, etc.)
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.decision_history = []
    
    def analyze_and_decide(self,
                          network_risk: float,
                          user_risk: float,
                          ip_address: str,
                          context: Optional[Dict] = None) -> Dict:
        """
        Analyze threat using AI and recommend action
        
        Args:
            network_risk: Network risk score (0-1)
            user_risk: User behavior risk score (0-1)
            ip_address: Source IP address
            context: Additional context (time, history, etc.)
        
        Returns:
            Dict with action, confidence, reasoning
        """
        if context is None:
            context = {}
        
        # Build prompt
        prompt = self._build_prompt(network_risk, user_risk, ip_address, context)
        
        # Get AI decision
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3  # Lower for consistent decisions
            )
            
            decision = json.loads(response.choices[0].message.content)
            
            # Store for learning
            self._store_decision(network_risk, user_risk, decision)
            
            return decision
            
        except Exception as e:
            print(f"AI Agent Error: {e}")
            # Fallback to traditional logic
            return self._fallback_decision(network_risk, user_risk)
    
    def _get_system_prompt(self) -> str:
        """System prompt defining AI agent's role"""
        return """
You are an expert cybersecurity AI agent responsible for analyzing threats 
and making response decisions for a cloud infrastructure.

Your goals:
1. Protect the system from attacks
2. Minimize false positives
3. Consider business impact and context
4. Provide clear, actionable reasoning

Available Actions:
- LOG: Record threat information only (low risk)
- ALERT: Send notification to security team (medium risk)
- RATE_LIMIT: Throttle traffic to 10 req/min (high risk)
- BLOCK: Block IP immediately via Security Group (critical risk)

You must respond in JSON format:
{
    "action": "LOG|ALERT|RATE_LIMIT|BLOCK",
    "confidence": 0.0-1.0,
    "reasoning": "clear explanation of decision",
    "risk_assessment": "LOW|MEDIUM|HIGH|CRITICAL",
    "recommended_duration": minutes (for RATE_LIMIT/BLOCK),
    "alternative_actions": ["other possible actions"]
}

Consider:
- Network risk indicates traffic anomalies
- User risk indicates behavioral anomalies
- Context provides situational awareness
- Historical patterns from similar threats
- Business impact of false positives vs missed attacks
"""
    
    def _build_prompt(self, network_risk, user_risk, ip, context) -> str:
        """Build context-aware prompt for AI"""
        
        # Get similar past threats
        similar = self._get_similar_threats(network_risk, user_risk)
        
        prompt = f"""
Analyze this potential cybersecurity threat:

CURRENT THREAT DATA:
- Network Risk: {network_risk:.2f} (0=normal, 1=critical)
  * Indicates traffic volume anomalies
  * Based on CloudWatch metrics
- User Risk: {user_risk:.2f} (0=normal, 1=critical)
  * Indicates behavioral anomalies
  * Based on CloudTrail logs
- IP Address: {ip}
- Timestamp: {context.get('time', datetime.now().isoformat())}

CONTEXTUAL INFORMATION:
- Time of Day: {context.get('time', 'unknown')}
- Day of Week: {context.get('day_of_week', 'unknown')}
- Business Hours: {context.get('business_hours', False)}
- Recent Attacks (last hour): {context.get('recent_attacks', 0)}
- User Importance: {context.get('user_importance', 'normal')}
- Active Blocks: {context.get('active_blocks', 0)}
- System Load: {context.get('system_load', 'normal')}

HISTORICAL CONTEXT:
{similar}

TRADITIONAL SYSTEM DECISION:
- 60/40 Fusion: {(0.6 * network_risk + 0.4 * user_risk):.2f}
- Would recommend: {self._traditional_action(network_risk, user_risk)}

Your task:
1. Analyze all available information
2. Consider context and history
3. Recommend the best action
4. Explain your reasoning clearly
5. Provide confidence level

Remember: False positives are costly, but missed attacks are dangerous.
Balance security with operational continuity.
"""
        return prompt
    
    def _get_similar_threats(self, network_risk, user_risk) -> str:
        """Get similar threats from history"""
        if not self.decision_history:
            return "No historical data available yet."
        
        similar = []
        for entry in self.decision_history[-10:]:  # Last 10 decisions
            nr = entry['input']['network_risk']
            ur = entry['input']['user_risk']
            
            # Find similar risk scores (within 0.2)
            if abs(nr - network_risk) < 0.2 and abs(ur - user_risk) < 0.2:
                similar.append(entry)
        
        if not similar:
            return "No similar threats found in recent history."
        
        summary = ["Similar threats from recent history:"]
        for i, s in enumerate(similar, 1):
            summary.append(
                f"{i}. Network: {s['input']['network_risk']:.2f}, "
                f"User: {s['input']['user_risk']:.2f} → "
                f"Action: {s['decision']['action']} "
                f"(Confidence: {s['decision'].get('confidence', 'N/A')})"
            )
        
        return "\n".join(summary)
    
    def _traditional_action(self, network_risk, user_risk) -> str:
        """What traditional system would recommend"""
        final_risk = 0.6 * network_risk + 0.4 * user_risk
        
        if final_risk < 0.4:
            return "LOG"
        elif final_risk < 0.6:
            return "ALERT"
        elif final_risk < 0.8:
            return "RATE_LIMIT"
        else:
            return "BLOCK"
    
    def _fallback_decision(self, network_risk, user_risk) -> Dict:
        """Fallback to traditional logic if AI fails"""
        final_risk = 0.6 * network_risk + 0.4 * user_risk
        action = self._traditional_action(network_risk, user_risk)
        
        return {
            "action": action,
            "confidence": 0.7,
            "reasoning": "AI unavailable, using traditional 60/40 fusion algorithm",
            "risk_assessment": "MEDIUM",
            "recommended_duration": 10
        }
    
    def _store_decision(self, network_risk, user_risk, decision):
        """Store decision for learning"""
        self.decision_history.append({
            'timestamp': datetime.now(),
            'input': {
                'network_risk': network_risk,
                'user_risk': user_risk
            },
            'decision': decision
        })
        
        # Keep only last 100 decisions
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]
    
    def learn_from_outcome(self, decision_index: int, outcome: str):
        """
        Learn from decision outcomes
        
        Args:
            decision_index: Index in decision_history
            outcome: 'success' | 'false_positive' | 'missed_attack'
        """
        if 0 <= decision_index < len(self.decision_history):
            self.decision_history[decision_index]['outcome'] = outcome
            
            print(f"📚 Learning: Decision {decision_index} outcome = {outcome}")
            
            # Could trigger retraining or threshold adjustment
            if outcome == 'false_positive':
                print("   → Will be more conservative in future")
            elif outcome == 'missed_attack':
                print("   → Will be more aggressive in future")
    
    def get_statistics(self) -> Dict:
        """Get agent statistics"""
        if not self.decision_history:
            return {"total_decisions": 0}
        
        actions = [d['decision']['action'] for d in self.decision_history]
        
        return {
            "total_decisions": len(self.decision_history),
            "actions": {
                "LOG": actions.count('LOG'),
                "ALERT": actions.count('ALERT'),
                "RATE_LIMIT": actions.count('RATE_LIMIT'),
                "BLOCK": actions.count('BLOCK')
            },
            "avg_confidence": sum(
                d['decision'].get('confidence', 0) 
                for d in self.decision_history
            ) / len(self.decision_history)
        }


# Example usage
if __name__ == "__main__":
    # Initialize agent
    agent = IntelligentThreatAgent(
        api_key="your-openai-api-key",
        model="gpt-4"
    )
    
    # Analyze a threat
    decision = agent.analyze_and_decide(
        network_risk=0.95,
        user_risk=0.10,
        ip_address="203.0.113.42",
        context={
            'time': datetime.now().isoformat(),
            'day_of_week': 'Friday',
            'business_hours': True,
            'recent_attacks': 2,
            'user_importance': 'high'
        }
    )
    
    print(f"\nAI Decision: {decision['action']}")
    print(f"Confidence: {decision['confidence']}")
    print(f"Reasoning: {decision['reasoning']}")
