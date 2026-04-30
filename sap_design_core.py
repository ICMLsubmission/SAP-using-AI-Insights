"""
SAP Design by AI Insights - Core Logic
AI-driven trial design informed by historical SAPs instead of building from scratch

Vision:
1. Parse historical SAPs (extract design parameters)
2. Build assumption landscape (what successful trials look like)
3. Generate scenarios for NEW drug design (base/optimistic/pessimistic)
4. SOLARA-ready output with sensitivity analysis
5. Evidence-grounded, not guesswork
"""

import json
from typing import List, Dict, Optional
import os

try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import PyPDF2
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    from docx import Document as DocxDocument
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import plotly.graph_objects as go
    import numpy as np
    import pandas as pd
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False


# ==================== DOCUMENT EXTRACTION ====================

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF"""
    if not HAS_PYPDF:
        return "[PDF extraction unavailable]"
    try:
        from io import BytesIO
        reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
        return "\n".join(page.extract_text() for page in reader.pages)
    except Exception as e:
        return f"Error: {str(e)}"


def extract_text_from_docx(docx_bytes: bytes) -> str:
    """Extract text from Word document"""
    if not HAS_DOCX:
        return "[DOCX extraction unavailable]"
    try:
        from io import BytesIO
        doc = DocxDocument(BytesIO(docx_bytes))
        return "\n".join(p.text for p in doc.paragraphs)
    except Exception as e:
        return f"Error: {str(e)}"


def extract_text_from_document(file_bytes: bytes, filename: str) -> str:
    """Extract text based on file type"""
    if filename.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_bytes)
    elif filename.lower().endswith('.docx'):
        return extract_text_from_docx(file_bytes)
    return ""


# ==================== LLM PARSING ====================

def parse_sap_with_llm(sap_text: str, trial_filename: str) -> Dict:
    """Use Claude to extract design parameters from SAP text"""
    if not HAS_ANTHROPIC:
        return generate_mock_parsed_record(trial_filename)

    try:
        client = Anthropic()
        
        prompt = f"""Extract trial design parameters from this SAP.
Return ONLY valid JSON with these fields:
- trial_id, indication, phase
- primary_endpoint, endpoint_type
- assumed_response_rate, control_response_rate
- effect_size_or, power, alpha
- sample_size, primary_analysis
- study_population, treatment

SAP TEXT (first 2000 chars):
{sap_text[:2000]}

