# 💻 Final Demo Day Execution Guide

This guide contains the exact commands for your Demo Day flow. The architecture has been refined so your `enhanced_main_with_agent.py` acts as the true "brain" hitting AWS, while the beautiful `web_dashboard.py` acts as a pure visual display connected to it.

---

### Terminal 1: Run the Agentic AI (Optional but Recommended)
*Ensure Ollama is running in the background for real-time reasoning:*
```cmd
ollama serve
```

### Terminal 2: Start the Main Brain (Detection & AWS Response)
*This is your main focus during the demo. It runs the loops and actively blocks IPs on AWS:*
```cmd
cd "C:\Users\aarit\Downloads\unified threat detection"
venv\Scripts\activate.bat
python src\enhanced_main_with_agent.py
```

### Terminal 3: Start the Premium Visualization Dashboard
*This dashboard is now a lightweight "Thin Client" perfectly synced to the main brain. Keep it running on a side window!*
```cmd
cd "C:\Users\aarit\Downloads\unified threat detection"
venv\Scripts\activate.bat
python src\web_dashboard.py
```

### Terminal 4: Run the Attack Simulation
*When you're ready to show the system responding to a live threat:*
```cmd
cd "C:\Users\aarit\Downloads\unified threat detection"
venv\Scripts\activate.bat
python tests\attack_simulator.py
```

---

### Core Evaluation Test (Optional)
*If you need to run the pure 4/4 scenario script:*
```cmd
python test_ollama_scenarios.py
```
