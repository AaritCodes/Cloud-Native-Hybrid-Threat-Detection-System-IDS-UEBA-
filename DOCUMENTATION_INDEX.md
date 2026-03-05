# Documentation Index
## Complete Guide to Project Documentation

**Last Updated:** February 28, 2026

---

## Start Here

### New to the Project?
1. Read **README.md** - Project overview and quick start
2. Read **PROJECT_SUMMARY.md** - Quick reference guide
3. Read **docs/COMPLETE_PROJECT_GUIDE.md** - Full project explanation

### Preparing for Demo Day?
1. Read **docs/DEMO_COMMANDS.md** - Step-by-step demo guide
2. Read **docs/DEMO_QA.md** - 30 Q&A with detailed answers
3. Practice running the demo

### Want to Understand the Code?
1. Read **docs/CODE_DOCUMENTATION.md** - Detailed code walkthrough
2. Read **docs/DATASET_AND_MODEL_GUIDE.md** - Dataset and ML choices
3. Explore source code in **src/** directory

---

## Documentation Structure

### Root Level Documents

#### README.md
**Purpose:** Main project documentation  
**Contents:**
- Project overview
- Key features
- System architecture
- Quick start guide
- Installation instructions
- Performance metrics
- AWS configuration

**When to Read:** First document to read for project overview

---

#### PROJECT_SUMMARY.md
**Purpose:** Quick reference and navigation guide  
**Contents:**
- File organization
- Quick start for different use cases
- Key numbers to remember
- Documentation map
- Common questions
- Demo day checklist

**When to Read:** Need quick reference or don't know where to start

---

#### DOCUMENTATION_INDEX.md (This File)
**Purpose:** Navigate all documentation  
**Contents:**
- Complete documentation structure
- What each document contains
- When to read each document
- Quick links

**When to Read:** Need to find specific information

---

### Core Documentation (docs/)

#### docs/COMPLETE_PROJECT_GUIDE.md
**Purpose:** Comprehensive project explanation  
**Contents:**
1. Project Overview
2. Problem Statement
3. Literature Survey
4. Proposed Solution
5. System Architecture
6. Novel Contribution (60/40 fusion)
7. Implementation Details
8. Testing and Validation
9. Results and Performance
10. Future Enhancements

**Length:** ~50 pages  
**Reading Time:** 30-45 minutes  
**When to Read:** 
- Understanding the entire project
- Preparing presentation
- Writing project report
- Answering "why" questions

**Key Sections:**
- Section 6: Novel 60/40 fusion algorithm (most important)
- Section 9: Results and performance metrics
- Section 3: Literature survey and research gap

---

#### docs/DATASET_AND_MODEL_GUIDE.md
**Purpose:** Explain dataset and ML model choices  
**Contents:**
1. Dataset Overview
2. IDS Dataset (Network Metrics)
3. UEBA Dataset (User Behavior)
4. Why Isolation Forest?
5. Model Training Process
6. Parameter Selection
7. Alternative Models Considered
8. Model Evaluation

**Length:** ~35 pages  
**Reading Time:** 25-35 minutes  
**When to Read:**
- Questions about dataset
- Questions about ML algorithm
- Questions about model training
- Questions about parameter selection

**Key Sections:**
- Section 4: Why Isolation Forest (most asked)
- Section 6: Parameter selection rationale
- Section 7: Why not other algorithms

---

#### docs/CODE_DOCUMENTATION.md
**Purpose:** Detailed code walkthrough  
**Contents:**
1. Project Structure
2. IDS Engine (ids_engine.py)
3. UEBA Engine (ueba_engine.py)
4. Threat Fusion Engine (threat_fusion_engine.py)
5. Autonomous Response Agent (autonomous_response_agent.py)
6. Alert System (alert_system.py)
7. Main System (enhanced_main_with_agent.py)
8. Attack Simulator (tests/attack_simulator.py)

**Length:** ~40 pages  
**Reading Time:** 30-40 minutes  
**When to Read:**
- Understanding how code works
- Modifying or extending code
- Debugging issues
- Code review

**Key Sections:**
- Section 4: Threat Fusion (60/40 algorithm implementation)
- Section 5: Autonomous Response Agent (decision logic)
- Complete Detection Flow diagram

---

#### docs/DEMO_COMMANDS.md
**Purpose:** Step-by-step demo execution guide  
**Contents:**
- Pre-demo checklist
- Demo workflow timeline
- Step-by-step commands
- Expected output for each step
- What to say during demo
- Troubleshooting
- Key talking points

**Length:** ~20 pages  
**Reading Time:** 15-20 minutes  
**When to Read:**
- Before demo day
- During demo practice
- As reference during demo

**Key Sections:**
- Demo Workflow (3-4 minute timeline)
- Step 5: Explain Agent Decision
- Key Talking Points

---

#### docs/DEMO_QA.md
**Purpose:** Demo day Q&A preparation  
**Contents:**
30 questions with detailed answers covering:
1. Project Overview (Q1-Q3)
2. Dataset (Q4-Q7)
3. Model and Algorithm (Q8-Q11)
4. 60/40 Fusion (Q12-Q14)
5. Implementation (Q15-Q17)
6. Performance (Q18-Q20)
7. AWS Integration (Q21-Q23)
8. Autonomous Response (Q24-Q26)
9. Testing and Validation (Q27-Q28)
10. Future Work (Q29-Q30)

**Length:** ~30 pages  
**Reading Time:** 25-35 minutes  
**When to Read:**
- Preparing for demo day
- Before presentation
- Practicing Q&A
- As reference during Q&A

**Key Questions:**
- Q12: Why 60/40 weighting?
- Q8: Which ML algorithm and why?
- Q18: Performance metrics
- Q4: What dataset did you use?

---

### Source Code Documentation

#### src/ids_engine.py
**Lines:** ~150  
**Purpose:** Network anomaly detection  
**Key Methods:**
- `get_metric()` - Fetch CloudWatch metrics
- `detect()` - Run anomaly detection

**Documentation:** See docs/CODE_DOCUMENTATION.md Section 2

---

#### src/ueba_engine.py
**Lines:** ~200  
**Purpose:** User behavior analytics  
**Key Methods:**
- `fetch_cloudtrail_logs()` - Get CloudTrail logs
- `extract_features()` - Extract behavioral features
- `detect()` - Run anomaly detection

**Documentation:** See docs/CODE_DOCUMENTATION.md Section 3

---

#### src/threat_fusion_engine.py
**Lines:** ~50  
**Purpose:** 60/40 weighted risk correlation  
**Key Function:**
- `combine_risks()` - Apply 60/40 fusion

**Documentation:** See docs/CODE_DOCUMENTATION.md Section 4

---

#### src/autonomous_response_agent.py
**Lines:** ~500  
**Purpose:** Automated threat response  
**Key Methods:**
- `take_action()` - Decide and execute response
- `block_ip_address()` - Block via Security Group
- `check_and_unblock_expired()` - Auto-unblock

**Documentation:** See docs/CODE_DOCUMENTATION.md Section 5

---

#### src/alert_system.py
**Lines:** ~200  
**Purpose:** Multi-channel alerting  
**Key Methods:**
- `create_alert()` - Create and send alerts
- `send_email_alert()` - Email notifications

**Documentation:** See docs/CODE_DOCUMENTATION.md Section 6

---

#### src/enhanced_main_with_agent.py
**Lines:** ~300  
**Purpose:** Main system integration  
**Key Methods:**
- `run_detection_cycle()` - Complete detection cycle
- `run()` - Main loop

**Documentation:** See docs/CODE_DOCUMENTATION.md Section 7

---

### Configuration Files

#### config/alert_config.json
**Purpose:** Email and alert settings  
**Format:** JSON  
**Contents:**
- SMTP server settings
- Email credentials
- Alert recipients

**Template:** config/alert_config.json.template

---

#### requirements.txt
**Purpose:** Python dependencies  
**Contents:**
- boto3 (AWS SDK)
- scikit-learn (ML)
- pandas (data processing)
- numpy (numerical)
- requests (HTTP)

**Install:** `pip install -r requirements.txt`

---

### Presentation Materials

#### presentation/AICS_Project_Review_Presentation.pptx
**Purpose:** AICS project review presentation  
**Slides:** 10  
**Contents:**
- Title slide
- Problem statement
- Literature survey
- Objectives
- Proposed methodology (2 slides)
- Dataset description (2 slides)
- References

---

#### AWS_Hybrid_Threat_Detection.pdf
**Purpose:** Project documentation PDF  
**Pages:** 17  
**Contents:** Complete project documentation

---

#### presentation_final.pdf
**Purpose:** Final presentation PDF  
**Pages:** 17  
**Contents:** Presentation slides

---

## Quick Navigation

### "I need to..."

**...understand the project quickly**
→ README.md → PROJECT_SUMMARY.md

**...prepare for demo day**
→ docs/DEMO_COMMANDS.md → docs/DEMO_QA.md

**...understand the 60/40 fusion**
→ docs/COMPLETE_PROJECT_GUIDE.md (Section 6)
→ docs/DEMO_QA.md (Q12-Q14)

**...understand the dataset**
→ docs/DATASET_AND_MODEL_GUIDE.md (Sections 2-3)

**...understand why Isolation Forest**
→ docs/DATASET_AND_MODEL_GUIDE.md (Section 4)

**...understand the code**
→ docs/CODE_DOCUMENTATION.md

**...answer questions about performance**
→ docs/DEMO_QA.md (Q18-Q20)
→ docs/COMPLETE_PROJECT_GUIDE.md (Section 9)

**...run the demo**
→ docs/DEMO_COMMANDS.md

**...modify the code**
→ docs/CODE_DOCUMENTATION.md
→ Source files in src/

---

## Reading Order Recommendations

### For Demo Day Preparation (2-3 hours)
1. PROJECT_SUMMARY.md (15 min)
2. docs/DEMO_COMMANDS.md (20 min)
3. docs/DEMO_QA.md (30 min)
4. Practice demo (60 min)
5. Review key sections (30 min)

### For Complete Understanding (4-5 hours)
1. README.md (20 min)
2. docs/COMPLETE_PROJECT_GUIDE.md (45 min)
3. docs/DATASET_AND_MODEL_GUIDE.md (35 min)
4. docs/CODE_DOCUMENTATION.md (40 min)
5. docs/DEMO_QA.md (30 min)
6. Source code review (90 min)

### For Quick Reference (30 minutes)
1. PROJECT_SUMMARY.md (15 min)
2. docs/DEMO_QA.md - Quick Answer Cheat Sheet (5 min)
3. Key sections from COMPLETE_PROJECT_GUIDE.md (10 min)

---

## Document Statistics

| Document | Pages | Words | Reading Time |
|----------|-------|-------|--------------|
| README.md | 12 | 3,500 | 20 min |
| PROJECT_SUMMARY.md | 10 | 2,800 | 15 min |
| COMPLETE_PROJECT_GUIDE.md | 50 | 12,000 | 45 min |
| DATASET_AND_MODEL_GUIDE.md | 35 | 9,000 | 35 min |
| CODE_DOCUMENTATION.md | 40 | 10,000 | 40 min |
| DEMO_COMMANDS.md | 20 | 5,000 | 20 min |
| DEMO_QA.md | 30 | 8,000 | 30 min |
| **Total** | **197** | **50,300** | **3.5 hours** |

---

## Key Concepts Index

### 60/40 Fusion Algorithm
- docs/COMPLETE_PROJECT_GUIDE.md - Section 6
- docs/DEMO_QA.md - Q12-Q14
- docs/CODE_DOCUMENTATION.md - Section 4

### Isolation Forest
- docs/DATASET_AND_MODEL_GUIDE.md - Section 4
- docs/DEMO_QA.md - Q8-Q11

### Autonomous Response
- docs/COMPLETE_PROJECT_GUIDE.md - Section 4
- docs/CODE_DOCUMENTATION.md - Section 5
- docs/DEMO_QA.md - Q24-Q26

### Performance Metrics
- docs/COMPLETE_PROJECT_GUIDE.md - Section 9
- docs/DEMO_QA.md - Q18-Q20
- README.md - Key Results section

### AWS Integration
- docs/COMPLETE_PROJECT_GUIDE.md - Section 7
- docs/DEMO_QA.md - Q21-Q23
- README.md - AWS Configuration section

---

## Version History

**v1.0 - February 28, 2026**
- Initial comprehensive documentation
- All core documents created
- Demo day ready

---

## Need Help?

**Can't find what you're looking for?**
1. Check PROJECT_SUMMARY.md - Documentation Map section
2. Use Ctrl+F to search within documents
3. Check the Quick Navigation section above

**Still stuck?**
- Review README.md for project overview
- Check docs/DEMO_QA.md for common questions
- Refer to source code comments

---

**Author:** Aarit Haldar  
**Date:** February 28, 2026  
**Institution:** Engineering College  
**USN:** ENG24CY0073