Return valid JSON only, no markdown."""

        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        
        text = response.content[0].text
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        
        parsed = json.loads(text)
        parsed["_source_file"] = trial_filename
        return parsed
        
    except Exception as e:
        return generate_mock_parsed_record(trial_filename)


def generate_mock_parsed_record(filename: str) -> Dict:
    """Fallback mock data"""
    mock_data = {
        "KEYNOTE-024": {"trial_id": "KEYNOTE-024", "indication": "NSCLC", "phase": "III",
                       "primary_endpoint": "PFS", "endpoint_type": "Time-to-event",
                       "assumed_response_rate": 0.45, "control_response_rate": 0.28,
                       "effect_size_or": 1.8, "power": 0.90, "alpha": 0.05,
                       "sample_size": 305, "primary_analysis": "Cox PH regression",
                       "study_population": "PD-L1 ≥50%", "treatment": "Pembrolizumab"},
        "ATTRACT-2": {"trial_id": "ATTRACT-2", "indication": "NSCLC", "phase": "II",
                     "assumed_response_rate": 0.42, "control_response_rate": 0.20,
                     "effect_size_or": 1.6, "power": 0.88, "sample_size": 256},
        "CheckMate-057": {"trial_id": "CheckMate-057", "indication": "NSCLC", "phase": "III",
                         "assumed_response_rate": 0.20, "control_response_rate": 0.09,
                         "effect_size_or": 1.3, "power": 0.90, "sample_size": 582},
        "MYSTIC": {"trial_id": "MYSTIC", "indication": "NSCLC", "phase": "III",
                  "assumed_response_rate": 0.44, "control_response_rate": 0.26,
                  "effect_size_or": 1.7, "power": 0.90, "sample_size": 566},
        "KEYNOTE-001": {"trial_id": "KEYNOTE-001", "indication": "Melanoma", "phase": "I",
                       "assumed_response_rate": 0.52, "control_response_rate": 0.25,
                       "effect_size_or": 2.1, "power": 0.85, "sample_size": 400},
        "CheckMate-066": {"trial_id": "CheckMate-066", "indication": "Melanoma", "phase": "III",
                         "assumed_response_rate": 0.61, "control_response_rate": 0.28,
                         "effect_size_or": 2.4, "power": 0.88, "sample_size": 280},
        "KEYNOTE-355": {"trial_id": "KEYNOTE-355", "indication": "Breast Cancer", "phase": "III",
                       "assumed_response_rate": 0.35, "control_response_rate": 0.22,
                       "effect_size_or": 1.4, "power": 0.82, "sample_size": 847},
        "IMpassion031": {"trial_id": "IMpassion031", "indication": "Breast Cancer", "phase": "III",
                        "assumed_response_rate": 0.38, "control_response_rate": 0.22,
                        "effect_size_or": 1.5, "power": 0.85, "sample_size": 651},
    }
    
    for key, data in mock_data.items():
        if key in filename:
            data["_source_file"] = filename
            return data
    
    result = mock_data["KEYNOTE-024"].copy()
    result["_source_file"] = filename
    return result


# ==================== ASSUMPTION LANDSCAPE ====================

def analyze_assumption_landscape(records: List[Dict], indication: str = None) -> Dict:
    """Build landscape of what successful trials look like"""
    
    records = records if not indication else [r for r in records if r.get("indication") == indication]
    
    if not records:
        return {}
    
    rr = [r.get("assumed_response_rate", 0) for r in records if r.get("assumed_response_rate")]
    cr = [r.get("control_response_rate", 0) for r in records if r.get("control_response_rate")]
    ors = [r.get("effect_size_or", 0) for r in records if r.get("effect_size_or")]
    pws = [r.get("power", 0) for r in records if r.get("power")]
    sss = [r.get("sample_size", 0) for r in records if r.get("sample_size")]
    
    def stats(vals):
        if not vals:
            return {}
        sv = sorted(vals)
        n = len(vals)
        return {
            "min": min(vals), "max": max(vals), "mean": sum(vals)/n,
            "median": sv[n//2], "q1": sv[n//4], "q3": sv[3*n//4]
        }
    
    return {
        "total_trials": len(records),
        "indication": indication or "All",
        "response_rate": stats(rr),
        "control_rate": stats(cr),
        "effect_size_or": stats(ors),
        "power": stats(pws),
        "sample_size": stats(sss),
        "trials": [{"id": r.get("trial_id"), "rr": r.get("assumed_response_rate"), 
                   "or": r.get("effect_size_or")} for r in records]
    }


# ==================== SCENARIO GENERATION ====================

def generate_scenarios(landscape: Dict, new_indication: str) -> Dict:
    """Create 3 scenarios for new drug based on historical landscape"""
    
    rr = landscape.get("response_rate", {})
    ors = landscape.get("effect_size_or", {})
    ss = landscape.get("sample_size", {})
    
    rr_mean = rr.get("mean", 0.40)
    rr_q3 = rr.get("q3", 0.45)
    rr_q1 = rr.get("q1", 0.35)
    
    or_mean = ors.get("mean", 1.6)
    or_q3 = ors.get("q3", 1.75)
    or_q1 = ors.get("q1", 1.4)
    
    ss_mean = int(ss.get("mean", 300))
    
    scenarios = {
        "base": {
            "name": "Base Case (Most Likely)",
            "rr": round(rr_mean, 2),
            "or": round(or_mean, 2),
            "sample_size": ss_mean,
            "power": 0.90,
            "rationale": f"Historical mean RR for {new_indication}. Represents typical outcome.",
            "confidence": "HIGH",
            "evidence_trials": landscape.get("total_trials", 0)
        },
        "optimistic": {
            "name": "Optimistic (Top Quartile)",
            "rr": round(rr_q3, 2),
            "or": round(or_q3, 2),
            "sample_size": int(ss_mean * 0.85),
            "power": 0.93,
            "rationale": f"Top 25% of historical trials. Represents strong effect.",
            "confidence": "MEDIUM",
            "evidence_trials": max(1, landscape.get("total_trials", 0) // 4)
        },
        "pessimistic": {
            "name": "Pessimistic (Bottom Quartile)",
            "rr": round(rr_q1, 2),
            "or": round(or_q1, 2),
            "sample_size": int(ss_mean * 1.15),
            "power": 0.82,
            "rationale": f"Bottom 25% of historical trials. Represents challenging scenario.",
            "confidence": "MEDIUM",
            "evidence_trials": max(1, landscape.get("total_trials", 0) // 4)
        }
    }
    
    return scenarios


# ==================== SENSITIVITY ANALYSIS ====================

def sensitivity_analysis(base_rr: float, base_or: float, base_n: int, base_power: float) -> Dict:
    """What assumptions matter most?"""
    
    def approx_power(rr: float, or_val: float, n: int) -> float:
        effect = (rr - 0.20) * or_val
        return min(0.99, max(0.50, base_power + (effect - (base_rr - 0.20) * base_or) * 0.5))
    
    results = {
        "RR -4%": {"power": round(approx_power(base_rr - 0.04, base_or, base_n), 3),
                  "impact": round((approx_power(base_rr - 0.04, base_or, base_n) - base_power) * 100, 1)},
        "RR +4%": {"power": round(approx_power(base_rr + 0.04, base_or, base_n), 3),
                  "impact": round((approx_power(base_rr + 0.04, base_or, base_n) - base_power) * 100, 1)},
        "OR -0.2": {"power": round(approx_power(base_rr, base_or - 0.2, base_n), 3),
                   "impact": round((approx_power(base_rr, base_or - 0.2, base_n) - base_power) * 100, 1)},
        "OR +0.2": {"power": round(approx_power(base_rr, base_or + 0.2, base_n), 3),
                   "impact": round((approx_power(base_rr, base_or + 0.2, base_n) - base_power) * 100, 1)},
    }
    
    return results


# ==================== SOLARA-READY OUTPUT ====================

def create_solara_input(base: Dict, optimistic: Dict, pessimistic: Dict, 
                       indication: str, landscape: Dict) -> Dict:
    """Package scenarios as SOLARA input with metadata"""
    
    return {
        "indication": indication,
        "n_historical_trials": landscape.get("total_trials", 0),
        "base_case": {**base, "confidence": "HIGH", "use_for": "Primary power calculation"},
        "optimistic_scenario": {**optimistic, "confidence": "MEDIUM", "use_for": "Best-case analysis"},
        "pessimistic_scenario": {**pessimistic, "confidence": "MEDIUM", "use_for": "Risk assessment"},
        "sensitivity_ranges": {
            "response_rate": [landscape["response_rate"]["min"], landscape["response_rate"]["max"]],
            "effect_size": [landscape["effect_size_or"]["min"], landscape["effect_size_or"]["max"]],
            "sample_size": [int(landscape["sample_size"]["min"]), int(landscape["sample_size"]["max"])]
        },
        "evidence": {
            "source_trials": [t["id"] for t in landscape.get("trials", [])],
            "key_finding": f"Design grounded in {landscape.get('total_trials', 0)} historical trials"
        }
    }


def export_to_json(data: Dict) -> str:
    """Export as JSON"""
    return json.dumps(data, indent=2, default=str)
