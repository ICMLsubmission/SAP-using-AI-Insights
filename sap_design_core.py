"""
SAP Design by AI Insights - Core Logic
Handles: PDF/Document upload → AI parsing → Structured intelligence table → Assumption landscape

Three-step workflow:
1. Upload SAPs (PDF/Word documents)
2. AI parses each SAP → structured intelligence table
3. Analyze multiple tables → assumption landscape
"""

import json
from typing import List, Dict, Optional
import os

# Try to import optional dependencies
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


# ==================== SCHEMA ====================
EXTRACTION_SCHEMA = {
    "trial_id": "str (e.g., KEYNOTE-024)",
    "indication": "str (e.g., NSCLC, Melanoma)",
    "phase": "str (e.g., II, III)",
    "primary_endpoint": "str (e.g., PFS, OS, ORR)",
    "endpoint_type": "str (e.g., Binary (ORR), Time-to-event)",
    "assumed_response_rate": "float (0-1, e.g., 0.45 for 45%)",
    "control_response_rate": "float (0-1)",
    "effect_size_or": "float (odds ratio, e.g., 1.8)",
    "power": "float (0-1, e.g., 0.90 for 90%)",
    "alpha": "float (e.g., 0.05)",
    "sample_size": "int (total N)",
    "primary_analysis": "str (e.g., Cox proportional hazards)",
    "study_population": "str (e.g., PD-L1 ≥50%)",
    "treatment": "str (e.g., Pembrolizumab monotherapy)"
}


# ==================== TEXT EXTRACTION ====================

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF file"""
    if not HAS_PYPDF:
        return "[PDF extraction requires PyPDF2 - returning mock data]"
    
    try:
        from io import BytesIO
        pdf_file = BytesIO(pdf_bytes)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"


def extract_text_from_docx(docx_bytes: bytes) -> str:
    """Extract text from Word document"""
    if not HAS_DOCX:
        return "[DOCX extraction requires python-docx - returning mock data]"
    
    try:
        from io import BytesIO
        docx_file = BytesIO(docx_bytes)
        doc = DocxDocument(docx_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        return f"Error extracting DOCX: {str(e)}"


def extract_text_from_document(file_bytes: bytes, filename: str) -> str:
    """Extract text based on file type"""
    if filename.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_bytes)
    elif filename.lower().endswith('.docx'):
        return extract_text_from_docx(file_bytes)
    else:
        return "[Unsupported file type]"


# ==================== LLM PARSING ====================

def parse_sap_with_llm(sap_text: str, trial_filename: str = "Unknown") -> Dict:
    """
    Use Claude to extract structured fields from unstructured SAP text
    
    Returns a structured record with all key fields from the schema
    Falls back to mock data if Anthropic not available
    """
    
    if not HAS_ANTHROPIC:
        # Mock response for demo
        return generate_mock_parsed_record(trial_filename)
    
    try:
        client = Anthropic()
        
        schema_str = json.dumps(EXTRACTION_SCHEMA, indent=2)
        
        prompt = f"""You are a clinical trial data extraction expert.

Extract the following fields from this Statistical Analysis Plan (SAP) text.
Return ONLY a valid JSON object with these fields. If a field is not found, use null.

REQUIRED SCHEMA:
{schema_str}

SAP TEXT:
{sap_text[:3000]}

