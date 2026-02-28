# 📁 Project Structure

## Directory Layout

```
hybrid-threat-detection/
│
├── 📂 src/                              # Source Code
│   ├── ids_engine.py                   # Network Intrusion Detection System
│   ├── ueba_engine.py                  # User & Entity Behavior Analytics
│   ├── threat_fusion_engine.py         # Risk Fusion Algorithm (60/40)
│   ├── alert_system.py                 # Multi-channel Alert System
│   ├── enhanced_main.py                # Main Detection Loop
│   └── dashboard.py                    # Web Dashboard (Optional)
│
├── 📂 models/                           # Machine Learning Models
│   ├── ddos_model.pkl                  # Network Anomaly Detection Model
│   └── uba_model.pkl                   # User Behavior Model (Isolation Forest)
│
├── 📂 config/                           # Configuration Files
│   └── alert_config.json               # Alert System Settings
│
├── 📂 tests/                            # Testing Tools
│   └── attack_simulator.py             # DDoS Attack Simulator (300 threads)
│
├── 📂 docs/                             # Documentation
│   ├── STUDY_GUIDE_Part1_Overview.md   # Project Overview & Concepts
│   ├── STUDY_GUIDE_Part2_Code_Explained.md  # Code Walkthrough
│   ├── STUDY_GUIDE_Part3_Demo_QA.md    # Demo Script & Q&A
│   ├── STUDY_GUIDE_Quick_Reference.md  # Quick Reference Guide
│   ├── DEMO_DAY_GUIDE.md               # Complete Demo Day Guide
│   ├── README_Enhanced.md              # Enhanced Features Documentation
│   ├── PROJECT_OUTPUT_SUMMARY.md       # Test Results Summary
│   └── DASHBOARD_DEMO_SUMMARY.md       # Dashboard Documentation
│
├── 📂 presentation/                     # Presentation Materials
│   ├── Hybrid_Threat_Detection_Presentation.pptx  # Main Presentation
│   ├── Hybrid_Threat_Detection_Presentation_Updated.pptx  # With Novelty
│   └── presentation.md                 # Markdown Version
│
├── 📂 logs/                             # Generated Logs (Auto-created)
│   ├── threat_alerts.log               # Human-readable Log
│   └── threat_alerts.json              # Machine-readable Log
│
├── 📂 venv/                             # Python Virtual Environment
│
├── 📄 README.md                         # Main Project README
├── 📄 requirements.txt                  # Python Dependencies
├── 📄 .gitignore                        # Git Ignore Rules
├── 📄 run.py                            # Quick Start Script
└── 📄 PROJECT_STRUCTURE.md              # This File
```

## File Descriptions

### Core Source Files (`src/`)

#### `ids_engine.py` (Network Monitoring)
- **Purpose**: Monitors AWS CloudWatch metrics for network anomalies
- **Input**: CloudWatch NetworkIn, NetworkPacketsIn
- **Output**: Network risk score (0.0 to 1.0)
- **Key Features**:
  - 5-minute rolling window
  - Threshold-based detection
  - Dynamic risk calculation

#### `ueba_engine.py` (Behavior Analytics)
- **Purpose**: Analyzes user behavior from CloudTrail logs
- **Input**: AWS CloudTrail audit logs
- **Output**: User risk score (0.0 to 1.0)
- **Key Features**:
  - Feature engineering (time, volume, diversity)
  - Isolation Forest ML model
  - Anomaly detection

#### `threat_fusion_engine.py` (Risk Fusion)
- **Purpose**: Combines network and user risks
- **Input**: Network risk, User risk
- **Output**: Final risk score + Threat level
- **Key Features**:
  - **Novel 60/40 weighted fusion**
  - Four threat levels (CRITICAL, HIGH, MEDIUM, LOW)
  - Context-aware classification

#### `alert_system.py` (Alerting)
- **Purpose**: Multi-channel alert management
- **Output**: Console alerts, Email alerts, Log files
- **Key Features**:
  - Color-coded console alerts
  - HTML email notifications
  - Rate limiting (10 emails/hour)
  - Configurable thresholds

