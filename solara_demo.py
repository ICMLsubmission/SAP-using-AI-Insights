#!/usr/bin/env python3
"""
SOLARA Demo: AI-Derived Trial Design Intelligence
Demonstrates: SAP Parsing → Cross-Trial Intelligence → SOLARA Input

Usage:
    python3 solara_demo.py
    Then open http://localhost:8000
"""

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from threading import Thread
import sys

# Mock historical trial data (simulating parsed SAPs)
MOCK_TRIALS = [
    {
        "trial_id": "KEYNOTE-024",
        "indication": "NSCLC",
        "phase": "III",
        "primary_endpoint": "PFS",
        "endpoint_type": "Binary (ORR)",
        "assumed_response_rate": 0.45,
        "control_response_rate": 0.28,
        "effect_size_or": 1.8,
        "power": 0.90,
        "alpha": 0.05,
        "sample_size": 305,
        "primary_analysis": "Logistic regression",
        "study_population": "PD-L1 ≥50%",
        "treatment": "Pembrolizumab monotherapy"
    },
    {
        "trial_id": "KEYNOTE-407",
        "indication": "NSCLC",
        "phase": "II",
        "primary_endpoint": "ORR",
        "endpoint_type": "Binary (ORR)",
        "assumed_response_rate": 0.38,
        "control_response_rate": 0.15,
        "effect_size_or": 1.5,
        "power": 0.85,
        "alpha": 0.05,
        "sample_size": 278,
        "primary_analysis": "Logistic regression",
        "study_population": "Squamous NSCLC",
        "treatment": "Pembrolizumab + chemotherapy"
    },
    {
        "trial_id": "ATTRACT-2",
        "indication": "NSCLC",
        "phase": "II",
        "primary_endpoint": "ORR",
        "endpoint_type": "Binary (ORR)",
        "assumed_response_rate": 0.42,
        "control_response_rate": 0.20,
        "effect_size_or": 1.6,
        "power": 0.88,
        "alpha": 0.05,
        "sample_size": 256,
        "primary_analysis": "Logistic regression",
        "study_population": "PD-L1 ≥1%",
        "treatment": "Atezolizumab monotherapy"
    },
    {
        "trial_id": "CheckMate-057",
        "indication": "NSCLC",
        "phase": "III",
        "primary_endpoint": "OS",
        "endpoint_type": "Binary (ORR)",
        "assumed_response_rate": 0.20,
        "control_response_rate": 0.09,
        "effect_size_or": 1.3,
        "power": 0.90,
        "alpha": 0.05,
        "sample_size": 582,
        "primary_analysis": "Cox proportional hazards",
        "study_population": "Nonsquamous NSCLC",
        "treatment": "Nivolumab monotherapy"
    },
    {
        "trial_id": "JIPANG-2",
        "indication": "NSCLC",
        "phase": "II",
        "primary_endpoint": "ORR",
        "endpoint_type": "Binary (ORR)",
        "assumed_response_rate": 0.35,
        "control_response_rate": 0.18,
        "effect_size_or": 1.4,
        "power": 0.82,
        "alpha": 0.05,
        "sample_size": 198,
        "primary_analysis": "Logistic regression",
        "study_population": "EGFR-mutant NSCLC",
        "treatment": "Nivolumab + chemotherapy"
    },
    {
        "trial_id": "MYSTIC",
        "indication": "NSCLC",
        "phase": "III",
        "primary_endpoint": "PFS",
        "endpoint_type": "Binary (ORR)",
        "assumed_response_rate": 0.44,
        "control_response_rate": 0.26,
        "effect_size_or": 1.7,
        "power": 0.90,
        "alpha": 0.05,
        "sample_size": 566,
        "primary_analysis": "Logistic regression (baseline + region)",
        "study_population": "PD-L1 ≥25%",
        "treatment": "Durvalumab monotherapy"
    }
]

