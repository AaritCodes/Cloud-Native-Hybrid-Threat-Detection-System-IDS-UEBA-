"""
Premium Cybersecurity Dashboard for Hybrid Threat Detection System
Flask-based web UI with real-time threat monitoring, AI reasoning display,
and stunning dark glassmorphism design.
"""

import sys
import os
import json
import threading
import time
from datetime import datetime
from collections import deque
from flask import Flask, render_template_string, jsonify

# Fix Windows encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Engines are now running externally via enhanced_main_with_agent.py
# The dashboard acts as a stateless thin client reading web_state.json

import warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)

# ── Global state ──
MAX_POINTS = 50
state = {
    "timestamps": deque(maxlen=MAX_POINTS),
    "network_risk": deque(maxlen=MAX_POINTS),
    "user_risk": deque(maxlen=MAX_POINTS),
    "final_risk": deque(maxlen=MAX_POINTS),
    "actions": deque(maxlen=MAX_POINTS),
    "events": deque(maxlen=20),
    "stats": {
        "total_cycles": 0,
        "log_count": 0,
        "alert_count": 0,
        "rate_limit_count": 0,
        "block_count": 0,
        "ai_available": False,
        "model": "none",
        "start_time": datetime.now().isoformat(),
    },
    "latest": {
        "network_risk": 0,
        "user_risk": 0,
        "final_risk": 0,
        "action": "LOG",
        "reasoning": "Initializing...",
        "confidence": 0,
        "threat_level": "LOW",
        "tools_used": [],
    },
}


# ── HTML Template ──
HTML_TEMPLATE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hybrid Threat Detection — Command Center</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#0a0e1a;--surface:#111827;--card:#1a2236;--border:#1e293b;
  --text:#e2e8f0;--muted:#64748b;--accent:#3b82f6;
  --green:#10b981;--yellow:#f59e0b;--orange:#f97316;--red:#ef4444;--purple:#a855f7;
  --cyan:#06b6d4;
}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;overflow-x:hidden}

/* Animated background */
body::before{content:'';position:fixed;top:0;left:0;width:100%;height:100%;
  background:radial-gradient(ellipse at 20% 50%,rgba(59,130,246,0.08) 0%,transparent 50%),
             radial-gradient(ellipse at 80% 20%,rgba(168,85,247,0.06) 0%,transparent 50%),
             radial-gradient(ellipse at 50% 80%,rgba(6,182,212,0.05) 0%,transparent 50%);
  pointer-events:none;z-index:0}

.container{max-width:1440px;margin:0 auto;padding:20px 24px;position:relative;z-index:1}

/* Header */
.header{display:flex;align-items:center;justify-content:space-between;margin-bottom:28px;padding-bottom:20px;border-bottom:1px solid var(--border)}
.header-left{display:flex;align-items:center;gap:16px}
.logo{width:48px;height:48px;background:linear-gradient(135deg,var(--accent),var(--purple));border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:24px;box-shadow:0 0 30px rgba(59,130,246,0.3)}
.header h1{font-size:22px;font-weight:700;background:linear-gradient(135deg,#fff,var(--cyan));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.header p{font-size:13px;color:var(--muted);margin-top:2px}
.status-badge{display:flex;align-items:center;gap:8px;padding:8px 18px;border-radius:20px;font-size:13px;font-weight:600;border:1px solid var(--border);background:rgba(16,185,129,0.1)}
.status-dot{width:9px;height:9px;border-radius:50%;background:var(--green);box-shadow:0 0 10px var(--green);animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}

/* Cards Grid */
.stats-row{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:24px}
.stat-card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:20px 22px;position:relative;overflow:hidden;transition:transform 0.2s,box-shadow 0.2s}
.stat-card:hover{transform:translateY(-2px);box-shadow:0 8px 30px rgba(0,0,0,0.3)}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;border-radius:16px 16px 0 0}
.stat-card:nth-child(1)::before{background:linear-gradient(90deg,var(--green),var(--cyan))}
.stat-card:nth-child(2)::before{background:linear-gradient(90deg,var(--red),var(--orange))}
.stat-card:nth-child(3)::before{background:linear-gradient(90deg,var(--accent),var(--purple))}
.stat-card:nth-child(4)::before{background:linear-gradient(90deg,var(--yellow),var(--orange))}
.stat-label{font-size:12px;color:var(--muted);text-transform:uppercase;letter-spacing:1.2px;font-weight:600}
.stat-value{font-size:32px;font-weight:800;margin:6px 0 4px;font-family:'JetBrains Mono',monospace}
.stat-sub{font-size:12px;color:var(--muted)}