#### `enhanced_main.py` (Main System)
- **Purpose**: Orchestrates all components
- **Features**:
  - 10-second detection cycles
  - Statistics tracking
  - Graceful error handling
  - Continuous monitoring

#### `dashboard.py` (Web Interface)
- **Purpose**: Real-time web dashboard
- **Features**:
  - 4 interactive charts
  - Auto-refresh (5 seconds)
  - Status cards
  - Alerts table

### Configuration (`config/`)

#### `alert_config.json`
```json
{
  "email": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your-email@gmail.com",
    "recipients": ["admin@company.com"]
  },
  "thresholds": {
    "critical": 0.8,
    "high": 0.6,
    "medium": 0.4
  },
  "rate_limiting": {
    "max_emails_per_hour": 10
  }
}
```

### Testing (`tests/`)

#### `attack_simulator.py`
- **Purpose**: Simulates DDoS attack for testing
- **Parameters**:
  - 300 concurrent threads
  - 60-second duration
  - HTTP GET flood
- **Target**: EC2 instance

### Documentation (`docs/`)

#### Study Guides (Read in Order)
1. **Part 1 - Overview**: Concepts, architecture, math
2. **Part 2 - Code Explained**: Line-by-line code walkthrough
3. **Part 3 - Demo & Q&A**: Demo script, questions, answers
4. **Quick Reference**: Daily review guide

#### Other Documentation
- **DEMO_DAY_GUIDE.md**: Complete demo day preparation
- **README_Enhanced.md**: Enhanced features details
- **PROJECT_OUTPUT_SUMMARY.md**: Test results and metrics
- **DASHBOARD_DEMO_SUMMARY.md**: Dashboard features

### Presentation (`presentation/`)

#### PowerPoint Files
- **Main**: Original presentation
- **Updated**: With novelty analysis and literature comparison

#### Markdown
- **presentation.md**: Text version for editing

## Quick Start Commands

### Run Detection System
```bash
python run.py
# OR
python src/enhanced_main.py
```

### Run with Attack Test
```bash
# Terminal 1
python src/enhanced_main.py

# Terminal 2
python tests/attack_simulator.py
```

### Run Dashboard
```bash
python src/dashboard.py
# Open: http://localhost:8050
```

## File Sizes (Approximate)

```
Source Code:        ~50 KB
Documentation:      ~500 KB
Presentation:       ~2 MB
Models:            ~100 KB
Total:             ~3 MB
```

## Dependencies

See `requirements.txt` for complete list:
- boto3 (AWS SDK)
- pandas (Data processing)
- scikit-learn (ML models)
- dash/plotly (Dashboard)

## Generated Files

### Logs (Auto-created)
- `logs/threat_alerts.log` - Created on first alert
- `logs/threat_alerts.json` - Created on first alert

### Temporary Files
- `__pycache__/` - Python bytecode (ignored)
- `.vscode/` - IDE settings (ignored)

## Important Notes

1. **AWS Credentials**: Required for CloudWatch and CloudTrail access
2. **Models**: Pre-trained ML models in `models/` directory
3. **Logs**: Automatically created in `logs/` directory
4. **Config**: Edit `config/alert_config.json` for email settings

## For Demo Day

**Essential Files:**
- `src/enhanced_main.py` - Main system
- `tests/attack_simulator.py` - Attack test
- `docs/DEMO_DAY_GUIDE.md` - Demo script
- `docs/STUDY_GUIDE_Quick_Reference.md` - Quick reference
- `presentation/Hybrid_Threat_Detection_Presentation_Updated.pptx` - Slides

**Quick Commands:**
```bash
# 1. Start system
python run.py

# 2. Launch attack
python tests/attack_simulator.py

# 3. View logs
type logs\threat_alerts.log
```

---

**Clean, organized, and ready for demo! 🚀**