# Mock unstructured SAP excerpt (as if parsed from raw document)
SAMPLE_SAP = """
TRIAL: KEYNOTE-024
PHASE: III, Randomized, Open-Label
INDICATION: NSCLC, first-line treatment
PRIMARY ENDPOINT: Progression-free survival (PFS)
STUDY POPULATION: Patients with PD-L1 expression ≥50% (by IHC 22C3)
TREATMENT: Pembrolizumab 200mg IV Q3W vs chemotherapy (pemetrexed + cisplatin)
SAMPLE SIZE CALCULATION: 
  - Assumed median PFS: 12 months (experimental), 6 months (control)
  - HR = 0.60
  - Power 90%, alpha 0.05 (two-sided)
  - Sample size: 305 patients (randomized 1:1)
PRIMARY ANALYSIS: 
  - Population: Intent-to-treat
  - Method: Cox proportional hazards regression with baseline covariates and region
RESPONSE RATE (secondary): ~45% vs 28% (assumed)
"""

# Import anthropic (will work if available)
try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("⚠ Note: Anthropic SDK not available. Will use mock LLM responses.")

# Initialize client if available
if HAS_ANTHROPIC:
    client = Anthropic()
else:
    client = None


def parse_sap_with_llm(sap_text: str) -> dict:
    """
    Use Claude to parse unstructured SAP into structured design record.
    Falls back to mock data if Anthropic not available.
    """
    if not HAS_ANTHROPIC or client is None:
        # Mock LLM response
        return {
            "trial_id": "KEYNOTE-024",
            "indication": "NSCLC",
            "phase": "III",
            "primary_endpoint": "PFS",
            "endpoint_type": "Binary (ORR)",
            "assumed_response_rate": 0.45,
            "control_response_rate": 0.28,
            "effect_size_or": 1.8,
            "power": 0.90,
            "alpha": 0.05,
            "sample_size": 305,
            "primary_analysis": "Logistic regression",
            "study_population": "PD-L1 ≥50%",
            "treatment": "Pembrolizumab monotherapy",
            "parsing_source": "MOCK - Set ANTHROPIC_API_KEY to use real LLM"
        }
    
    try:
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": f"""Parse this SAP excerpt and extract key design parameters. 
Return ONLY valid JSON with these fields (use null for missing):
- trial_id, indication, phase, primary_endpoint, endpoint_type
- assumed_response_rate, control_response_rate, effect_size_or
- power, alpha, sample_size, primary_analysis, study_population, treatment

SAP TEXT:
{sap_text}

