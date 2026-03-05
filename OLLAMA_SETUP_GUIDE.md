# Ollama Setup Guide
## Local Agentic AI Integration (Free, No API Costs)

**Date:** February 28, 2026

---

## 🎯 Why Ollama?

✅ **Free** - No API costs  
✅ **Private** - Data stays on your machine  
✅ **Offline** - Works without internet  
✅ **Fast** - Local inference  
✅ **Multiple Models** - Llama 3, Mistral, Phi, etc.  

---

## 📦 Installation

### Step 1: Install Ollama

**Windows:**
1. Download from: https://ollama.ai/download/windows
2. Run the installer
3. Ollama will start automatically

**Mac:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Step 2: Verify Installation

```bash
ollama --version
```

Should show: `ollama version 0.x.x`

### Step 3: Start Ollama Server

**Windows:** Already running (check system tray)

**Mac/Linux:**
```bash
ollama serve
```

Keep this terminal open!

---

## 🤖 Download Models

### Recommended Models

**1. Llama 3 (Best Quality)**
```bash
ollama pull llama3
```
- Size: 4.7 GB
- RAM: 8 GB minimum
- Quality: Excellent
- Speed: Medium

**2. Mistral (Balanced)**
```bash
ollama pull mistral
```
- Size: 4.1 GB
- RAM: 8 GB minimum
- Quality: Very Good
- Speed: Fast

**3. Phi-3 (Lightweight)**
```bash
ollama pull phi3
```
- Size: 2.3 GB
- RAM: 4 GB minimum
- Quality: Good
- Speed: Very Fast

**4. Llama 3.1 (Latest)**
```bash
ollama pull llama3.1
```
- Size: 4.7 GB
- RAM: 8 GB minimum
- Quality: Excellent
- Speed: Medium

### Check Downloaded Models

```bash
ollama list
```

---

## 🚀 Quick Test

### Test 1: Basic Chat

```bash
ollama run llama3
```

Type: "Hello, how are you?"  
Press Ctrl+D to exit

### Test 2: API Test

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

Should return JSON response.

---

## 🔧 Integration with Your Project

### Step 1: Test the Ollama Agent

```bash
python src/ollama_agent.py
```

Expected output:
```
✅ Ollama connected. Using model: llama3

Analyzing threat...

🤖 AI Decision:
   Action: RATE_LIMIT
   Confidence: 0.85
   Reasoning: High network risk but normal user behavior...
```

### Step 2: Integrate with Main System

Modify `src/enhanced_main_with_agent.py`:

```python
from src.ollama_agent import OllamaAgent

class EnhancedThreatDetectionWithAI:
    def __init__(self, security_group_id):
        # Existing components
        self.ids = IDSEngine("models/ddos_model.pkl")
        self.ueba = UEBAEngine("models/uba_model.pkl")
        
        # NEW: Ollama AI Agent
        self.ai_agent = OllamaAgent(
            model="llama3",  # or "mistral", "phi3"
            base_url="http://localhost:11434"
        )
        
        # Traditional agent as fallback
        self.traditional_agent = AutonomousResponseAgent(
            security_group_id=security_group_id
        )
    
    def run_detection_cycle(self):
        # ... existing detection code ...
        
        # Use AI for medium+ threats
        if final_risk >= 0.4:
            print("\n🤖 AI Agent Analyzing...")
            
            context = {
                'time': datetime.now().isoformat(),
                'day_of_week': datetime.now().strftime('%A'),
                'business_hours': 9 <= datetime.now().hour <= 17,
                'recent_attacks': self._count_recent_attacks(),
                'user_importance': 'normal'
            }
            
            ai_decision = self.ai_agent.analyze_and_decide(
                network_risk, user_risk, ip, context
            )
            
            print(f"   Action: {ai_decision['action']}")
            print(f"   Reasoning: {ai_decision['reasoning']}")
            
            action = ai_decision['action']
        else:
            action = "LOG"
```

---

## ⚙️ Configuration

### Model Selection

**For Best Quality:**
```python
agent = OllamaAgent(model="llama3")
```

**For Speed:**
```python
agent = OllamaAgent(model="phi3")
```

**For Balance:**
```python
agent = OllamaAgent(model="mistral")
```

### Custom Ollama URL

If running Ollama on different port:
```python
agent = OllamaAgent(
    model="llama3",
    base_url="http://localhost:8080"
)
```

---

## 📊 Performance Comparison

