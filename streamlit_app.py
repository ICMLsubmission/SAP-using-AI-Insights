"""
SAP Design by AI Insights - Streamlit App
Make trial designs informed by historical SAPs instead of from scratch
"""

import streamlit as st
import json
from datetime import datetime
import pandas as pd

from sap_design_core import (
    extract_text_from_document,
    parse_sap_with_llm,
    analyze_assumption_landscape,
    generate_scenarios,
    sensitivity_analysis,
    create_solara_input,
    export_to_json,
    HAS_ANTHROPIC
)

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="SAP Design by AI Insights",
    page_icon="🔬",
    layout="wide"
)

st.markdown("""
<style>
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
.scenario-box {
    background: #f8f9fa;
    border-left: 4px solid #667eea;
    padding: 15px;
    border-radius: 6px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("# 🔬 SAP Design by AI Insights")
    st.markdown("""
    ### Vision
    Make new drug trial designs more **informed and evidence-driven** 
    by analyzing historical SAPs instead of building from scratch.
    
    ### How It Works
    1. Parse historical SAPs with AI
    2. Identify patterns (assumption landscape)
    3. Generate 3 scenarios for new drug
    4. SOLARA-ready output
    5. Sensitivity analysis
    """)
    
    st.markdown("---")
    if HAS_ANTHROPIC:
        st.success("✓ Claude API Available")
    else:
        st.warning("⚠ Mock mode (no API)")

# ==================== SESSION STATE ====================
if 'parsed_records' not in st.session_state:
    st.session_state.parsed_records = []
if 'selected_indication' not in st.session_state:
    st.session_state.selected_indication = None
if 'landscape' not in st.session_state:
    st.session_state.landscape = {}
if 'scenarios' not in st.session_state:
    st.session_state.scenarios = {}
if 'solara_input' not in st.session_state:
    st.session_state.solara_input = {}

# ==================== HEADER ====================
st.markdown("# 🔬 SAP Design by AI Insights")
st.markdown("**Build trial designs informed by historical evidence, not from scratch**")
st.markdown("---")

# ==================== STEP 1: UPLOAD ====================
st.subheader("Step 1: Upload Historical SAP Documents")
st.markdown("Upload 1+ SAP documents to build the assumption landscape.")

uploaded_files = st.file_uploader(
    "Choose SAP documents",
    type=["pdf", "docx"],
    accept_multiple_files=True
)

if uploaded_files:
    st.markdown(f"""
    <div class="success-box">
    ✓ {len(uploaded_files)} file(s) selected
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==================== STEP 2: PARSE ====================
st.subheader("Step 2: Parse with AI")

if st.button("🧠 Parse Documents", use_container_width=True):
    if not uploaded_files:
        st.error("Please upload documents first")
    else:
        st.session_state.parsed_records = []
        progress_bar = st.progress(0)
        status = st.empty()
        
        for idx, file in enumerate(uploaded_files):
            progress_bar.progress((idx + 1) / len(uploaded_files))
            status.info(f"Parsing {idx + 1}/{len(uploaded_files)}: {file.name}")
            
            try:
                file_bytes = file.read()
                text = extract_text_from_document(file_bytes, file.name)
                parsed = parse_sap_with_llm(text, file.name)
                st.session_state.parsed_records.append(parsed)
            except Exception as e:
                st.error(f"Error: {str(e)}")
        
        progress_bar.empty()
        status.success(f"✅ Parsed {len(st.session_state.parsed_records)} documents")

if st.session_state.parsed_records:
    st.markdown(f"""
    <div class="success-box">
    ✓ {len(st.session_state.parsed_records)} documents parsed
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==================== STEP 3: SELECT INDICATION ====================
if st.session_state.parsed_records:
    st.subheader("Step 3: Select Cancer Type")
    
    indications = sorted(list(set([r.get("indication") for r in st.session_state.parsed_records])))
    
    cols = st.columns(len(indications))
    for idx, indication in enumerate(indications):
        count = len([r for r in st.session_state.parsed_records if r.get("indication") == indication])
        with cols[idx]:
            if st.button(f"{indication} ({count})", use_container_width=True):
                st.session_state.selected_indication = indication
                st.rerun()
    
    if st.session_state.selected_indication:
        st.markdown(f"""
        <div class="info-box">
        Analyzing {st.session_state.selected_indication}
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ==================== STEP 4: BUILD LANDSCAPE ====================
if st.session_state.selected_indication:
    st.subheader("Step 4: Build Assumption Landscape")
    st.markdown(f"What do successful {st.session_state.selected_indication} trials look like?")
    
    if st.button("📊 Analyze Historical Patterns", use_container_width=True):
        st.session_state.landscape = analyze_assumption_landscape(
            st.session_state.parsed_records,
            st.session_state.selected_indication
        )
        st.session_state.scenarios = generate_scenarios(
            st.session_state.landscape,
            st.session_state.selected_indication
        )
        st.session_state.solara_input = create_solara_input(
            st.session_state.scenarios["base"],
            st.session_state.scenarios["optimistic"],
            st.session_state.scenarios["pessimistic"],
            st.session_state.selected_indication,
            st.session_state.landscape
        )
        st.rerun()
    
    if st.session_state.landscape:
        st.markdown("### Historical Context")
        
        rr = st.session_state.landscape.get("response_rate", {})
        ors = st.session_state.landscape.get("effect_size_or", {})
        ss = st.session_state.landscape.get("sample_size", {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
            <div>Response Rate</div>
            <div class="metric-value">{rr.get('mean', 0)*100:.0f}%</div>
            <div>Range: {rr.get('min', 0)*100:.0f}%-{rr.get('max', 0)*100:.0f}%</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
            <div>Effect Size (OR)</div>
            <div class="metric-value">{ors.get('mean', 0):.2f}</div>
            <div>Range: {ors.get('min', 0):.2f}-{ors.get('max', 0):.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
            <div>Sample Size</div>
            <div class="metric-value">{int(ss.get('mean', 0))}</div>
            <div>Range: {int(ss.get('min', 0))}-{int(ss.get('max', 0))}</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("---")

# ==================== STEP 5: THREE SCENARIOS ====================
if st.session_state.scenarios:
    st.subheader("Step 5: Design Scenarios for New Drug")
    st.markdown("Three scenarios informed by historical evidence")
    
    col1, col2, col3 = st.columns(3)
    
    scenarios_list = [
        ("base", "🟢", col1),
        ("optimistic", "🔵", col2),
        ("pessimistic", "🟠", col3)
    ]
    
    for key, emoji, col in scenarios_list:
        scenario = st.session_state.scenarios[key]
        with col:
            st.markdown(f"""
            <div class="scenario-box">
            {emoji} **{scenario['name']}**
            
            - **RR:** {scenario['rr']*100:.0f}%
            - **OR:** {scenario['or']:.2f}
            - **N:** {scenario['sample_size']}
            - **Power:** {scenario['power']*100:.0f}%
            
            Confidence: {scenario['confidence']}
            
            {scenario['rationale']}
            </div>
            """, unsafe_allow_html=True)
    
    # Sensitivity Analysis
    st.subheader("Sensitivity Analysis")
    st.markdown("What if assumptions change?")
    
    base = st.session_state.scenarios["base"]
    sensitivity = sensitivity_analysis(
        base["rr"], base["or"], base["sample_size"], base["power"]
    )
    
    sensitivity_df = pd.DataFrame([
        {"Parameter": k, "New Power": f"{v['power']*100:.0f}%", "Impact": f"{v['impact']:+.1f}%"}
        for k, v in sensitivity.items()
    ])
    
    st.dataframe(sensitivity_df, use_container_width=True, hide_index=True)
    
    # SOLARA Input
    st.subheader("SOLARA Input (Ready to Export)")
    st.markdown("Three scenarios + sensitivity parameters for SOLARA stress-testing")
    
    solara_json = export_to_json(st.session_state.solara_input)
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 Download SOLARA Input (JSON)",
            data=solara_json,
            file_name=f"solara_input_{st.session_state.selected_indication}_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
    
    with col2:
        # Create text summary
        summary = f"""# SOLARA Input Summary - {st.session_state.selected_indication}

## Base Case (Most Likely)
- Response Rate: {base['rr']*100:.0f}%
- Effect Size (OR): {base['or']:.2f}
- Sample Size: {base['sample_size']}
- Power: {base['power']*100:.0f}%
- Rationale: {base['rationale']}

## Optimistic Scenario
- RR: {st.session_state.scenarios['optimistic']['rr']*100:.0f}%
- OR: {st.session_state.scenarios['optimistic']['or']:.2f}

## Pessimistic Scenario
- RR: {st.session_state.scenarios['pessimistic']['rr']*100:.0f}%
- OR: {st.session_state.scenarios['pessimistic']['or']:.2f}

## Historical Support
- {st.session_state.landscape.get('total_trials', 0)} trials inform this design
- Trials: {', '.join([t['id'] for t in st.session_state.landscape.get('trials', [])])}

---
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        st.download_button(
            label="📥 Download Summary (Markdown)",
            data=summary,
            file_name=f"summary_{st.session_state.selected_indication}_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown"
        )
    
    # Show raw JSON
    with st.expander("View Full SOLARA Input JSON"):
        st.json(st.session_state.solara_input)

st.markdown("---")
st.markdown("""
**SAP Design by AI Insights** | Make designs evidence-driven, not guesswork
""")