/* Main grid */
.main-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px}
.panel{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:24px;overflow:hidden}
.panel-title{font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:1px;margin-bottom:18px;display:flex;align-items:center;gap:10px;color:var(--muted)}
.panel-title span{font-size:16px}

/* Threat Gauge */
.gauge-container{display:flex;flex-direction:column;align-items:center;gap:10px}
.gauge-ring{position:relative;width:200px;height:200px}
.gauge-ring svg{transform:rotate(-90deg)}
.gauge-ring circle{fill:none;stroke-width:12;stroke-linecap:round}
.gauge-bg{stroke:var(--border)}
.gauge-fill{transition:stroke-dashoffset 1s ease,stroke 0.5s}
.gauge-center{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center}
.gauge-score{font-size:42px;font-weight:900;font-family:'JetBrains Mono',monospace}
.gauge-label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:2px;margin-top:2px}
.gauge-action{margin-top:8px;padding:6px 20px;border-radius:8px;font-size:14px;font-weight:700;font-family:'JetBrains Mono',monospace;letter-spacing:1px}

/* Risk bars */
.risk-bars{display:flex;flex-direction:column;gap:16px;margin-top:10px}
.risk-item label{display:flex;justify-content:space-between;font-size:13px;font-weight:500;margin-bottom:6px}
.risk-item label span{font-family:'JetBrains Mono',monospace;font-weight:700}
.bar-track{height:10px;background:var(--border);border-radius:6px;overflow:hidden}
.bar-fill{height:100%;border-radius:6px;transition:width 0.8s ease;position:relative}
.bar-fill::after{content:'';position:absolute;top:0;left:0;right:0;bottom:0;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.15));border-radius:6px}