| Model | Size | RAM | Speed | Quality | Best For |
|-------|------|-----|-------|---------|----------|
| Llama 3 | 4.7GB | 8GB | Medium | ⭐⭐⭐⭐⭐ | Production |
| Mistral | 4.1GB | 8GB | Fast | ⭐⭐⭐⭐ | Balanced |
| Phi-3 | 2.3GB | 4GB | Very Fast | ⭐⭐⭐ | Testing |
| Llama 3.1 | 4.7GB | 8GB | Medium | ⭐⭐⭐⭐⭐ | Latest |

---

## 🔍 Testing

### Test Script

Create `test_ollama.py`:

```python
from src.ollama_agent import OllamaAgent
from datetime import datetime

# Initialize
agent = OllamaAgent(model="llama3")

# Test cases
test_cases = [
    # Normal traffic
    {"network": 0.05, "user": 0.10, "expected": "LOG"},
    
    # Medium threat
    {"network": 0.50, "user": 0.40, "expected": "ALERT"},
    
    # High threat
    {"network": 0.95, "user": 0.10, "expected": "RATE_LIMIT"},
    
    # Critical threat
    {"network": 0.95, "user": 0.90, "expected": "BLOCK"}
]

for i, test in enumerate(test_cases, 1):
    print(f"\nTest {i}:")
    print(f"  Network: {test['network']}, User: {test['user']}")
    
    decision = agent.analyze_and_decide(
        network_risk=test['network'],
        user_risk=test['user'],
        ip_address="192.168.1.1",
        context={'time': datetime.now().isoformat()}
    )
    
    print(f"  Expected: {test['expected']}")
    print(f"  Got: {decision['action']}")
    print(f"  Reasoning: {decision['reasoning']}")
    print(f"  Match: {'✅' if decision['action'] == test['expected'] else '❌'}")
```

Run:
```bash
python test_ollama.py
```

---

## 🐛 Troubleshooting

### Issue 1: "Cannot connect to Ollama"

**Solution:**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it
ollama serve
```

### Issue 2: "Model not found"

**Solution:**
```bash
# List available models
ollama list

# Pull the model
ollama pull llama3
```

### Issue 3: "Out of memory"

**Solution:**
- Use smaller model: `phi3` instead of `llama3`
- Close other applications
- Increase system RAM

### Issue 4: Slow responses

**Solution:**
- Use faster model: `phi3` or `mistral`
- Reduce context in prompts
- Use GPU if available

---

## 💡 Tips & Best Practices

### 1. Model Selection
- **Development:** Use `phi3` (fast, small)
- **Testing:** Use `mistral` (balanced)
- **Production:** Use `llama3` (best quality)

### 2. Prompt Optimization
- Keep prompts concise
- Include only relevant context
- Use JSON format for structured output

### 3. Caching
- Ollama caches model in RAM
- First request is slower
- Subsequent requests are fast

### 4. Monitoring
```python
# Check agent statistics
stats = agent.get_statistics()
print(f"Total decisions: {stats['total_decisions']}")
print(f"Model: {stats['model']}")
```

---

## 🔄 Updating Models

### Update to Latest Version

```bash
# Update Llama 3
ollama pull llama3

# Update Mistral
ollama pull mistral
```

### Remove Old Models

```bash
# List models
ollama list

# Remove model
ollama rm old-model-name
```

---

## 📈 Performance Benchmarks

**On typical laptop (16GB RAM, i7 CPU):**

| Model | First Request | Subsequent | Tokens/sec |
|-------|--------------|------------|------------|
| Llama 3 | 3-5s | 1-2s | 20-30 |
| Mistral | 2-4s | 1s | 30-40 |
| Phi-3 | 1-2s | 0.5s | 40-50 |

---

## 🎯 Next Steps

1. **Install Ollama** ✅
2. **Pull model** (llama3 recommended)
3. **Test** `python src/ollama_agent.py`
4. **Integrate** with main system
5. **Monitor** performance
6. **Optimize** based on results

---

## 📚 Resources

**Official:**
- Ollama Website: https://ollama.ai/
- Ollama GitHub: https://github.com/ollama/ollama
- Model Library: https://ollama.ai/library

**Documentation:**
- API Docs: https://github.com/ollama/ollama/blob/main/docs/api.md
- Model Cards: https://ollama.ai/library/llama3

**Community:**
- Discord: https://discord.gg/ollama
- Reddit: r/ollama

---

## ✅ Checklist

- [ ] Ollama installed
- [ ] Ollama server running
- [ ] Model downloaded (llama3)
- [ ] Test script works
- [ ] Integrated with main system
- [ ] Performance acceptable
- [ ] Ready for production

---

**You're now ready to use local Agentic AI with zero API costs! 🚀**

**Ollama gives you the power of GPT-4 level reasoning without any ongoing costs.**
