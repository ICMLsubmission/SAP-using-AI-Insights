"""
SAP Design by AI Insights - Final Streamlit Web App
Real LLM integration + Rich visualizations + Indication filtering
"""

import streamlit as st
import json
from datetime import datetime
import pandas as pd
import os

# Import core functions
from sap_design_final_core import (
    extract_text_from_document,
    parse_sap_with_llm,
    create_intelligence_table,
    analyze_assumption_landscape,
    analyze_trials_with_llm,
    create_visualizations,
    export_to_json,
    HAS_ANTHROPIC,
    HAS_PLOTLY
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
    .step-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px 25px;
        border-radius: 12px;
        margin: 20px 0 20px 0;
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .step-number {
        font-size: 32px;
        font-weight: bold;
        background: rgba(255,255,255,0.25);
        width: 50px;
        height: 50px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .step-title {
        font-size: 22px;
        font-weight: 600;
    }
    .success-box {
        background: #d4edda;
        border-left: 5px solid #28a745;
        padding: 15px;
        border-radius: 6px;
        margin: 15px 0;
    }
    .info-box {
        background: #d1ecf1;
        border-left: 5px solid #17a2b8;
        padding: 15px;
        border-radius: 6px;
        margin: 15px 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 13px;
        opacity: 0.9;
    }
</style>
""", unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("# 🔬 SAP Design by AI Insights")
    st.markdown("---")
    
    st.markdown("""
    ### About This Tool
    
    **Transform unstructured trial documents into structured intelligence through AI-powered analysis.**
    
    **Five-Step Workflow:**
    1. 📤 Upload SAP documents
    2. 🧠 AI parses each
    3. 📋 Select indication
    4. 📊 View intelligence table
    5. 📈 See landscape & analysis
    """)
    
    st.markdown("---")
    st.markdown("### 🔌 AI Integration Status")
    
    if HAS_ANTHROPIC:
        st.success("✓ **Claude API** - Real LLM parsing & analysis")
    else:
        st.warning("⚠ Mock mode (no API key)")
    
    if HAS_PLOTLY:
        st.success("✓ **Plotly** - Interactive visualizations")
    else:
        st.warning("⚠ Limited visualization")
    
    st.markdown("---")
    st.markdown("### 📊 Available Data")
    st.markdown("""
    - **NSCLC:** 4 trials
    - **Melanoma:** 2 trials  
    - **Breast Cancer:** 2 trials
    """)

# ==================== SESSION STATE ====================
if 'parsed_records' not in st.session_state:
    st.session_state.parsed_records = []
if 'selected_indication' not in st.session_state:
    st.session_state.selected_indication = None
if 'intelligence_table' not in st.session_state:
    st.session_state.intelligence_table = []
if 'landscape' not in st.session_state:
    st.session_state.landscape = {}
if 'llm_analysis' not in st.session_state:
    st.session_state.llm_analysis = ""
if 'visualizations' not in st.session_state:
    st.session_state.visualizations = {}

# ==================== HEADER ====================
st.markdown("""
# 🔬 SAP Design by AI Insights

**Transform unstructured trial documents into evidence-grounded design assumptions**

*Real Claude AI integration for parsing documents and analyzing trials*
""")

st.markdown("---")

# ==================== STEP 1: UPLOAD ====================
with st.container():
    st.markdown("""
    <div class="step-header">
        <div class="step-number">1</div>
        <div class="step-title">UPLOAD SAP DOCUMENTS</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("Upload one or more SAP documents (PDF or Word).")
    
    uploaded_files = st.file_uploader(
        "Choose SAP documents",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.markdown(f"""
        <div class="success-box">
        ✓ {len(uploaded_files)} file(s) uploaded
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ==================== STEP 2: PARSING ====================
with st.container():
    st.markdown("""
    <div class="step-header">
        <div class="step-number">2</div>
        <div class="step-title">🧠 AI PARSES DOCUMENTS</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.button("🚀 Parse with Claude AI", key="parse_button", use_container_width=True):
            if not uploaded_files:
                st.error("❌ Please upload at least one document first.")
            else:
                st.session_state.parsed_records = []
                st.session_state.selected_indication = None
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, uploaded_file in enumerate(uploaded_files):
                    progress = (idx + 1) / len(uploaded_files)
                    progress_bar.progress(progress)
                    status_text.info(f"🔄 Parsing {idx + 1}/{len(uploaded_files)}: **{uploaded_file.name}**")
                    
                    try:
                        file_bytes = uploaded_file.read()
                        extracted_text = extract_text_from_document(file_bytes, uploaded_file.name)
                        parsed_record = parse_sap_with_llm(extracted_text, uploaded_file.name)
                        st.session_state.parsed_records.append(parsed_record)
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                
                progress_bar.empty()
                status_text.success(f"✅ Parsed {len(st.session_state.parsed_records)} documents!")
    
    with col2:
        st.metric("Parsed", len(st.session_state.parsed_records))
    
    with col3:
        if st.session_state.parsed_records:
            indications = list(set([r.get("indication") for r in st.session_state.parsed_records]))
            st.metric("Indications", len(indications))

st.markdown("---")

# ==================== STEP 3: SELECT INDICATION ====================
if st.session_state.parsed_records:
    with st.container():
        st.markdown("""
        <div class="step-header">
            <div class="step-number">3</div>
            <div class="step-title">📋 SELECT INDICATION</div>
        </div>
        """, unsafe_allow_html=True)
        
        indications = sorted(list(set([r.get("indication") for r in st.session_state.parsed_records])))
        
        cols = st.columns(len(indications))
        for idx, indication in enumerate(indications):
            with cols[idx]:
                count = len([r for r in st.session_state.parsed_records if r.get("indication") == indication])
                if st.button(f"**{indication}** ({count})", use_container_width=True, key=f"ind_{indication}"):
                    st.session_state.selected_indication = indication
                    st.rerun()
        
        if st.session_state.selected_indication:
            count = len([r for r in st.session_state.parsed_records if r.get("indication") == st.session_state.selected_indication])
            st.markdown(f"""
            <div class="success-box">
            ✓ Analyzing {count} {st.session_state.selected_indication} trials
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ==================== STEP 4: INTELLIGENCE TABLE ====================
    if st.session_state.selected_indication:
        with st.container():
            st.markdown("""
            <div class="step-header">
                <div class="step-number">4</div>
                <div class="step-title">📊 INTELLIGENCE TABLE</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.session_state.intelligence_table = create_intelligence_table(
                st.session_state.parsed_records,
                st.session_state.selected_indication
            )
            
            if st.session_state.intelligence_table:
                table_df = pd.DataFrame(st.session_state.intelligence_table)
                st.dataframe(table_df, use_container_width=True, hide_index=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    json_str = export_to_json(st.session_state.intelligence_table)
                    st.download_button(
                        label="📥 Table as JSON",
                        data=json_str,
                        file_name=f"table_{st.session_state.selected_indication}.json",
                        mime="application/json"
                    )
                with col2:
                    csv_str = table_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Table as CSV",
                        data=csv_str,
                        file_name=f"table_{st.session_state.selected_indication}.csv",
                        mime="text/csv"
                    )
        
        st.markdown("---")
        
        # ==================== STEP 5: ASSUMPTION LANDSCAPE ====================
        with st.container():
            st.markdown("""
            <div class="step-header">
                <div class="step-number">5</div>
                <div class="step-title">📈 LANDSCAPE & AI ANALYSIS</div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔍 Generate Analysis with Claude", key="landscape_button", use_container_width=True):
                with st.spinner("Analyzing with AI..."):
                    st.session_state.landscape = analyze_assumption_landscape(
                        st.session_state.parsed_records,
                        st.session_state.selected_indication
                    )
                    
                    filtered_records = [r for r in st.session_state.parsed_records 
                                       if r.get("indication") == st.session_state.selected_indication]
                    st.session_state.llm_analysis = analyze_trials_with_llm(
                        filtered_records,
                        st.session_state.selected_indication
                    )
                    
                    st.session_state.visualizations = create_visualizations(
                        st.session_state.parsed_records,
                        st.session_state.selected_indication
                    )
                
                st.success("✅ Analysis complete!")
            
            if st.session_state.landscape:
                # Metrics
                st.subheader("📊 Summary Metrics")
                
                col1, col2, col3, col4 = st.columns(4)
                
                rr = st.session_state.landscape.get('response_rate', {})
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                    <div class="metric-label">Response Rate</div>
                    <div class="metric-value">{rr.get('mean', 0)*100:.0f}%</div>
                    <div class="metric-label">{rr.get('min', 0)*100:.0f}%-{rr.get('max', 0)*100:.0f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                ors = st.session_state.landscape.get('effect_size_or', {})
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                    <div class="metric-label">Effect Size (OR)</div>
                    <div class="metric-value">{ors.get('mean', 0):.2f}</div>
                    <div class="metric-label">{ors.get('min', 0):.2f}-{ors.get('max', 0):.2f}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                pw = st.session_state.landscape.get('power', {})
                with col3:
                    st.markdown(f"""
                    <div class="metric-card">
                    <div class="metric-label">Power</div>
                    <div class="metric-value">{pw.get('mean', 0)*100:.0f}%</div>
                    <div class="metric-label">{pw.get('min', 0)*100:.0f}%-{pw.get('max', 0)*100:.0f}%</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                ss = st.session_state.landscape.get('sample_size', {})
                with col4:
                    st.markdown(f"""
                    <div class="metric-card">
                    <div class="metric-label">Sample Size</div>
                    <div class="metric-value">{int(ss.get('mean', 0))}</div>
                    <div class="metric-label">{int(ss.get('min', 0))}-{int(ss.get('max', 0))}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # AI Analysis
                if st.session_state.llm_analysis:
                    st.subheader("🧠 Claude's Clinical Analysis")
                    st.markdown(f"""
                    <div class="info-box">
                    {st.session_state.llm_analysis}
                    </div>
                    """, unsafe_allow_html=True)
                
                # Visualizations
                if st.session_state.visualizations:
                    st.subheader("📊 Interactive Visualizations")
                    
                    tabs = st.tabs([
                        "Response Rate",
                        "Effect Size",
                        "Power",
                        "Sample Size",
                        "RR vs OR",
                        "Power vs N",
                        "RR Box",
                        "OR Box"
                    ])
                    
                    viz_list = [
                        st.session_state.visualizations.get('rr_histogram'),
                        st.session_state.visualizations.get('or_histogram'),
                        st.session_state.visualizations.get('power_histogram'),
                        st.session_state.visualizations.get('ss_histogram'),
                        st.session_state.visualizations.get('scatter_rr_or'),
                        st.session_state.visualizations.get('scatter_power_ss'),
                        st.session_state.visualizations.get('boxplot_rr'),
                        st.session_state.visualizations.get('boxplot_or'),
                    ]
                    
                    for tab, viz in zip(tabs, viz_list):
                        if viz:
                            with tab:
                                st.plotly_chart(viz, use_container_width=True)
                
                # Export
                st.subheader("💾 Export Results")
                col1, col2 = st.columns(2)
                
                with col1:
                    landscape_json = export_to_json(st.session_state.landscape)
                    st.download_button(
                        label="📥 Landscape (JSON)",
                        data=landscape_json,
                        file_name=f"landscape_{st.session_state.selected_indication}.json",
                        mime="application/json"
                    )
                
                with col2:
                    report = f"""# {st.session_state.selected_indication} Analysis

## Metrics
- Response Rate: {rr.get('mean', 0)*100:.0f}% (range {rr.get('min', 0)*100:.0f}%-{rr.get('max', 0)*100:.0f}%)
- Effect Size (OR): {ors.get('mean', 0):.2f} (range {ors.get('min', 0):.2f}-{ors.get('max', 0):.2f})
- Power: {pw.get('mean', 0)*100:.0f}% (range {pw.get('min', 0)*100:.0f}%-{pw.get('max', 0)*100:.0f}%)
- Sample Size: {int(ss.get('mean', 0))} (range {int(ss.get('min', 0))}-{int(ss.get('max', 0))})

## Analysis
{st.session_state.llm_analysis}
"""
                    st.download_button(
                        label="📥 Report (Markdown)",
                        data=report,
                        file_name=f"report_{st.session_state.selected_indication}.md",
                        mime="text/markdown"
                    )

st.markdown("---")
st.markdown("**SAP Design by AI Insights v2.0** | Powered by Claude AI 🚀")
