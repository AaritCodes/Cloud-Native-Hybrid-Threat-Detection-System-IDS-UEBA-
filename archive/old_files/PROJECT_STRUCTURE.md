# Project Structure

**Date:** March 3, 2026  
**Author:** Aarit Haldar

---

## Clean, Organized Project Structure

```
unified-threat-detection/
│
├── 📄 README.md                          # Main project documentation
├── 📄 START_HERE.md                      # Getting started guide
├── 📄 DOCUMENTATION_INDEX.md             # Navigation to all docs
├── 📄 PROJECT_SUMMARY.md                 # Quick project overview
├── 📄 AGENTIC_AI_EXPLAINED.md           # AI integration explanation
├── 📄 OLLAMA_SETUP_GUIDE.md             # Ollama setup instructions
├── 📄 CONTRIBUTING.md                    # Contribution guidelines
├── 📄 LICENSE                            # MIT License
├── 📄 requirements.txt                   # Python dependencies
├── 📄 .gitignore                         # Git ignore rules
│
├── 📁 demo_materials/                    # Demo day materials
│   ├── DEMO_DAY_QUICK_CARD_ENHANCED.md  # Quick reference card (PRINT THIS!)
│   ├── DEMO_DAY_QUICK_CARD_ENHANCED.pdf
│   ├── DEMO_DAY_DETAILED_EXPLANATIONS.md # Comprehensive demo guide
│   └── DEMO_DAY_DETAILED_EXPLANATIONS.pdf
│
├── 📁 docs/                              # Complete documentation
│   ├── AGENTIC_AI_INTEGRATION_GUIDE.md  # AI technical guide
│   ├── CODE_DOCUMENTATION.md            # Code walkthrough
│   ├── COMPLETE_PROJECT_GUIDE.md        # Full project guide
│   ├── DATASET_AND_MODEL_GUIDE.md       # Dataset & model details
│   ├── DEMO_COMMANDS.md                 # Full demo commands
│   ├── DEMO_QA.md                       # 30 Q&A for demo
│   └── *.pdf                            # PDF versions of all docs
│
├── 📁 src/                               # Source code
│   ├── enhanced_main_with_agent.py      # Main system with AI
│   ├── ids_engine.py                    # IDS engine
│   ├── ueba_engine.py                   # UEBA engine
│   ├── threat_fusion_engine.py          # 60/40 fusion algorithm
│   ├── alert_system.py                  # Alert system
│   ├── autonomous_response_agent.py     # Autonomous response
│   ├── ollama_agent.py                  # Ollama AI agent
│   ├── intelligent_agent.py             # OpenAI agent (alternative)
│   ├── dashboard.py                     # Web dashboard
│   └── agent_tools.py                   # Agent tools
│
├── 📁 tests/                             # Test files
│   └── attack_simulator.py              # DDoS attack simulator
│
├── 📁 models/                            # ML models
│   ├── ddos_model.pkl                   # IDS model
│   └── uba_model.pkl                    # UEBA model
│
├── 📁 config/                            # Configuration
│   ├── alert_config.json                # Alert configuration
│   └── alert_config.json.template       # Template
│
├── 📁 logs/                              # Log files
│   ├── autonomous_response.log          # Response logs
│   ├── threat_alerts.json               # Alert logs
│   └── decisions.db                     # AI decision database
│
├── 📁 presentation/                      # Presentations
│   ├── *.pptx                           # PowerPoint files
│   └── *.pdf                            # PDF versions
│
├── 📁 scripts/                           # Utility scripts
│   ├── convert_all_md_to_pdf.py        # MD to PDF converter
│   └── convert_pptx_to_pdf.py          # PPTX to PDF converter
│
├── 📁 archive/                           # Old/redundant files
│   └── *.pdf                            # Archived documents
│
└── 📁 venv/                              # Python virtual environment
```

---

## Essential Files for Demo Day

### Must Print:
1. **`demo_materials/DEMO_DAY_QUICK_CARD_ENHANCED.pdf`** (2 pages)
   - Quick reference card
   - Keep on desk during demo

### Must Read Tonight:
2. **`demo_materials/DEMO_DAY_DETAILED_EXPLANATIONS.pdf`** (15+ pages)
   - Comprehensive explanations
   - Q&A preparation
   
3. **`docs/DEMO_QA.pdf`** (30 pages)
   - 30 common questions with answers

### Backup References:
4. **`docs/DEMO_COMMANDS.pdf`** (30 pages)
   - Full demo walkthrough
   
5. **`AGENTIC_AI_EXPLAINED.pdf`**
   - AI integration details

---

## File Categories

### 📘 Documentation (Root)
- **README.md** - Start here for project overview
- **START_HERE.md** - Quick setup guide
- **DOCUMENTATION_INDEX.md** - Find all documentation
- **PROJECT_SUMMARY.md** - Executive summary
- **AGENTIC_AI_EXPLAINED.md** - AI integration explained
- **OLLAMA_SETUP_GUIDE.md** - Setup Ollama
- **CONTRIBUTING.md** - How to contribute

### 🎯 Demo Materials
- **demo_materials/** - Everything for demo day
  - Quick card (print this!)
  - Detailed explanations (read this!)

### 📚 Complete Documentation
- **docs/** - All detailed documentation
  - Technical guides
  - Code documentation
  - Q&A preparation
  - Demo commands

### 💻 Source Code
- **src/** - All Python source code
  - Main system
  - Detection engines
  - AI agents
  - Alert system

### 🧪 Testing
- **tests/** - Test files
  - Attack simulator for demo

### 🤖 Models
- **models/** - Trained ML models
  - IDS model (DDoS detection)
  - UEBA model (user behavior)

### ⚙️ Configuration
- **config/** - Configuration files
  - Alert settings
  - Email configuration

### 📊 Logs
- **logs/** - System logs
  - Response logs
  - Alert logs
  - AI decisions

### 🎤 Presentations
- **presentation/** - All presentations
  - PowerPoint files
  - PDF versions

### 🛠️ Scripts
- **scripts/** - Utility scripts
  - Conversion tools
  - Helper scripts

### 📦 Archive
- **archive/** - Old/redundant files
  - Kept for reference
  - Not needed for demo

---

## Quick Navigation

### For Demo Day:
```
demo_materials/DEMO_DAY_QUICK_CARD_ENHANCED.pdf
demo_materials/DEMO_DAY_DETAILED_EXPLANATIONS.pdf
docs/DEMO_QA.pdf
```

### To Run System:
```
python src/enhanced_main_with_agent.py
python tests/attack_simulator.py
```

### To Read Documentation:
```
README.md
docs/COMPLETE_PROJECT_GUIDE.pdf
docs/CODE_DOCUMENTATION.pdf
```

### To Setup:
```
START_HERE.md
OLLAMA_SETUP_GUIDE.md
requirements.txt
```

---

## File Counts

- **Markdown files:** 9 (root) + 6 (docs) = 15 total
- **PDF files:** ~30 total
- **Python files:** 10 source files
- **Presentations:** 8 files (4 PPTX + 4 PDF)
- **Models:** 2 ML models
- **Config:** 2 files
- **Tests:** 1 attack simulator

---

## Clean and Organized!

✅ All files properly categorized
✅ Demo materials in dedicated folder
✅ Documentation well organized
✅ Source code in src/
✅ Old files archived
✅ Easy to navigate
✅ Professional structure

**Project is demo-ready! 🚀**
