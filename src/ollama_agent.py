"""
Local Agentic AI using Ollama
No API costs, runs offline, privacy-friendly
"""

import requests
import json
from datetime import datetime
from typing import Dict, Optional

class OllamaAgent:
    """
    Agentic AI using local Ollama LLM
    
    Features:
    - Free (no API costs)
    - Runs offline
    - Privacy-friendly (data stays local)
    - Fast inference
    - Multiple model support
    """
    
    def __init__(self, 
                 model: str = "llama3:latest",
                 base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama agent
        
        Args:
            model: Ollama model to use (llama3:latest, mistral, phi, etc.)
            base_url: Ollama API endpoint
        """
        self.model = model
        self.base_url = base_url
        self.decision_history = []
        
        # Verify Ollama is running
        self._check_ollama()
    
    def _check_ollama(self):
        """Check if Ollama is running and model is available"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                models = [m['name'] for m in response.json()['models']]
                if self.model not in models:
                    print(f"⚠️  Model '{self.model}' not found.")
                    print(f"   Available models: {', '.join(models)}")
                    print(f"   Run: ollama pull {self.model}")
                else:
                    print(f"✅ Ollama connected. Using model: {self.model}")
            else:
                print("⚠️  Ollama not responding. Make sure it's running.")
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to Ollama.")
            print("   1. Install: https://ollama.ai/")
            print("   2. Run: ollama serve")
            print(f"   3. Pull model: ollama pull {self.model}")
    
    def analyze_and_decide(self,
                          network_risk: float,
                          user_risk: float,
                          ip_address: str,
                          context: Optional[Dict] = None) -> Dict:
        """
        Analyze threat using local LLM and recommend action
        
        Args:
            network_risk: Network risk score (0-1)
            user_risk: User behavior risk score (0-1)
            ip_address: Source IP address
            context: Additional context
        
        Returns:
            Dict with action, confidence, reasoning
        """
        if context is None:
            context = {}
        
        # Calculate combined risk using 60/40 fusion
        final_risk = 0.6 * network_risk + 0.4 * user_risk
        
        # Ultra-simplified prompt for faster response
        prompt = f"""Threat: Network={network_risk:.2f}, User={user_risk:.2f}, Combined={final_risk:.2f}
Action needed (LOG<0.4, ALERT 0.4-0.6, RATE_LIMIT 0.6-0.8, BLOCK>=0.8)?
Format: Action: [ACTION]"""
        
        try:
            # Call Ollama API without JSON format requirement
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # More deterministic
                        "num_predict": 20,   # Minimal tokens for fast response
                        "top_k": 10,
                        "top_p": 0.5
                    }
                },
                timeout=10  # Reduced for simple classification
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', '')
                
                # Parse the response
                action = self._extract_action(ai_response, final_risk)
                reasoning = self._extract_reasoning(ai_response, final_risk)
                
                decision = {
                    "action": action,
                    "confidence": 0.85,
                    "reasoning": reasoning,
                    "risk_assessment": self._assess_risk_level(final_risk),
                    "recommended_duration": 10
                }
                
                # Store for learning
                self._store_decision(network_risk, user_risk, decision)
                
                return decision
            else:
                print(f"Ollama error: {response.status_code}")
                return self._fallback_decision(network_risk, user_risk)
                
        except Exception as e:
            print(f"Ollama Agent Error: {e}")
            return self._fallback_decision(network_risk, user_risk)
    
    def _extract_action(self, response: str, final_risk: float) -> str:
        """Extract action from AI response, fallback to rule-based"""
        response_upper = response.upper()
        
        if "BLOCK" in response_upper:
            return "BLOCK"
        elif "RATE_LIMIT" in response_upper or "RATE LIMIT" in response_upper:
            return "RATE_LIMIT"
        elif "ALERT" in response_upper:
            return "ALERT"
        elif "LOG" in response_upper:
            return "LOG"
        else:
            # Fallback to rule-based using final_risk directly
            if final_risk < 0.4:
                return "LOG"
            elif final_risk < 0.6:
                return "ALERT"
            elif final_risk < 0.8:
                return "RATE_LIMIT"
            else:
                return "BLOCK"
    
    def _extract_reasoning(self, response: str, final_risk: float) -> str:
        """Extract reasoning from AI response"""
        lines = response.split('\n')
        for line in lines:
            if 'reasoning:' in line.lower():
                return line.split(':', 1)[1].strip()
        
        # If no reasoning found, return the whole response or default
        if len(response) > 20 and len(response) < 300:
            return response.strip()
        else:
            return f"Combined risk of {final_risk:.2f} indicates appropriate action based on threat thresholds"
    
    def _assess_risk_level(self, final_risk: float) -> str:
        """Assess risk level from score"""
        if final_risk < 0.4:
            return "LOW"
        elif final_risk < 0.6:
            return "MEDIUM"
        elif final_risk < 0.8:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def _build_prompt(self, network_risk, user_risk, ip, context) -> str:
        """Build prompt for local LLM"""
        
        # Get similar past threats
        similar = self._get_similar_threats(network_risk, user_risk)
        
        # Traditional system decision
        traditional = self._traditional_action(network_risk, user_risk)
        
        prompt = f"""You are a cybersecurity AI agent. Analyze this threat and choose ONE action.

THREAT DATA:
- Network Risk: {network_risk:.2f} (0=normal, 1=critical)
- User Risk: {user_risk:.2f} (0=normal, 1=critical)
- IP: {ip}
- Time: {context.get('time', datetime.now().isoformat())}
- Day: {context.get('day_of_week', 'unknown')}
- Business Hours: {context.get('business_hours', False)}
- Recent Attacks: {context.get('recent_attacks', 0)}
- User Importance: {context.get('user_importance', 'normal')}

HISTORY:
{similar}

TRADITIONAL SYSTEM (60/40 fusion):
- Combined Risk: {(0.6 * network_risk + 0.4 * user_risk):.2f}
- Recommendation: {traditional}

ACTION RULES (follow strictly):
- Combined Risk < 0.4 → LOG (just record)
- Combined Risk 0.4-0.6 → ALERT (notify team)
- Combined Risk 0.6-0.8 → RATE_LIMIT (throttle traffic)
- Combined Risk >= 0.8 → BLOCK (block IP immediately)

Your task: Choose the appropriate action based on the combined risk score.

Respond with ONLY this JSON (no extra text):
{{
    "action": "LOG",
    "confidence": 0.85,
    "reasoning": "Combined risk is X.XX which falls in Y range, therefore action Z is appropriate",
    "risk_assessment": "LOW",
    "recommended_duration": 10
}}"""
        return prompt
    
    def _get_similar_threats(self, network_risk, user_risk) -> str:
        """Get similar threats from history"""
        if not self.decision_history:
            return "No historical data yet."
        
        similar = []
        for entry in self.decision_history[-10:]:
            nr = entry['input']['network_risk']
            ur = entry['input']['user_risk']
            
            if abs(nr - network_risk) < 0.2 and abs(ur - user_risk) < 0.2:
                similar.append(entry)
        
        if not similar:
            return "No similar threats found."
        
        summary = ["Similar past threats:"]
        for i, s in enumerate(similar, 1):
            summary.append(
                f"{i}. Network: {s['input']['network_risk']:.2f}, "
                f"User: {s['input']['user_risk']:.2f} -> "
                f"Action: {s['decision']['action']}"
            )
        
        return "\n".join(summary)
    
    def _traditional_action(self, network_risk, user_risk) -> str:
        """Traditional 60/40 fusion decision"""
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
        """Fallback to traditional logic if Ollama fails"""
        final_risk = 0.6 * network_risk + 0.4 * user_risk
        action = self._traditional_action(network_risk, user_risk)
        
        return {
            "action": action,
            "confidence": 0.7,
            "reasoning": "Ollama unavailable, using traditional 60/40 fusion",
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
        
        # Keep only last 100
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]
    
    def get_statistics(self) -> Dict:
        """Get agent statistics"""
        if not self.decision_history:
            return {
                "total_decisions": 0,
                "model": self.model
            }
        
        actions = [d['decision']['action'] for d in self.decision_history]
        
        return {
            "total_decisions": len(self.decision_history),
            "model": self.model,
            "actions": {
                "LOG": actions.count('LOG'),
                "ALERT": actions.count('ALERT'),
                "RATE_LIMIT": actions.count('RATE_LIMIT'),
                "BLOCK": actions.count('BLOCK')
            }
        }


# Example usage
if __name__ == "__main__":
    print("Testing Ollama Agent...\n")
    
    # Initialize agent
    agent = OllamaAgent(model="llama3:latest")
    
    # Test decision
    print("\nAnalyzing threat...")
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
    
    print(f"\n🤖 AI Decision:")
    print(f"   Action: {decision['action']}")
    print(f"   Confidence: {decision.get('confidence', 'N/A')}")
    print(f"   Reasoning: {decision.get('reasoning', 'N/A')}")
    print(f"   Risk Assessment: {decision.get('risk_assessment', 'N/A')}")
    
    # Show statistics
    stats = agent.get_statistics()
    print(f"\n📊 Statistics:")
    print(f"   Total Decisions: {stats['total_decisions']}")
    print(f"   Model: {stats.get('model', 'N/A')}")