Return ONLY the JSON object, no other text or markdown."""

        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=800,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        result_text = response.content[0].text
        
        # Clean up markdown if present
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()
        
        parsed = json.loads(result_text)
        
        # Ensure all fields are present
        for key in EXTRACTION_SCHEMA.keys():
            if key not in parsed:
                parsed[key] = None
        
        # Add filename for reference
        parsed["_source_file"] = trial_filename
        
        return parsed
        
    except Exception as e:
        print(f"LLM parsing error: {str(e)}. Using mock data.")
        return generate_mock_parsed_record(trial_filename)


def generate_mock_parsed_record(trial_filename: str) -> Dict:
    """Generate mock parsed record for testing"""
    
    # Map filenames to realistic data
    mock_data = {
        "KEYNOTE-024": {
            "trial_id": "KEYNOTE-024",
            "indication": "NSCLC",
            "phase": "III",
            "primary_endpoint": "PFS",
            "endpoint_type": "Time-to-event",
            "assumed_response_rate": 0.45,
            "control_response_rate": 0.28,
            "effect_size_or": 1.8,
            "power": 0.90,
            "alpha": 0.05,
            "sample_size": 305,
            "primary_analysis": "Cox proportional hazards regression",
            "study_population": "PD-L1 ≥50%",
            "treatment": "Pembrolizumab monotherapy"
        },
        "ATTRACT-2": {
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
        "CheckMate-057": {
            "trial_id": "CheckMate-057",
            "indication": "NSCLC",
            "phase": "III",
            "primary_endpoint": "OS",
            "endpoint_type": "Time-to-event",
            "assumed_response_rate": 0.20,
            "control_response_rate": 0.09,
            "effect_size_or": 1.3,
            "power": 0.90,
            "alpha": 0.05,
            "sample_size": 582,
            "primary_analysis": "Cox proportional hazards regression",
            "study_population": "Non-squamous NSCLC",
            "treatment": "Nivolumab monotherapy"
        }
    }
    
    # Try to match filename
    for key, data in mock_data.items():
        if key in trial_filename:
            result = data.copy()
            result["_source_file"] = trial_filename
            return result
    
    # Default to KEYNOTE-024
    result = mock_data["KEYNOTE-024"].copy()
    result["_source_file"] = trial_filename
    return result


# ==================== INTELLIGENCE TABLE ====================

def create_intelligence_table(parsed_records: List[Dict]) -> List[Dict]:
    """
    Create structured intelligence table from parsed SAP records
    Each row is a trial with extracted fields
    """
    
    table = []
    
    for record in parsed_records:
        row = {
            "Trial ID": record.get("trial_id", "Unknown"),
            "Indication": record.get("indication", "Unknown"),
            "Phase": record.get("phase", "Unknown"),
            "Endpoint": record.get("primary_endpoint", "Unknown"),
            "RR %": f"{record.get('assumed_response_rate', 0)*100:.0f}%" if record.get('assumed_response_rate') else "N/A",
            "Control %": f"{record.get('control_response_rate', 0)*100:.0f}%" if record.get('control_response_rate') else "N/A",
            "OR": f"{record.get('effect_size_or', 0):.2f}" if record.get('effect_size_or') else "N/A",
            "Power": f"{record.get('power', 0)*100:.0f}%" if record.get('power') else "N/A",
            "N": record.get("sample_size", "Unknown"),
            "Treatment": record.get("treatment", "Unknown")
        }
        table.append(row)
    
    return table


# ==================== ASSUMPTION LANDSCAPE ====================

def analyze_assumption_landscape(parsed_records: List[Dict]) -> Dict:
    """
    Analyze multiple parsed trial records to create assumption landscape
    Computes: min, max, mean, median for key metrics
    """
    
    if not parsed_records:
        return {}
    
    # Extract numeric values
    response_rates = [r.get("assumed_response_rate", 0) for r in parsed_records 
                     if r.get("assumed_response_rate") is not None]
    control_rates = [r.get("control_response_rate", 0) for r in parsed_records 
                    if r.get("control_response_rate") is not None]
    effect_sizes = [r.get("effect_size_or", 0) for r in parsed_records 
                   if r.get("effect_size_or") is not None]
    powers = [r.get("power", 0) for r in parsed_records 
             if r.get("power") is not None]
    sample_sizes = [r.get("sample_size", 0) for r in parsed_records 
                   if r.get("sample_size") is not None]
    
    def compute_stats(values):
        """Compute min, max, mean, median"""
        if not values:
            return {}
        sorted_vals = sorted(values)
        return {
            "min": min(values),
            "max": max(values),
            "mean": sum(values) / len(values),
            "median": sorted_vals[len(values) // 2]
        }
    
    landscape = {
        "total_trials": len(parsed_records),
        "response_rate": compute_stats(response_rates),
        "control_rate": compute_stats(control_rates),
        "effect_size_or": compute_stats(effect_sizes),
        "power": compute_stats(powers),
        "sample_size": compute_stats(sample_sizes),
        "indications": list(set([r.get("indication", "Unknown") for r in parsed_records])),
        "phases": list(set([r.get("phase", "Unknown") for r in parsed_records])),
        "common_treatments": list(set([r.get("treatment", "Unknown") for r in parsed_records]))[:5]
    }
    
    return landscape


# ==================== FORMATTING ====================

def format_landscape_for_display(landscape: Dict) -> Dict:
    """Format landscape data for display"""
    
    if not landscape:
        return {}
    
    def format_range(stats, is_percent=False, decimals=1):
        if not stats:
            return "N/A"
        min_val = stats.get("min", 0)
        max_val = stats.get("max", 0)
        if is_percent:
            return f"{min_val*100:.0f}%–{max_val*100:.0f}%"
        else:
            return f"{min_val:.{decimals}f}–{max_val:.{decimals}f}"
    
    return {
        "Total Trials Analyzed": landscape.get("total_trials", 0),
        "Response Rate Range": format_range(landscape.get("response_rate"), is_percent=True),
        "Response Rate Mean": f"{landscape.get('response_rate', {}).get('mean', 0)*100:.0f}%",
        "Control Rate Range": format_range(landscape.get("control_rate"), is_percent=True),
        "Effect Size (OR) Range": format_range(landscape.get("effect_size_or"), is_percent=False, decimals=2),
        "Effect Size (OR) Mean": f"{landscape.get('effect_size_or', {}).get('mean', 0):.2f}",
        "Power Range": format_range(landscape.get("power"), is_percent=True),
        "Power Mean": f"{landscape.get('power', {}).get('mean', 0)*100:.0f}%",
        "Sample Size Range": f"{int(landscape.get('sample_size', {}).get('min', 0))}–{int(landscape.get('sample_size', {}).get('max', 0))}",
        "Sample Size Mean": f"{int(landscape.get('sample_size', {}).get('mean', 0))}",
        "Indications": ", ".join(landscape.get("indications", [])),
        "Phases": ", ".join(landscape.get("phases", [])),
        "Common Treatments": ", ".join(landscape.get("common_treatments", []))
    }


# ==================== EXPORT ====================

def export_table_as_json(table: List[Dict]) -> str:
    """Export intelligence table as JSON"""
    return json.dumps(table, indent=2)


def export_landscape_as_json(landscape: Dict) -> str:
    """Export landscape as JSON"""
    return json.dumps(landscape, indent=2)