Return only JSON, no markdown or explanation."""
                }
            ]
        )
        result = response.content[0].text
        # Clean up markdown if present
        if "```" in result:
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
            result = result.strip()
        return json.loads(result)
    except Exception as e:
        print(f"LLM parsing error: {e}. Using mock data.")
        return MOCK_TRIALS[0]


def analyze_assumption_landscape(trials: list) -> dict:
    """
    Aggregate trial data to surface typical ranges, means, and outliers.
    """
    if not trials:
        return {}
    
    # Extract key metrics
    response_rates = [t.get("assumed_response_rate", 0) for t in trials if t.get("assumed_response_rate")]
    effect_sizes = [t.get("effect_size_or", 0) for t in trials if t.get("effect_size_or")]
    powers = [t.get("power", 0) for t in trials if t.get("power")]
    sample_sizes = [t.get("sample_size", 0) for t in trials if t.get("sample_size")]
    
    def stats(vals):
        if not vals:
            return {}
        return {
            "min": min(vals),
            "max": max(vals),
            "mean": sum(vals) / len(vals),
            "median": sorted(vals)[len(vals)//2]
        }
    
    return {
        "total_trials": len(trials),
        "response_rate": stats(response_rates),
        "effect_size_or": stats(effect_sizes),
        "power": stats(powers),
        "sample_size": stats(sample_sizes),
        "common_treatments": list(set([t.get("treatment", "Unknown") for t in trials]))[:5],
        "common_populations": list(set([t.get("study_population", "Unknown") for t in trials]))[:5]
    }


def generate_solara_input(new_design: dict, assumption_landscape: dict) -> dict:
    """
    Generate SOLARA input with rationale explaining how historical data informs the design.
    """
    
    # Compare new design to landscape
    new_response_rate = new_design.get("assumed_response_rate", 0)
    landscape_rr = assumption_landscape.get("response_rate", {})
    
    new_or = new_design.get("effect_size_or", 0)
    landscape_or = assumption_landscape.get("effect_size_or", {})
    
    new_power = new_design.get("power", 0)
    landscape_power = assumption_landscape.get("power", {})
    
    rationale = []
    
    # Response rate rationale
    if landscape_rr.get("min"):
        if new_response_rate < landscape_rr["min"]:
            rationale.append(
                f"⚠ Response rate {new_response_rate:.0%} is BELOW historical range "
                f"({landscape_rr['min']:.0%}–{landscape_rr['max']:.0%}). "
                f"Consider if population is more refractory or if this is conservative."
            )
        elif new_response_rate > landscape_rr["max"]:
            rationale.append(
                f"✓ Response rate {new_response_rate:.0%} is ABOVE historical range "
                f"({landscape_rr['min']:.0%}–{landscape_rr['max']:.0%}). "
                f"Optimistic; ensure justification in regulatory submission."
            )
        else:
            rationale.append(
                f"✓ Response rate {new_response_rate:.0%} falls within historical range "
                f"({landscape_rr['min']:.0%}–{landscape_rr['max']:.0%}, mean {landscape_rr['mean']:.0%}). "
                f"Grounded in precedent."
            )
    
    # Effect size rationale
    if landscape_or.get("min"):
        if new_or < landscape_or["min"]:
            rationale.append(
                f"⚠ Effect size (OR) {new_or:.2f} is BELOW historical range "
                f"({landscape_or['min']:.2f}–{landscape_or['max']:.2f}). "
                f"May require larger sample size."
            )
        elif new_or > landscape_or["max"]:
            rationale.append(
                f"✓ Effect size (OR) {new_or:.2f} EXCEEDS historical range "
                f"({landscape_or['min']:.2f}–{landscape_or['max']:.2f}). "
                f"Conservative; trial likely powered adequately."
            )
        else:
            rationale.append(
                f"✓ Effect size (OR) {new_or:.2f} within historical range "
                f"({landscape_or['min']:.2f}–{landscape_or['max']:.2f}). "
                f"Well-supported by precedent."
            )
    
    # Power rationale
    if landscape_power.get("min"):
        typical_power = landscape_power.get("mean", 0.90)
        if new_power < typical_power - 0.03:
            rationale.append(
                f"⚠ Power {new_power:.0%} is below typical {typical_power:.0%}. "
                f"Higher risk of Type II error."
            )
        else:
            rationale.append(
                f"✓ Power {new_power:.0%} at or above typical precedent {typical_power:.0%}."
            )
    
    return {
        "design_parameters": new_design,
        "assumption_landscape_summary": {
            "n_historical_trials": assumption_landscape.get("total_trials"),
            "response_rate_range": f"{landscape_rr.get('min', 0):.0%}–{landscape_rr.get('max', 0):.0%}",
            "effect_size_range": f"{landscape_or.get('min', 0):.2f}–{landscape_or.get('max', 0):.2f}",
            "typical_power": f"{landscape_power.get('mean', 0):.0%}"
        },
        "rationale_for_solara": rationale,
        "key_insights": [
            f"Based on {assumption_landscape.get('total_trials')} historical NSCLC trials",
            f"Common treatment patterns: {', '.join(assumption_landscape.get('common_treatments', [])[:3])}",
            f"Key populations: {', '.join(assumption_landscape.get('common_populations', [])[:3])}"
        ]
    }


# ==================== WEB SERVER ====================

class TrialDesignHandler(SimpleHTTPRequestHandler):
    """HTTP handler for the demo UI and API."""
    
    def do_GET(self):
        """Serve the HTML UI."""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        elif self.path == '/api/trials':
            self.send_json({"trials": MOCK_TRIALS})
        elif self.path == '/api/sap-sample':
            self.send_json({"sap": SAMPLE_SAP})
        elif self.path.startswith('/api/landscape'):
            landscape = analyze_assumption_landscape(MOCK_TRIALS)
            self.send_json(landscape)
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle API requests (parse SAP, generate SOLARA input)."""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        if self.path == '/api/parse-sap':
            data = json.loads(body)
            sap_text = data.get('sap', SAMPLE_SAP)
            parsed = parse_sap_with_llm(sap_text)
            self.send_json(parsed)
        
        elif self.path == '/api/generate-solara':
            data = json.loads(body)
            new_design = data.get('design')
            landscape = analyze_assumption_landscape(MOCK_TRIALS)
            solara_input = generate_solara_input(new_design, landscape)
            self.send_json(solara_input)
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def send_json(self, obj):
        """Send JSON response."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(obj, indent=2).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress request logging."""
        pass


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SOLARA Demo: Trial Design Intelligence</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.1em; opacity: 0.9; }
        .content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            padding: 40px;
        }
        .panel {
            background: #f8fafc;
            border: 2px solid #e2e8f0;
            border-radius: 8px;
            padding: 25px;
        }
        .panel h2 {
            color: #1e293b;
            font-size: 1.4em;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .panel h3 {
            color: #475569;
            font-size: 1.05em;
            margin-top: 20px;
            margin-bottom: 12px;
            border-bottom: 2px solid #cbd5e1;
            padding-bottom: 8px;
        }
        .metric {
            background: white;
            padding: 15px;
            border-radius: 6px;
            margin: 10px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 4px solid #667eea;
        }
        .metric-label { color: #475569; font-weight: 500; }
        .metric-value { 
            color: #1e293b;
            font-weight: bold;
            font-size: 1.2em;
        }
        .rationale-list {
            list-style: none;
            margin: 15px 0;
        }
        .rationale-list li {
            background: white;
            padding: 12px;
            margin: 10px 0;
            border-radius: 6px;
            border-left: 4px solid #10b981;
            font-size: 0.95em;
            line-height: 1.5;
        }
        .rationale-list li.warning {
            border-left-color: #f59e0b;
        }
        .button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            font-size: 1em;
            font-weight: 600;
            cursor: pointer;
            margin: 10px 5px 10px 0;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(102, 126, 234, 0.4);
        }
        .input-group {
            margin: 15px 0;
        }
        .input-group label {
            display: block;
            color: #475569;
            font-weight: 500;
            margin-bottom: 6px;
            font-size: 0.95em;
        }
        .input-group input, .input-group textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            font-family: inherit;
            font-size: 0.95em;
        }
        .input-group textarea {
            min-height: 100px;
            resize: vertical;
        }
        .input-group input:focus, .input-group textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        .output-section {
            background: white;
            padding: 20px;
            border-radius: 6px;
            margin-top: 20px;
            max-height: 500px;
            overflow-y: auto;
            border: 2px solid #e2e8f0;
        }
        .output-section pre {
            background: #1e293b;
            color: #10b981;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 0.85em;
            line-height: 1.4;
        }
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
            margin: 15px 0;
        }
        .stat-card {
            background: white;
            padding: 15px;
            border-radius: 6px;
            border: 1px solid #cbd5e1;
        }
        .stat-card-title {
            color: #64748b;
            font-size: 0.85em;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .stat-card-value {
            color: #1e293b;
            font-size: 1.3em;
            font-weight: bold;
        }
        .loading {
            color: #667eea;
            font-style: italic;
        }
        .emoji { font-size: 1.2em; }
        @media (max-width: 1024px) {
            .content { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><span class="emoji">🔬</span> SOLARA Demo</h1>
            <p>AI-Derived Trial Design Intelligence from Historical Data</p>
        </div>
        
        <div class="content">
            <!-- LEFT: HISTORICAL DATA & SAP PARSING -->
            <div class="panel">
                <h2><span class="emoji">📊</span> Step 1: Historical Trial Landscape</h2>
                
                <h3>Aggregated Assumption Landscape</h3>
                <div id="landscapeMetrics" class="stat-grid">
                    <div class="stat-card">
                        <div class="stat-card-title">Response Rate Range</div>
                        <div class="stat-card-value" id="rrRange">—</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-card-title">Effect Size (OR) Range</div>
                        <div class="stat-card-value" id="orRange">—</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-card-title">Typical Power</div>
                        <div class="stat-card-value" id="powerRange">—</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-card-title">Historical Trials</div>
                        <div class="stat-card-value" id="trialCount">—</div>
                    </div>
                </div>

                <h3>Sample SAP (Unstructured)</h3>
                <textarea id="sapInput" placeholder="Paste SAP excerpt here..."></textarea>
                <button class="button" onclick="parseSAP()"><span class="emoji">🧠</span> Parse SAP with LLM</button>
                
                <div class="output-section" id="parsedOutput" style="display: none;">
                    <h3 style="margin-top: 0;">Parsed Design Record</h3>
                    <pre id="parsedJson"></pre>
                </div>
            </div>
            
            <!-- RIGHT: NEW DESIGN & SOLARA OUTPUT -->
            <div class="panel">
                <h2><span class="emoji">✨</span> Step 2: New Trial Design & SOLARA Input</h2>
                
                <h3>Proposed Design Parameters</h3>
                <div class="input-group">
                    <label>Trial ID</label>
                    <input type="text" id="trialId" value="MY-TRIAL-2024" />
                </div>
                <div class="input-group">
                    <label>Assumed Response Rate (%)</label>
                    <input type="number" id="responseRate" value="42" min="0" max="100" />
                </div>
                <div class="input-group">
                    <label>Control Response Rate (%)</label>
                    <input type="number" id="controlRate" value="25" min="0" max="100" />
                </div>
                <div class="input-group">
                    <label>Effect Size (OR)</label>
                    <input type="number" id="effectSize" value="1.65" min="0.5" max="5" step="0.1" />
                </div>
                <div class="input-group">
                    <label>Power (%)</label>
                    <input type="number" id="power" value="90" min="50" max="99" />
                </div>
                <button class="button" onclick="generateSOLARA()"><span class="emoji">🚀</span> Generate SOLARA Input</button>
                
                <div class="output-section" id="solaraOutput" style="display: none;">
                    <h3 style="margin-top: 0;">SOLARA Input & Rationale</h3>
                    <div id="solaraContent"></div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Load initial landscape
        async function loadLandscape() {
            try {
                const res = await fetch('/api/landscape');
                const data = await res.json();
                document.getElementById('rrRange').textContent = 
                    `${(data.response_rate.min * 100).toFixed(0)}%–${(data.response_rate.max * 100).toFixed(0)}%`;
                document.getElementById('orRange').textContent = 
                    `${data.effect_size_or.min.toFixed(2)}–${data.effect_size_or.max.toFixed(2)}`;
                document.getElementById('powerRange').textContent = 
                    `${(data.power.mean * 100).toFixed(0)}%`;
                document.getElementById('trialCount').textContent = `${data.total_trials}`;
            } catch (e) {
                console.error('Failed to load landscape:', e);
            }
        }

        // Load sample SAP
        async function loadSample() {
            try {
                const res = await fetch('/api/sap-sample');
                const data = await res.json();
                document.getElementById('sapInput').value = data.sap;
            } catch (e) {
                console.error('Failed to load sample:', e);
            }
        }

        // Parse SAP
        async function parseSAP() {
            const sap = document.getElementById('sapInput').value;
            if (!sap.trim()) {
                alert('Please enter SAP text');
                return;
            }
            
            try {
                const res = await fetch('/api/parse-sap', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ sap })
                });
                const data = await res.json();
                document.getElementById('parsedJson').textContent = JSON.stringify(data, null, 2);
                document.getElementById('parsedOutput').style.display = 'block';
            } catch (e) {
                alert('Error parsing SAP: ' + e.message);
            }
        }

        // Generate SOLARA input
        async function generateSOLARA() {
            const design = {
                trial_id: document.getElementById('trialId').value,
                assumed_response_rate: parseFloat(document.getElementById('responseRate').value) / 100,
                control_response_rate: parseFloat(document.getElementById('controlRate').value) / 100,
                effect_size_or: parseFloat(document.getElementById('effectSize').value),
                power: parseFloat(document.getElementById('power').value) / 100
            };
            
            try {
                const res = await fetch('/api/generate-solara', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ design })
                });
                const data = await res.json();
                
                let html = '<h3 style="margin-top: 0;">Input Summary</h3>';
                html += '<div class="stat-grid">';
                html += `<div class="stat-card"><div class="stat-card-title">Response Rate</div><div class="stat-card-value">${(design.assumed_response_rate * 100).toFixed(0)}%</div></div>`;
                html += `<div class="stat-card"><div class="stat-card-title">Effect Size</div><div class="stat-card-value">${design.effect_size_or.toFixed(2)}</div></div>`;
                html += `<div class="stat-card"><div class="stat-card-title">Power</div><div class="stat-card-value">${(design.power * 100).toFixed(0)}%</div></div>`;
                html += `<div class="stat-card"><div class="stat-card-title">vs Historical Mean</div><div class="stat-card-value">✓</div></div>`;
                html += '</div>';
                
                html += '<h3>Rationale (Why these assumptions?)</h3>';
                html += '<ul class="rationale-list">';
                data.rationale_for_solara.forEach(r => {
                    const isWarning = r.includes('BELOW') || r.includes('⚠');
                    html += `<li${isWarning ? ' class="warning"' : ''}>${r}</li>`;
                });
                html += '</ul>';
                
                html += '<h3>Key Insights</h3>';
                html += '<ul class="rationale-list">';
                data.key_insights.forEach(k => {
                    html += `<li>${k}</li>`;
                });
                html += '</ul>';
                
                document.getElementById('solaraContent').innerHTML = html;
                document.getElementById('solaraOutput').style.display = 'block';
            } catch (e) {
                alert('Error generating SOLARA input: ' + e.message);
            }
        }

        // Initialize
        window.onload = () => {
            loadLandscape();
            loadSample();
        };
    </script>
</body>
</html>
"""


def main():
    """Start the demo server."""
    port = 8000
    server = HTTPServer(('localhost', port), TrialDesignHandler)
    print(f"""
╔═══════════════════════════════════════════════════════════════════╗
║               🚀 SOLARA DEMO - Trial Design Intelligence          ║
╚═══════════════════════════════════════════════════════════════════╝

✓ Historical Trials Loaded: {len(MOCK_TRIALS)} NSCLC studies
✓ LLM Parser: {'Claude API' if HAS_ANTHROPIC else 'Mock Mode'}
✓ Web Server: http://localhost:{port}

📖 How it works:
  1. LEFT PANEL: Load historical trials → Parse SAP with LLM
  2. RIGHT PANEL: Input new design → Get SOLARA input with rationale

🌐 Open http://localhost:{port} in your browser
⌨️  Press Ctrl+C to stop

""")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✓ Server stopped.")
        sys.exit(0)


if __name__ == "__main__":
    main()
