"""
SAP Design by AI Insights - Streamlit Web App

Three-step workflow:
1. Upload SAPs (PDF/Word documents)
2. AI parses each → Structured intelligence table
3. Analyze multiple → Assumption landscape
"""

import streamlit as st
import json
from datetime import datetime
import pandas as pd
import os

# Import core functions
from sap_design_core import (
    extract_text_from_document,
    parse_sap_with_llm,
    create_intelligence_table,
    analyze_assumption_landscape,
    format_landscape_for_display,
    export_table_as_json,
    export_landscape_as_json,
    HAS_ANTHROPIC,
    HAS_PYPDF,
    HAS_DOCX
)

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="SAP Design by AI Insights",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 16px;
        font-weight: 600;
    }
    .step-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .step-number {
        font-size: 36px;
        font-weight: bold;
        display: inline-block;
        width: 50px;
        height: 50px;
        background: rgba(255,255,255,0.2);
        border-radius: 50%;
        text-align: center;
        line-height: 50px;
        margin-right: 15px;
        vertical-align: middle;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 10px 0;
    }
    .success-box {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 12px;
        border-radius: 4px;
        margin: 10px 0;
    }
    .warning-box {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 12px;
        border-radius: 4px;
        margin: 10px 0;
    }
    .info-box {
        background: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 12px;
        border-radius: 4px;
        margin: 10px 0;
    }
    .table-header {
        background: #667eea;
        color: white;
        padding: 12px;
        border-radius: 6px 6px 0 0;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("# 🔬 SAP Design by AI Insights")
    st.markdown("---")
    
    st.markdown("""
    ### About This Tool
    
    Transform unstructured trial documents into structured intelligence.
    
    **Workflow:**
    1. Upload SAP documents (PDF/Word)
    2. AI parses each → Structured table
    3. Analyze multiple → Assumption landscape
    
    **No Python needed!** Just upload and analyze.
    """)
    
    st.markdown("---")
    
    st.markdown("### Status")
    if HAS_ANTHROPIC:
        st.success("✓ Claude API available")
    else:
        st.warning("⚠ Using mock mode (no API key)")
    
    if HAS_PYPDF:
        st.success("✓ PDF support")
    else:
        st.warning("⚠ PDF support limited")
    
    if HAS_DOCX:
        st.success("✓ Word support")
    else:
        st.warning("⚠ Word support limited")

# ==================== SESSION STATE ====================
if 'parsed_records' not in st.session_state:
    st.session_state.parsed_records = []

if 'intelligence_table' not in st.session_state:
    st.session_state.intelligence_table = []

if 'landscape' not in st.session_state:
    st.session_state.landscape = {}

# ==================== HEADER ====================
st.markdown("""
# 🔬 SAP Design by AI Insights

**Transform unstructured trial documents into evidence-grounded design assumptions**
""")

st.markdown("---")

# ==================== STEP 1: UPLOAD ====================
with st.container():
    st.markdown("""
    <div class="step-header">
        <span class="step-number">1</span>
        <span style="font-size: 24px; vertical-align: middle;">UPLOAD SAP DOCUMENTS</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("Upload one or more SAP documents (PDF or Word). The system will extract text and parse each document.")
    
    uploaded_files = st.file_uploader(
        "Choose SAP documents",
        type=["pdf", "docx"],
        accept_multiple_files=True,
        help="Upload PDF or Word documents containing Statistical Analysis Plans"
    )
    
    if uploaded_files:
        st.markdown(f"""
        <div class="success-box">
            ✓ {len(uploaded_files)} file(s) uploaded: {', '.join([f.name for f in uploaded_files])}
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ==================== STEP 2: PARSING ====================
with st.container():
    st.markdown("""
    <div class="step-header">
        <span class="step-number">2</span>
        <span style="font-size: 24px; vertical-align: middle;">AI PARSES → STRUCTURED TABLE</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("Click below to parse uploaded documents. The AI will extract key design parameters from each SAP.")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if st.button("🧠 Parse Documents with AI", key="parse_button", use_container_width=True):
            if not uploaded_files:
                st.error("Please upload at least one document first.")
            else:
                # Clear previous results
                st.session_state.parsed_records = []
                st.session_state.intelligence_table = []
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                results_container = st.container()
                
                for idx, uploaded_file in enumerate(uploaded_files):
                    # Update progress
                    progress = (idx + 1) / len(uploaded_files)
                    progress_bar.progress(progress)
                    
                    status_text.info(f"🔄 Parsing {idx + 1} of {len(uploaded_files)}: {uploaded_file.name}")
                    
                    try:
                        # Read file
                        file_bytes = uploaded_file.read()
                        
                        # Extract text
                        extracted_text = extract_text_from_document(file_bytes, uploaded_file.name)
                        
                        # Parse with LLM
                        parsed_record = parse_sap_with_llm(extracted_text, uploaded_file.name)
                        
                        st.session_state.parsed_records.append(parsed_record)
                        
                        # Display parsing result
                        with results_container:
                            st.markdown(f"""
                            <div class="success-box">
                            ✓ Parsed: <strong>{parsed_record.get('trial_id', 'Unknown')}</strong>
                            - {parsed_record.get('indication', 'Unknown')} (Phase {parsed_record.get('phase', '?')})
                            - RR: {parsed_record.get('assumed_response_rate', 0)*100:.0f}% | OR: {parsed_record.get('effect_size_or', 0):.2f} | Power: {parsed_record.get('power', 0)*100:.0f}%
                            </div>
                            """, unsafe_allow_html=True)
                    
                    except Exception as e:
                        st.error(f"Error parsing {uploaded_file.name}: {str(e)}")
                
                # Create intelligence table
                st.session_state.intelligence_table = create_intelligence_table(st.session_state.parsed_records)
                
                progress_bar.empty()
                status_text.success(f"✅ Successfully parsed {len(st.session_state.parsed_records)} document(s)!")
    
    with col2:
        st.metric("Files Parsed", len(st.session_state.parsed_records))
    
    # Display intelligence table
    if st.session_state.intelligence_table:
        st.markdown("### 📊 Structured Intelligence Table")
        st.markdown("Extracted fields from all uploaded SAPs:")
        
        table_df = pd.DataFrame(st.session_state.intelligence_table)
        st.dataframe(table_df, use_container_width=True, hide_index=True)
        
        # Export options
        col1, col2 = st.columns(2)
        with col1:
            json_str = export_table_as_json(st.session_state.intelligence_table)
            st.download_button(
                label="📥 Download Table (JSON)",
                data=json_str,
                file_name=f"intelligence_table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col2:
            csv_str = table_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Table (CSV)",
                data=csv_str,
                file_name=f"intelligence_table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

st.markdown("---")

# ==================== STEP 3: ASSUMPTION LANDSCAPE ====================
with st.container():
    st.markdown("""
    <div class="step-header">
        <span class="step-number">3</span>
        <span style="font-size: 24px; vertical-align: middle;">ANALYZE → ASSUMPTION LANDSCAPE</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("Aggregate all parsed trials to derive typical assumption ranges (the assumption landscape).")
    
    if st.button("📊 Generate Assumption Landscape", key="landscape_button", use_container_width=True):
        if not st.session_state.parsed_records:
            st.error("Please parse documents first (Step 2).")
        else:
            st.session_state.landscape = analyze_assumption_landscape(st.session_state.parsed_records)
            st.success("✅ Assumption landscape generated!")
    
    # Display landscape
    if st.session_state.landscape:
        st.markdown("### 📈 Assumption Landscape Summary")
        
        # Format for display
        landscape_display = format_landscape_for_display(st.session_state.landscape)
        
        # Create columns for metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### Response Rate")
            st.markdown(f"""
            <div class="metric-card">
            <strong>Range:</strong> {landscape_display.get('Response Rate Range', 'N/A')}<br>
            <strong>Mean:</strong> {landscape_display.get('Response Rate Mean', 'N/A')}<br>
            <strong>Trials:</strong> {st.session_state.landscape.get('total_trials', 0)}
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### Effect Size (OR)")
            st.markdown(f"""
            <div class="metric-card">
            <strong>Range:</strong> {landscape_display.get('Effect Size (OR) Range', 'N/A')}<br>
            <strong>Mean:</strong> {landscape_display.get('Effect Size (OR) Mean', 'N/A')}
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("#### Power")
            st.markdown(f"""
            <div class="metric-card">
            <strong>Range:</strong> {landscape_display.get('Power Range', 'N/A')}<br>
            <strong>Mean:</strong> {landscape_display.get('Power Mean', 'N/A')}
            </div>
            """, unsafe_allow_html=True)
        
        # Full landscape table
        st.markdown("### 📋 Full Landscape Summary")
        landscape_df = pd.DataFrame(landscape_display.items(), columns=["Metric", "Value"])
        st.dataframe(landscape_df, use_container_width=True, hide_index=True)
        
        # Export landscape
        col1, col2 = st.columns(2)
        with col1:
            json_str = export_landscape_as_json(st.session_state.landscape)
            st.download_button(
                label="📥 Download Landscape (JSON)",
                data=json_str,
                file_name=f"assumption_landscape_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        
        with col2:
            landscape_df.to_csv(f"assumption_landscape_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", index=False)
            st.info("💾 Landscape data ready for export")

st.markdown("---")

# ==================== FOOTER ====================
st.markdown("""
---

**SAP Design by AI Insights v1.0** | Transform unstructured trial documents into evidence-grounded design assumptions
""")
