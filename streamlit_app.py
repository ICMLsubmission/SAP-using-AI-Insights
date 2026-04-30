"""
SAP Design by AI Insights - Streamlit App
Make trial designs informed by historical SAPs instead of from scratch
"""

import streamlit as st
import json
from datetime import datetime
import pandas as pd
import plotly.graph_objects as go

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
    st.markdown("# 🧠 AI Powered SAP Design")
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
st.markdown("# 🧠 AI Powered SAP Design")
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
        trials = st.session_state.landscape.get("trials", [])
        
        # METRICS CARDS
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
        
        # ==================== VISUALIZATIONS ====================
        st.markdown("### Visual Analysis of Historical Trials")
        
        # Extract data for plots
        rr_values = [t.get("rr", 0) * 100 for t in trials if t.get("rr")]
        or_values = [t.get("or", 0) for t in trials if t.get("or")]
        trial_ids = [t.get("id", "") for t in trials]
        
        # Create tabs for different visualizations
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Response Rate Distribution",
            "📈 Effect Size Distribution", 
            "🔗 RR vs OR Relationship",
            "📋 Trial Summary"
        ])
        
        # ========== TAB 1: Response Rate Histogram ==========
        with tab1:
            st.markdown(f"**Response Rate Histogram** - Distribution across {len(rr_values)} {st.session_state.selected_indication} trials")
            
            if rr_values:
                fig_rr = go.Figure()
                fig_rr.add_trace(go.Histogram(
                    x=rr_values,
                    nbinsx=max(3, len(rr_values) // 2),
                    marker_color='#3498db',
                    name='Response Rate %',
                    showlegend=False,
                    hovertemplate='<b>RR Range</b>: %{x:.0f}%<br><b>Count</b>: %{y}<extra></extra>'
                ))
                fig_rr.add_vline(
                    x=rr.get('mean', 0) * 100,
                    line_dash="dash",
                    line_color="red",
                    line_width=2,
                    annotation_text=f"Mean: {rr.get('mean', 0)*100:.0f}%",
                    annotation_position="top right"
                )
                fig_rr.update_layout(
                    title=f"Response Rate Distribution - {st.session_state.selected_indication}",
                    xaxis_title="Response Rate (%)",
                    yaxis_title="Number of Trials",
                    template="plotly_white",
                    height=450,
                    showlegend=False
                )
                st.plotly_chart(fig_rr, use_container_width=True)
                
                st.markdown(f"""
                **Key Insights:**
                - **Mean RR:** {rr.get('mean', 0)*100:.0f}% (use this for base case)
                - **Median RR:** {rr.get('median', 0)*100:.0f}%
                - **Range:** {rr.get('min', 0)*100:.0f}% - {rr.get('max', 0)*100:.0f}%
                - **Spread:** Indicates variability in trial outcomes
                """)
        
        # ========== TAB 2: Effect Size Histogram ==========
        with tab2:
            st.markdown(f"**Effect Size (OR) Histogram** - Distribution across {len(or_values)} {st.session_state.selected_indication} trials")
            
            if or_values:
                fig_or = go.Figure()
                fig_or.add_trace(go.Histogram(
                    x=or_values,
                    nbinsx=max(3, len(or_values) // 2),
                    marker_color='#2ecc71',
                    name='Odds Ratio',
                    showlegend=False,
                    hovertemplate='<b>OR Range</b>: %{x:.2f}<br><b>Count</b>: %{y}<extra></extra>'
                ))
                fig_or.add_vline(
                    x=ors.get('mean', 0),
                    line_dash="dash",
                    line_color="red",
                    line_width=2,
                    annotation_text=f"Mean: {ors.get('mean', 0):.2f}",
                    annotation_position="top right"
                )
                fig_or.update_layout(
                    title=f"Effect Size (OR) Distribution - {st.session_state.selected_indication}",
                    xaxis_title="Odds Ratio (OR)",
                    yaxis_title="Number of Trials",
                    template="plotly_white",
                    height=450,
                    showlegend=False
                )
                st.plotly_chart(fig_or, use_container_width=True)
                
                st.markdown(f"""
                **Key Insights:**
                - **Mean OR:** {ors.get('mean', 0):.2f}x (drug is {ors.get('mean', 0):.2f}x better than control)
                - **Median OR:** {ors.get('median', 0):.2f}
                - **Range:** {ors.get('min', 0):.2f} - {ors.get('max', 0):.2f}
                - **Consistency:** Tighter distribution = more predictable effect
                """)
        
        # ========== TAB 3: RR vs OR Scatter Plot ==========
        with tab3:
            st.markdown(f"**RR vs OR Relationship** - How response rate relates to effect size")
            
            if rr_values and or_values:
                fig_scatter = go.Figure()
                
                fig_scatter.add_trace(go.Scatter(
                    x=rr_values,
                    y=or_values,
                    mode='markers+text',
                    marker=dict(
                        size=12,
                        color='#667eea',
                        opacity=0.7,
                        line=dict(color='#764ba2', width=2)
                    ),
                    text=trial_ids,
                    textposition='top center',
                    textfont=dict(size=10),
                    hovertemplate='<b>%{text}</b><br>RR: %{x:.0f}%<br>OR: %{y:.2f}<extra></extra>',
                    showlegend=False
                ))
                
                # Add mean lines
                fig_scatter.add_vline(
                    x=rr.get('mean', 0) * 100,
                    line_dash="dash",
                    line_color="rgba(255, 0, 0, 0.3)",
                    annotation_text="Mean RR"
                )
                fig_scatter.add_hline(
                    y=ors.get('mean', 0),
                    line_dash="dash",
                    line_color="rgba(255, 0, 0, 0.3)",
                    annotation_text="Mean OR"
                )
                
                fig_scatter.update_layout(
                    title=f"Response Rate vs Effect Size - {st.session_state.selected_indication}",
                    xaxis_title="Response Rate (%)",
                    yaxis_title="Odds Ratio (OR)",
                    template="plotly_white",
                    height=450,
                    hovermode='closest'
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
                
                st.markdown(f"""
                **Key Insights:**
                - **Pattern:** Shows if high RR trials also have high OR
                - **Outliers:** Trials far from the cluster may have special characteristics
                - **Correlation:** Helps understand assumption relationships
                - **New Drug Design:** Expect similar RR-OR relationship
                """)
        
        # ========== TAB 4: Trial Summary Table ==========
        with tab4:
            st.markdown(f"**Trial Summary Table** - All {len(trials)} {st.session_state.selected_indication} trials")
            
            if trials:
                # Create DataFrame
                summary_df = pd.DataFrame([
                    {
                        "Trial ID": t.get("id", ""),
                        "Response Rate (%)": f"{t.get('rr', 0)*100:.0f}%",
                        "Effect Size (OR)": f"{t.get('or', 0):.2f}"
                    }
                    for t in trials
                ])
                
                st.dataframe(summary_df, use_container_width=True, hide_index=True)
                
                st.markdown(f"""
                **Legend:**
                - **Trial ID:** Identifier of the historical trial
                - **Response Rate (%):** Percentage of patients who responded to treatment
                - **Effect Size (OR):** How much better the drug is vs control (1.0 = no difference)
                """)

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
**🧠 AI Powered SAP Design** | Make designs evidence-driven, not guesswork
""")
