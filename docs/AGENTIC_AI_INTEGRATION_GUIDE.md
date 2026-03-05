# Agentic AI Integration Guide
## Enhancing Threat Detection with Intelligent Agents

**Author:** Aarit Haldar  
**Date:** February 2026

---

## Table of Contents
1. [Overview](#overview)
2. [Why Agentic AI?](#why-agentic-ai)
3. [Integration Approaches](#integration-approaches)
4. [Implementation Options](#implementation-options)
5. [Step-by-Step Integration](#step-by-step-integration)
6. [Code Examples](#code-examples)
7. [Benefits](#benefits)
8. [Challenges](#challenges)

---

## 1. Overview

### What is Agentic AI?

Agentic AI systems are autonomous agents that can:
- **Perceive** their environment (threat landscape)
- **Reason** about situations (analyze threats)
- **Plan** actions (response strategies)
- **Learn** from experience (improve over time)
- **Act** autonomously (execute responses)

### Current System vs Agentic AI

**Current System (Rule-Based):**
```
Risk < 0.4 → LOG
0.4-0.6 → ALERT
0.6-0.8 → RATE_LIMIT
≥ 0.8 → BLOCK
```
Fixed thresholds, no learning, no context awareness.

**With Agentic AI:**
```
Agent analyzes:
- Historical attack patterns
- Current threat landscape
- Business context
- Time of day
- User importance
→ Intelligent decision with reasoning
→ Learns from outcomes
→ Adapts thresholds dynamically
```

---

## 2. Why Agentic AI?

### Limitations of Current System

1. **Fixed Thresholds:** 0.4, 0.6, 0.8 don't adapt
2. **No Context:** Doesn't consider business impact
3. **No Learning:** Same response every time
4. **No Reasoning:** Can't explain decisions
5. **No Adaptation:** Doesn't improve over time

### Benefits of Agentic AI

1. **Adaptive Thresholds:** Learn optimal values
2. **Context-Aware:** Consider business impact
3. **Continuous Learning:** Improve from feedback
4. **Explainable:** Provide reasoning for decisions
5. **Proactive:** Predict threats before they happen



---

## 3. Integration Approaches

### Approach 1: LLM-Based Agent (Recommended)

Use Large Language Models (GPT-4, Claude, Gemini) as reasoning engine.

**Architecture:**
```
Threat Detection System
    ↓
Risk Scores + Context
    ↓
LLM Agent (GPT-4/Claude)
    ↓
Reasoning + Decision
    ↓
Action Execution
```

**Pros:**
- Natural language reasoning
- Explainable decisions
- Easy to implement
- No training needed

**Cons:**
- API costs
- Latency (1-3 seconds)
- Requires internet

### Approach 2: Reinforcement Learning Agent

Train an RL agent to learn optimal response policies.

**Architecture:**
```
State: [network_risk, user_risk, time, context]
    ↓
RL Agent (DQN/PPO)
    ↓
Action: [LOG, ALERT, RATE_LIMIT, BLOCK]
    ↓
Reward: Based on outcome
```

**Pros:**
- Learns optimal policy
- Fast inference
- No API costs

**Cons:**
- Requires training data
- Complex implementation
- Needs reward engineering

### Approach 3: Hybrid (Best of Both)

Combine LLM reasoning with RL optimization.

**Architecture:**
```
Threat Detection
    ↓
LLM: High-level reasoning
    ↓
RL Agent: Fine-tuned actions
    ↓
Execution + Learning
```

---

## 4. Implementation Options

### Option 1: OpenAI GPT-4 Integration (Easiest)

**Tools Needed:**
- OpenAI API key
- `openai` Python library
- Prompt engineering

**Cost:** ~$0.01-0.03 per decision

### Option 2: Local LLM (Ollama)

**Tools Needed:**
- Ollama (local LLM runtime)
- Llama 3 or Mistral model
- 16GB+ RAM

**Cost:** Free (runs locally)

### Option 3: LangChain + Agents

**Tools Needed:**
- LangChain framework
- LLM (OpenAI/Anthropic/Local)
- Agent tools and memory

**Cost:** Depends on LLM choice

### Option 4: AutoGen Framework

**Tools Needed:**
- Microsoft AutoGen
- Multiple LLM agents
- Agent orchestration

**Cost:** Depends on LLM choice

---

## 5. Step-by-Step Integration

### Phase 1: Simple LLM Integration (1-2 days)

**Step 1: Install Dependencies**
```bash
pip install openai langchain
```

**Step 2: Create AI Agent Class**
```python
# src/ai_agent.py
import openai
from typing import Dict

class ThreatAnalysisAgent:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
    
    def analyze_threat(self, 
                      network_risk: float,
                      user_risk: float,
                      context: Dict) -> Dict:
        """
        Use LLM to analyze threat and recommend action
        """
        prompt = f"""
        You are a cybersecurity expert analyzing a potential threat.
        
        Threat Data:
        - Network Risk: {network_risk} (0-1 scale)
        - User Risk: {user_risk} (0-1 scale)
        - Time: {context.get('time')}
        - Previous Attacks: {context.get('history')}
        
        Available Actions:
        1. LOG - Just record (low risk)
        2. ALERT - Notify security team (medium risk)
        3. RATE_LIMIT - Throttle traffic (high risk)
        4. BLOCK - Block IP immediately (critical risk)
        
        Analyze this threat and recommend:
        1. Action to take
        2. Reasoning for your decision
        3. Confidence level (0-1)
        
        Respond in JSON format.
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
```

**Step 3: Integrate with Existing System**
```python
# Modify src/enhanced_main_with_agent.py

from src.ai_agent import ThreatAnalysisAgent

# Initialize AI agent
ai_agent = ThreatAnalysisAgent(api_key="your-openai-key")

# In detection cycle:
if final_risk > 0.3:  # Only use AI for potential threats
    context = {
        'time': datetime.now().isoformat(),
        'history': get_recent_attacks(),
        'user_importance': get_user_importance(ip)
    }
    
    ai_decision = ai_agent.analyze_threat(
        network_risk, user_risk, context
    )
    
    print(f"AI Reasoning: {ai_decision['reasoning']}")
    action = ai_decision['action']
else:
    action = "LOG"  # Skip AI for low risk
```

### Phase 2: Add Memory & Learning (3-5 days)

**Step 1: Add Vector Database**
```bash
pip install chromadb
```

**Step 2: Store Historical Decisions**
```python
import chromadb

class AgentMemory:
    def __init__(self):
        self.client = chromadb.Client()
        self.collection = self.client.create_collection("threats")
    
    def store_decision(self, threat_data, decision, outcome):
        """Store decision and outcome for learning"""
        self.collection.add(
            documents=[str(threat_data)],
            metadatas=[{
                'decision': decision,
                'outcome': outcome,
                'timestamp': datetime.now().isoformat()
            }]
        )
    
    def get_similar_threats(self, current_threat):
        """Retrieve similar past threats"""
        results = self.collection.query(
            query_texts=[str(current_threat)],
            n_results=5
        )
        return results
```

**Step 3: Use Memory in Decisions**
```python
# Get similar past threats
similar = memory.get_similar_threats({
    'network_risk': network_risk,
    'user_risk': user_risk
})

# Include in prompt
prompt += f"\nSimilar Past Threats:\n{similar}"
```

### Phase 3: Reinforcement Learning (1-2 weeks)

**Step 1: Define RL Environment**
```python
import gym
from gym import spaces
import numpy as np

class ThreatResponseEnv(gym.Env):
    def __init__(self):
        super().__init__()
        
        # State: [network_risk, user_risk, hour, day_of_week]
        self.observation_space = spaces.Box(
            low=0, high=1, shape=(4,), dtype=np.float32
        )
        
        # Actions: LOG=0, ALERT=1, RATE_LIMIT=2, BLOCK=3
        self.action_space = spaces.Discrete(4)
    
    def step(self, action):
        # Execute action
        # Calculate reward based on outcome
        reward = self._calculate_reward(action)
        done = True
        return self.state, reward, done, {}
    
    def _calculate_reward(self, action):
        # Reward engineering
        if self.is_attack and action == 3:  # Blocked attack
            return +10
        elif self.is_attack and action < 2:  # Missed attack
            return -10
        elif not self.is_attack and action == 3:  # False positive
            return -5
        else:
            return 0
```

**Step 2: Train RL Agent**
```python
from stable_baselines3 import PPO

# Create environment
env = ThreatResponseEnv()

# Train agent
model = PPO("MlpPolicy", env, verbose=1)
model.learn(total_timesteps=10000)

# Save model
model.save("models/rl_agent")
```

**Step 3: Use RL Agent**
```python
# Load trained agent
model = PPO.load("models/rl_agent")

# Get action
state = [network_risk, user_risk, hour, day_of_week]
action = model.predict(state)[0]

# Map to action name
actions = ['LOG', 'ALERT', 'RATE_LIMIT', 'BLOCK']
action_name = actions[action]
```



---

## 6. Code Examples

### Example 1: Complete LLM Agent Integration

```python
# src/intelligent_agent.py

import openai
import json
from datetime import datetime
from typing import Dict, List

class IntelligentThreatAgent:
    """
    Agentic AI for intelligent threat response
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.decision_history = []
    
    def analyze_and_decide(self,
                          network_risk: float,
                          user_risk: float,
                          ip_address: str,
                          context: Dict) -> Dict:
        """
        Intelligent threat analysis with reasoning
        """
        
        # Build context-aware prompt
        prompt = self._build_prompt(
            network_risk, user_risk, ip_address, context
        )
        
        # Get LLM decision
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3  # Lower for consistent decisions
        )
        
        # Parse decision
        decision = json.loads(response.choices[0].message.content)
        
        # Store for learning
        self.decision_history.append({
            'timestamp': datetime.now(),
            'input': {'network_risk': network_risk, 'user_risk': user_risk},
            'decision': decision
        })
        
        return decision
    
    def _get_system_prompt(self) -> str:
        return """
        You are an expert cybersecurity AI agent responsible for 
        analyzing threats and making response decisions.
        
        Your goals:
        1. Protect the system from attacks
        2. Minimize false positives
        3. Consider business impact
        4. Provide clear reasoning
        
        You must respond in JSON format with:
        {
            "action": "LOG|ALERT|RATE_LIMIT|BLOCK",
            "confidence": 0.0-1.0,
            "reasoning": "explanation",
            "risk_assessment": "LOW|MEDIUM|HIGH|CRITICAL",
            "recommended_duration": minutes (for RATE_LIMIT/BLOCK)
        }
        """
    
    def _build_prompt(self, network_risk, user_risk, ip, context) -> str:
        # Get historical context
        similar_threats = self._get_similar_threats(network_risk, user_risk)
        
        prompt = f"""
        Analyze this potential threat:
        
        CURRENT THREAT:
        - Network Risk: {network_risk:.2f} (0=normal, 1=critical)
        - User Risk: {user_risk:.2f} (0=normal, 1=critical)
        - IP Address: {ip}
        - Time: {context.get('time', 'unknown')}
        - Day of Week: {context.get('day_of_week', 'unknown')}
        
        CONTEXT:
        - Recent attacks in last hour: {context.get('recent_attacks', 0)}
        - User importance: {context.get('user_importance', 'normal')}
        - Business hours: {context.get('business_hours', False)}
        
        SIMILAR PAST THREATS:
        {similar_threats}
        
        CURRENT SYSTEM STATE:
        - Active blocks: {context.get('active_blocks', 0)}
        - System load: {context.get('system_load', 'normal')}
        
        Analyze and recommend action.
        """
        
        return prompt
    
    def _get_similar_threats(self, network_risk, user_risk) -> str:
        """Get similar threats from history"""
        if not self.decision_history:
            return "No historical data yet"
        
        # Simple similarity: find threats with similar risk scores
        similar = []
        for entry in self.decision_history[-10:]:  # Last 10
            nr = entry['input']['network_risk']
            ur = entry['input']['user_risk']
            
            if abs(nr - network_risk) < 0.2 and abs(ur - user_risk) < 0.2:
                similar.append(entry)
        
        if not similar:
            return "No similar threats found"
        
        summary = []
        for s in similar:
            summary.append(
                f"- Risk: {s['input']['network_risk']:.2f}/"
                f"{s['input']['user_risk']:.2f}, "
                f"Action: {s['decision']['action']}"
            )
        
        return "\n".join(summary)
    
    def learn_from_outcome(self, decision_id: int, outcome: str):
        """
        Learn from decision outcomes
        outcome: 'success' | 'false_positive' | 'missed_attack'
        """
        if decision_id < len(self.decision_history):
            self.decision_history[decision_id]['outcome'] = outcome
            
            # Could trigger retraining or threshold adjustment
            if outcome == 'false_positive':
                print(f"Learning: Decision {decision_id} was false positive")
            elif outcome == 'missed_attack':
                print(f"Learning: Decision {decision_id} missed attack")
```

### Example 2: Integration with Main System

```python
# Modified src/enhanced_main_with_agent.py

from src.intelligent_agent import IntelligentThreatAgent

class EnhancedThreatDetectionWithAI:
    def __init__(self, security_group_id, openai_api_key):
        # Existing components
        self.ids = IDSEngine("models/ddos_model.pkl")
        self.ueba = UEBAEngine("models/uba_model.pkl")
        
        # NEW: AI Agent
        self.ai_agent = IntelligentThreatAgent(
            api_key=openai_api_key,
            model="gpt-4"
        )
        
        # Traditional agent as fallback
        self.traditional_agent = AutonomousResponseAgent(
            security_group_id=security_group_id
        )
    
    def run_detection_cycle(self):
        # Run detection
        network_results = self.ids.detect()
        user_results = self.ueba.detect()
        
        for net in network_results:
            ip = net["ip"]
            network_risk = net["network_risk"]
            user_risk = self._get_user_risk(ip, user_results)
            
            # Traditional fusion
            final_risk, level = combine_risks(network_risk, user_risk)
            
            # Build context
            context = {
                'time': datetime.now().isoformat(),
                'day_of_week': datetime.now().strftime('%A'),
                'recent_attacks': self._count_recent_attacks(),
                'user_importance': self._get_user_importance(ip),
                'business_hours': self._is_business_hours(),
                'active_blocks': len(self.traditional_agent.blacklist),
                'system_load': 'normal'
            }
            
            # Use AI for medium/high/critical threats
            if final_risk >= 0.4:
                print("\n🤖 AI Agent Analyzing Threat...")
                
                ai_decision = self.ai_agent.analyze_and_decide(
                    network_risk=network_risk,
                    user_risk=user_risk,
                    ip_address=ip,
                    context=context
                )
                
                print(f"AI Decision: {ai_decision['action']}")
                print(f"Confidence: {ai_decision['confidence']:.2f}")
                print(f"Reasoning: {ai_decision['reasoning']}")
                
                # Execute AI decision
                self._execute_ai_decision(ip, ai_decision)
                
            else:
                # Use traditional agent for low risk
                self.traditional_agent.take_action(
                    ip, final_risk, network_risk, user_risk
                )
    
    def _execute_ai_decision(self, ip: str, decision: Dict):
        """Execute AI agent's decision"""
        action = decision['action']
        
        if action == 'LOG':
            self.traditional_agent.log_threat(ip, ...)
        elif action == 'ALERT':
            self.traditional_agent.send_alert(ip, ...)
        elif action == 'RATE_LIMIT':
            duration = decision.get('recommended_duration', 5)
            self.traditional_agent.simulate_rate_limiting(ip, ...)
        elif action == 'BLOCK':
            duration = decision.get('recommended_duration', 10)
            self.traditional_agent.block_ip_address(ip, ...)
```

### Example 3: Local LLM with Ollama (No API Costs)

```python
# src/local_ai_agent.py

import requests
import json

class LocalAIAgent:
    """
    Use local LLM (Ollama) for threat analysis
    No API costs, runs offline
    """
    
    def __init__(self, model: str = "llama3"):
        self.model = model
        self.base_url = "http://localhost:11434"
    
    def analyze_threat(self, network_risk, user_risk, context):
        """Analyze using local LLM"""
        
        prompt = f"""
        Analyze this cybersecurity threat:
        Network Risk: {network_risk}
        User Risk: {user_risk}
        Context: {json.dumps(context)}
        
        Recommend action: LOG, ALERT, RATE_LIMIT, or BLOCK
        Provide reasoning.
        
        Respond in JSON format.
        """
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
        )
        
        return json.loads(response.json()['response'])
```



---

## 7. Benefits

### Immediate Benefits (Phase 1)

1. **Explainable Decisions**
   - "Blocked because: Similar attack pattern detected 3 times in last hour"
   - Builds trust with security teams

2. **Context-Aware**
   - Considers time of day, user importance, business impact
   - Smarter than fixed thresholds

3. **Natural Language Interface**
   - Security team can query: "Why was this IP blocked?"
   - Agent explains reasoning

### Long-Term Benefits (Phase 2-3)

1. **Continuous Learning**
   - Learns from outcomes
   - Improves over time
   - Adapts to new attack patterns

2. **Proactive Defense**
   - Predicts attacks before they happen
   - Identifies patterns humans miss

3. **Reduced False Positives**
   - Learns what's normal for each user
   - Adapts thresholds dynamically

4. **Cost Savings**
   - Fewer false alarms = less wasted time
   - Better threat detection = less damage

---

## 8. Challenges

### Technical Challenges

1. **Latency**
   - LLM calls take 1-3 seconds
   - Solution: Use for high-risk only, cache decisions

2. **API Costs**
   - GPT-4: ~$0.03 per decision
   - Solution: Use local LLM (Ollama) or smaller models

3. **Reliability**
   - LLMs can be unpredictable
   - Solution: Validate outputs, have fallback

4. **Training Data**
   - RL needs labeled outcomes
   - Solution: Start with LLM, collect data, then train RL

### Operational Challenges

1. **Explainability**
   - Need to explain AI decisions to auditors
   - Solution: Log all reasoning, maintain audit trail

2. **Safety**
   - AI might make wrong decisions
   - Solution: Human-in-the-loop for critical actions

3. **Monitoring**
   - Need to monitor AI performance
   - Solution: Track accuracy, false positives, outcomes

---

## 9. Recommended Implementation Plan

### Week 1-2: Foundation
- [ ] Set up OpenAI API or Ollama
- [ ] Create basic AI agent class
- [ ] Integrate with existing system
- [ ] Test with historical data

### Week 3-4: Enhancement
- [ ] Add vector database for memory
- [ ] Implement decision history
- [ ] Add context gathering
- [ ] Test with live traffic

### Week 5-6: Learning
- [ ] Collect outcome data
- [ ] Implement feedback loop
- [ ] Start RL training (optional)
- [ ] Optimize prompts

### Week 7-8: Production
- [ ] Add monitoring and logging
- [ ] Implement safety checks
- [ ] Create dashboard
- [ ] Deploy to production

---

## 10. Quick Start (30 Minutes)

### Minimal LLM Integration

```python
# install
pip install openai

# src/simple_ai_agent.py
import openai

def ai_decide(network_risk, user_risk, api_key):
    client = openai.OpenAI(api_key=api_key)
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # Cheaper than GPT-4
        messages=[{
            "role": "user",
            "content": f"""
            Network risk: {network_risk}
            User risk: {user_risk}
            
            Should I LOG, ALERT, RATE_LIMIT, or BLOCK?
            Respond with just the action name.
            """
        }]
    )
    
    return response.choices[0].message.content.strip()

# Use it
action = ai_decide(0.95, 0.10, "your-api-key")
print(f"AI recommends: {action}")
```

---

## 11. Resources

### Learning Resources

**LLM Agents:**
- LangChain Documentation: https://python.langchain.com/
- OpenAI Agents Guide: https://platform.openai.com/docs/guides/agents
- AutoGen Framework: https://microsoft.github.io/autogen/

**Reinforcement Learning:**
- Stable Baselines3: https://stable-baselines3.readthedocs.io/
- OpenAI Gym: https://www.gymlibrary.dev/
- RL for Cybersecurity: Research papers

**Local LLMs:**
- Ollama: https://ollama.ai/
- Llama 3: https://llama.meta.com/
- Mistral: https://mistral.ai/

### Tools & Libraries

```bash
# LLM Integration
pip install openai anthropic langchain

# Vector Database
pip install chromadb pinecone-client

# RL Training
pip install stable-baselines3 gym

# Local LLM
# Install Ollama from https://ollama.ai/
ollama pull llama3
```

---

## 12. Conclusion

Integrating Agentic AI with your threat detection system will:

✅ Make decisions more intelligent and context-aware  
✅ Provide explainable reasoning for actions  
✅ Learn and improve over time  
✅ Adapt to new attack patterns  
✅ Reduce false positives  

**Start Simple:** Begin with LLM integration (Phase 1)  
**Iterate:** Add memory and learning (Phase 2)  
**Optimize:** Train RL agent for production (Phase 3)

Your current 60/40 fusion algorithm is excellent. Adding Agentic AI will make it even more powerful by adding reasoning, learning, and adaptation capabilities.

---

**Author:** Aarit Haldar  
**Date:** February 2026  
**Next Steps:** Start with Phase 1 - LLM integration
