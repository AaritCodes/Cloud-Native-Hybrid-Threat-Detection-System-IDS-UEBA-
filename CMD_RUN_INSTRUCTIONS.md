# 💻 CMD Execution Cheat Sheet

This guide contains the **exact** commands you need to copy-paste if you are using the traditional Windows **Command Prompt (CMD)** instead of PowerShell. 

---

### Step 1: Pre-Demo Setup

*Open a Command Prompt (`cmd.exe`) and navigate to your project folder:*
```cmd
cd "C:\Users\aarit\Downloads\unified threat detection"
```

*Activate the virtual environment (This is different from PowerShell):*
```cmd
venv\Scripts\activate.bat
```

*Ensure your AI is running (Optional: do this in a new, separate CMD window):*
```cmd
ollama serve
```

---

### Step 2: Running the Full Agentic AI Demo

*In your first terminal (where the `venv` is activated):*
```cmd
python src\enhanced_main_with_agent.py
```
*(This starts the monitoring system. Keep it running to watch the AI's real-time reasoning).*

*Open a **second** Command Prompt window specifically for simulating the attack:*
```cmd
cd "C:\Users\aarit\Downloads\unified threat detection"
venv\Scripts\activate.bat
python tests\attack_simulator.py
```

---

### Step 3: Running the Core Evaluation Test (Optional)

*If you want to run the clean 4/4 matching scenario script we just fixed, use this command (ensure `venv` is activated):*
```cmd
python test_ollama_scenarios.py
```

### Step 4: Running the Streamlit Dashboard (Optional)

*If your project has the visual dashboard ready, run it with:*
```cmd
python -m streamlit run src\dashboard.py
```