/* AI Reasoning */
.ai-box{background:rgba(59,130,246,0.06);border:1px solid rgba(59,130,246,0.15);border-radius:12px;padding:18px;margin-top:12px;font-size:13px;line-height:1.7;color:#94a3b8;font-family:'Inter',sans-serif;max-height:200px;overflow-y:auto;position:relative}
.ai-box::before{content:'AI';position:absolute;top:10px;right:12px;font-size:10px;font-weight:800;color:var(--accent);background:rgba(59,130,246,0.15);padding:2px 8px;border-radius:4px;letter-spacing:1px}
.tools-row{display:flex;gap:6px;margin-top:10px;flex-wrap:wrap}
.tool-chip{padding:3px 10px;border-radius:6px;font-size:11px;font-weight:600;background:rgba(168,85,247,0.12);color:var(--purple);border:1px solid rgba(168,85,247,0.2);font-family:'JetBrains Mono',monospace}

/* Timeline chart (canvas) */
canvas{width:100%!important;border-radius:8px}

/* Event Log */
.event-log{max-height:360px;overflow-y:auto;scrollbar-width:thin;scrollbar-color:var(--border) transparent}
.event-item{display:flex;align-items:flex-start;gap:12px;padding:12px 14px;border-radius:10px;margin-bottom:8px;border:1px solid var(--border);background:rgba(255,255,255,0.01);transition:background 0.2s}
.event-item:hover{background:rgba(255,255,255,0.03)}
.event-time{font-size:11px;color:var(--muted);font-family:'JetBrains Mono',monospace;white-space:nowrap;min-width:65px;padding-top:2px}
.event-badge{padding:2px 10px;border-radius:6px;font-size:11px;font-weight:700;font-family:'JetBrains Mono',monospace;white-space:nowrap}
.badge-LOG{background:rgba(16,185,129,0.12);color:var(--green);border:1px solid rgba(16,185,129,0.2)}
.badge-ALERT{background:rgba(245,158,11,0.12);color:var(--yellow);border:1px solid rgba(245,158,11,0.2)}
.badge-RATE_LIMIT{background:rgba(249,115,22,0.12);color:var(--orange);border:1px solid rgba(249,115,22,0.2)}
.badge-BLOCK{background:rgba(239,68,68,0.12);color:var(--red);border:1px solid rgba(239,68,68,0.2)}
.event-msg{font-size:12px;color:#94a3b8;line-height:1.5;flex:1}

/* Full-width panels */
.full-panel{grid-column:1/-1}

/* Footer */
.footer{text-align:center;padding:20px 0;color:var(--muted);font-size:12px;border-top:1px solid var(--border);margin-top:10px}

/* Responsive */
@media(max-width:1024px){.stats-row{grid-template-columns:repeat(2,1fr)}.main-grid{grid-template-columns:1fr}}
@media(max-width:640px){.stats-row{grid-template-columns:1fr}.header{flex-direction:column;gap:12px}}

/* Confidence bar */
.confidence-row{display:flex;align-items:center;gap:10px;margin-top:12px}
.confidence-label{font-size:12px;color:var(--muted);min-width:80px}
.confidence-track{flex:1;height:6px;background:var(--border);border-radius:4px;overflow:hidden}
.confidence-fill{height:100%;border-radius:4px;background:linear-gradient(90deg,var(--accent),var(--cyan));transition:width 0.8s}
.confidence-val{font-size:13px;font-weight:700;font-family:'JetBrains Mono',monospace;min-width:40px;text-align:right}
</style>
</head>
<body>

<div class="container">
  <!-- Header -->
  <div class="header">
    <div class="header-left">
      <div class="logo">🛡️</div>
      <div>
        <h1>Hybrid Threat Detection — Command Center</h1>
        <p>IDS + UEBA · 60/40 Fusion · Agentic AI (ReAct)</p>
      </div>
    </div>
    <div class="status-badge"><div class="status-dot"></div><span id="sys-status">ONLINE</span></div>
  </div>

  <!-- Stats Row -->
  <div class="stats-row">
    <div class="stat-card">
      <div class="stat-label">Detection Cycles</div>
      <div class="stat-value" id="s-cycles">0</div>
      <div class="stat-sub">Total scans completed</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Current Threat</div>
      <div class="stat-value" id="s-threat" style="color:var(--green)">LOW</div>
      <div class="stat-sub" id="s-risk-sub">Risk: 0.00</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">AI Model</div>
      <div class="stat-value" id="s-model" style="font-size:18px">—</div>
      <div class="stat-sub" id="s-ai-status">Checking...</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Actions Taken</div>
      <div class="stat-value" id="s-actions">0</div>
      <div class="stat-sub" id="s-action-breakdown">—</div>
    </div>
  </div>

  <!-- Main Grid -->
  <div class="main-grid">
    <!-- Left: Threat Gauge + Risk Bars -->
    <div class="panel">
      <div class="panel-title"><span>📊</span> Threat Assessment</div>
      <div class="gauge-container">
        <div class="gauge-ring">
          <svg viewBox="0 0 200 200">
            <circle class="gauge-bg" cx="100" cy="100" r="85"/>
            <circle class="gauge-fill" id="gauge-arc" cx="100" cy="100" r="85"
                    stroke-dasharray="534" stroke-dashoffset="534" stroke="var(--green)"/>
          </svg>
          <div class="gauge-center">
            <div class="gauge-score" id="gauge-score">0.00</div>
            <div class="gauge-label">Combined Risk</div>
          </div>
        </div>
        <div class="gauge-action badge-LOG" id="gauge-action">LOG</div>
      </div>
      <div class="risk-bars">
        <div class="risk-item">
          <label>Network Risk (IDS) <span id="net-risk-val">0.00</span></label>
          <div class="bar-track"><div class="bar-fill" id="net-bar" style="width:0%;background:linear-gradient(90deg,var(--cyan),var(--accent))"></div></div>
        </div>
        <div class="risk-item">
          <label>User Risk (UEBA) <span id="user-risk-val">0.00</span></label>
          <div class="bar-track"><div class="bar-fill" id="user-bar" style="width:0%;background:linear-gradient(90deg,var(--yellow),var(--orange))"></div></div>
        </div>
      </div>
    </div>

    <!-- Right: AI Reasoning -->
    <div class="panel">
      <div class="panel-title"><span>🤖</span> Agentic AI Reasoning</div>
      <div class="ai-box" id="ai-reasoning">Waiting for first detection cycle...</div>
      <div class="tools-row" id="tools-row"></div>
      <div class="confidence-row">
        <div class="confidence-label">Confidence</div>
        <div class="confidence-track"><div class="confidence-fill" id="conf-bar" style="width:0%"></div></div>
        <div class="confidence-val" id="conf-val">0%</div>
      </div>
    </div>

    <!-- Risk Timeline Chart -->
    <div class="panel">
      <div class="panel-title"><span>📈</span> Risk Timeline</div>
      <canvas id="timeline" height="220"></canvas>
    </div>

    <!-- Event Log -->
    <div class="panel">
      <div class="panel-title"><span>📋</span> Event Log</div>
      <div class="event-log" id="event-log">
        <div style="text-align:center;color:var(--muted);padding:40px 0">Waiting for events...</div>
      </div>
    </div>
  </div>

  <div class="footer">
    Cloud-Native Hybrid Threat Detection System · Aarit Haldar, Priyanshu Sithole, Jay Bhagat · DSCE 2026
  </div>
</div>

<script>
// ── Timeline chart (pure Canvas) ──
const canvas = document.getElementById('timeline');
const ctx = canvas.getContext('2d');
let historyNet = [], historyUser = [], historyFinal = [];
const MAX_HIST = 40;

function drawChart() {
  const W = canvas.width = canvas.offsetWidth * 2;
  const H = canvas.height = 440;
  ctx.clearRect(0, 0, W, H);
  ctx.scale(1, 1);
  const pad = {l:50,r:20,t:20,b:40};
  const cw = W - pad.l - pad.r, ch = H - pad.t - pad.b;

  // Grid
  ctx.strokeStyle = '#1e293b'; ctx.lineWidth = 1;
  for (let i = 0; i <= 4; i++) {
    const y = pad.t + ch * i / 4;
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(pad.l + cw, y); ctx.stroke();
    ctx.fillStyle = '#475569'; ctx.font = '20px JetBrains Mono';
    ctx.textAlign = 'right';
    ctx.fillText((1 - i/4).toFixed(1), pad.l - 8, y + 6);
  }

  // Threshold lines
  const thresholds = [{v:0.8,c:'#ef4444',l:'BLOCK'},{v:0.6,c:'#f97316',l:'RATE_LIMIT'},{v:0.4,c:'#f59e0b',l:'ALERT'}];
  thresholds.forEach(t => {
    const y = pad.t + ch * (1 - t.v);
    ctx.strokeStyle = t.c + '40'; ctx.lineWidth = 1; ctx.setLineDash([6,4]);
    ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(pad.l+cw, y); ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = t.c + '80'; ctx.font = '18px Inter'; ctx.textAlign = 'left';
    ctx.fillText(t.l, pad.l + cw - 80, y - 6);
  });

  function line(data, color, width) {
    if (data.length < 2) return;
    const step = cw / (MAX_HIST - 1);
    ctx.strokeStyle = color; ctx.lineWidth = width; ctx.lineJoin = 'round';
    ctx.beginPath();
    data.forEach((v, i) => {
      const x = pad.l + i * step, y = pad.t + ch * (1 - v);
      i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
    });
    ctx.stroke();
    // Glow
    ctx.strokeStyle = color + '30'; ctx.lineWidth = width + 4; ctx.stroke();
  }

  line(historyNet, '#06b6d4', 2);
  line(historyUser, '#f59e0b', 2);
  line(historyFinal, '#a855f7', 3);

  // Legend
  const legends = [{c:'#06b6d4',l:'Network'},{c:'#f59e0b',l:'User'},{c:'#a855f7',l:'Combined'}];
  let lx = pad.l + 10;
  legends.forEach(lg => {
    ctx.fillStyle = lg.c; ctx.fillRect(lx, H - 22, 14, 4); lx += 18;
    ctx.fillStyle = '#94a3b8'; ctx.font = '18px Inter'; ctx.textAlign = 'left';
    ctx.fillText(lg.l, lx, H - 15); lx += ctx.measureText(lg.l).width + 20;
  });
}

// ── Color helpers ──
function threatColor(level) {
  return {LOW:'var(--green)',MEDIUM:'var(--yellow)',HIGH:'var(--orange)',CRITICAL:'var(--red)'}[level] || 'var(--muted)';
}
function riskGaugeColor(r) {
  if (r >= 0.8) return '#ef4444';
  if (r >= 0.6) return '#f97316';
  if (r >= 0.4) return '#f59e0b';
  return '#10b981';
}

// ── Poll data ──
async function poll() {
  try {
    const res = await fetch('/api/state');
    const d = await res.json();

    // Stats
    document.getElementById('s-cycles').textContent = d.stats.total_cycles;
    const tl = d.latest.threat_level;
    const tlEl = document.getElementById('s-threat');
    tlEl.textContent = tl; tlEl.style.color = threatColor(tl);
    document.getElementById('s-risk-sub').textContent = 'Risk: ' + d.latest.final_risk.toFixed(2);
    document.getElementById('s-model').textContent = d.stats.model === 'none' ? '—' : d.stats.model;
    document.getElementById('s-ai-status').textContent = d.stats.ai_available ? 'Connected' : 'Fallback (rules)';
    document.getElementById('s-ai-status').style.color = d.stats.ai_available ? 'var(--green)' : 'var(--yellow)';

    const total = d.stats.log_count + d.stats.alert_count + d.stats.rate_limit_count + d.stats.block_count;
    document.getElementById('s-actions').textContent = total;
    document.getElementById('s-action-breakdown').textContent =
      `L:${d.stats.log_count} A:${d.stats.alert_count} R:${d.stats.rate_limit_count} B:${d.stats.block_count}`;

    // Gauge
    const r = d.latest.final_risk;
    const circ = 534;
    const offset = circ - (circ * r);
    const arc = document.getElementById('gauge-arc');
    arc.style.strokeDashoffset = offset;
    arc.style.stroke = riskGaugeColor(r);
    document.getElementById('gauge-score').textContent = r.toFixed(2);
    document.getElementById('gauge-score').style.color = riskGaugeColor(r);

    const actionEl = document.getElementById('gauge-action');
    actionEl.textContent = d.latest.action;
    actionEl.className = 'gauge-action badge-' + d.latest.action;

    // Risk bars
    document.getElementById('net-risk-val').textContent = d.latest.network_risk.toFixed(2);
    document.getElementById('net-bar').style.width = (d.latest.network_risk * 100) + '%';
    document.getElementById('user-risk-val').textContent = d.latest.user_risk.toFixed(2);
    document.getElementById('user-bar').style.width = (d.latest.user_risk * 100) + '%';

    // AI
    document.getElementById('ai-reasoning').textContent = d.latest.reasoning || 'No reasoning available.';
    const toolsRow = document.getElementById('tools-row');
    toolsRow.innerHTML = '';
    (d.latest.tools_used || []).forEach(t => {
      const chip = document.createElement('div');
      chip.className = 'tool-chip'; chip.textContent = t;
      toolsRow.appendChild(chip);
    });
    const conf = d.latest.confidence || 0;
    document.getElementById('conf-bar').style.width = (conf * 100) + '%';
    document.getElementById('conf-val').textContent = (conf * 100).toFixed(0) + '%';

    // Timeline
    historyNet = Array.from(d.network_risk || []);
    historyUser = Array.from(d.user_risk || []);
    historyFinal = Array.from(d.final_risk || []);
    drawChart();

    // Events
    const logEl = document.getElementById('event-log');
    if (d.events && d.events.length) {
      logEl.innerHTML = '';
      d.events.slice().reverse().forEach(ev => {
        const div = document.createElement('div');
        div.className = 'event-item';
        div.innerHTML = `
          <div class="event-time">${ev.time}</div>
          <div class="event-badge badge-${ev.action}">${ev.action}</div>
          <div class="event-msg">${ev.msg}</div>`;
        logEl.appendChild(div);
      });
    }
  } catch(e) {
    console.error('Poll error:', e);
  }
}

setInterval(poll, 2000);
poll();
window.addEventListener('resize', drawChart);
</script>
</body>
</html>
"""


# ── Dashboard is now a Thin Client ──
# Detection loop is handled natively by enhanced_main_with_agent.py
# which writes state to web_state.json periodically.


# ── Flask routes ──
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route("/api/state")
def api_state():
    try:
        if os.path.exists("web_state.json"):
            with open("web_state.json", "r") as f:
                return jsonify(json.load(f))
    except Exception as e:
        print(f"Error reading state: {e}")
        
    return jsonify({
        "timestamps": list(state["timestamps"]),
        "network_risk": list(state["network_risk"]),
        "user_risk": list(state["user_risk"]),
        "final_risk": list(state["final_risk"]),
        "actions": list(state["actions"]),
        "events": list(state["events"]),
        "stats": state["stats"],
        "latest": state["latest"],
    })


if __name__ == "__main__":
    print("=" * 60)
    print("  Hybrid Threat Detection — Command Center")
    print("=" * 60)
    print("  Dashboard running in Thin Client Mode...")
    print("  Make sure to run enhanced_main_with_agent.py to populate state!")

    print("  Dashboard: http://localhost:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False)
