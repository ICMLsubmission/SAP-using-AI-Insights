"""
SOLARA Demo - Streamlit Cloud App
Run this with: streamlit run streamlit_app.py

Deploy to Streamlit Cloud:
1. Push this repo to GitHub
2. Go to https://streamlit.io/cloud
3. Click "New app" → Select this repo
4. Done! Share the URL
"""

import streamlit as st
import json
from datetime import datetime
import pandas as pd

# ==================== IMPORT SOLARA FUNCTIONS ====================
import sys
sys.path.append('.')

try:
    from solara_demo import (
        MOCK_TRIALS,
        SAMPLE_SAP,
        analyze_assumption_landscape,
        generate_solara_input,
        parse_sap_with_llm,
        HAS_ANTHROPIC
    )
except ImportError:
    st.error("Could not import SOLARA modules. Make sure solara_demo.py is in the same directory.")
    st.stop()

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="SOLARA Demo",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 16px;
    }
    .metric-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-label {
        font-size: 12px;
        opacity: 0.9;
    }
    .rationale-good {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 12px;
        border-radius: 4px;
        margin: 8px 0;
    }
    .rationale-warning {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 12px;
        border-radius: 4px;
        margin: 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==================== HEADER ====================
st.markdown("""
# 🔬 SOLARA Demo
## AI-Derived Trial Design Intelligence

**Transform unstructured trial documents into evidence-grounded design assumptions for SOLARA stress-testing.**
""")

if not HAS_ANTHROPIC:
    st.warning("⚠️ Anthropic SDK not available - using mock LLM responses. Set `ANTHROPIC_API_KEY` environment variable to use real Claude API.")

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("🎯 Navigation")
    page = st.radio(
        "Select a tool:",
        ["🏠 Home", "📊 Landscape", "📄 Parse SAP", "🎨 Design Solver", "📈 Compare Designs", "ℹ️ About"]
    )
    
    st.divider()
    st.subheader("📚 Quick Links")
    st.markdown("""
    - [GitHub Repo](https://github.com/yourusername/solara-demo)
    - [Documentation](https://github.com/yourusername/solara-demo#readme)
    - [Colab Notebook](https://colab.research.google.com/)
    """)

# ==================== PAGE: HOME ====================
if page == "🏠 Home":
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("What is SOLARA?")
        st.markdown("""
        SOLARA is a tool for **stress-testing trial designs** under uncertainty.
        
        This demo helps you:
        1. **Parse** unstructured SAPs into structured data
        2. **Analyze** historical trials to understand typical assumptions
        3. **Compare** your design to precedent
        4. **Generate** SOLARA input with evidence-based rationale
        """)
    
    with col2:
        st.header("Quick Example")
        st.markdown("""
        **You input:**
        - Response rate: 42%
        - Effect size (OR): 1.65
        - Power: 90%
        
        **You get:**
        - ✓ "Response rate 42% within historical range (35%-45%)"
        - ✓ "Effect size supported by precedent"
        - 📋 Ready for SOLARA analysis
        """)
    
    st.divider()
    st.subheader("🚀 Getting Started")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 1. Explore Landscape")
        st.markdown("View 6 historical NSCLC trials")
        if st.button("Go to Landscape →", key="home_landscape"):
            st.session_state.page = "📊 Landscape"
    
    with col2:
        st.markdown("### 2. Parse a SAP")
        st.markdown("See unstructured text → structured JSON")
        if st.button("Go to Parser →", key="home_parser"):
            st.session_state.page = "📄 Parse SAP"
    
    with col3:
        st.markdown("### 3. Design Your Trial")
        st.markdown("Input assumptions → Get rationale")
        if st.button("Go to Designer →", key="home_designer"):
            st.session_state.page = "🎨 Design Solver"

# ==================== PAGE: LANDSCAPE ====================
elif page == "📊 Landscape":
    st.header("Historical Assumption Landscape")
    st.markdown("Aggregated statistics from 6 NSCLC trials")
    
    # Get landscape
    landscape = analyze_assumption_landscape(MOCK_TRIALS)
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Response Rate Range</div>
            <div class="metric-value">{landscape['response_rate']['min']:.0%}–{landscape['response_rate']['max']:.0%}</div>
            <div class="metric-label">mean: {landscape['response_rate']['mean']:.0%}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Effect Size (OR)</div>
            <div class="metric-value">{landscape['effect_size_or']['min']:.2f}–{landscape['effect_size_or']['max']:.2f}</div>
            <div class="metric-label">mean: {landscape['effect_size_or']['mean']:.2f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Power</div>
            <div class="metric-value">{landscape['power']['min']:.0%}–{landscape['power']['max']:.0%}</div>
            <div class="metric-label">mean: {landscape['power']['mean']:.0%}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-box">
            <div class="metric-label">Sample Size</div>
            <div class="metric-value">{landscape['sample_size']['min']:.0f}–{landscape['sample_size']['max']:.0f}</div>
            <div class="metric-label">mean: {landscape['sample_size']['mean']:.0f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Show trials table
    st.subheader("Historical Trials")
    trials_df = pd.DataFrame(MOCK_TRIALS)
    st.dataframe(
        trials_df[['trial_id', 'indication', 'phase', 'assumed_response_rate', 'effect_size_or', 'power', 'sample_size']],
        use_container_width=True,
        hide_index=True
    )
    
    st.divider()
    
    # Common patterns
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Common Treatments")
        for t in landscape['common_treatments']:
            st.markdown(f"• {t}")
    
    with col2:
        st.subheader("Key Populations")
        for p in landscape['common_populations']:
            st.markdown(f"• {p}")

# ==================== PAGE: PARSE SAP ====================
elif page == "📄 Parse SAP":
    st.header("Parse SAP with AI")
    st.markdown("Paste unstructured SAP text → Get structured design record")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        sap_text = st.text_area(
            "Paste your SAP text here:",
            value=SAMPLE_SAP,
            height=200,
            placeholder="Paste unstructured SAP excerpt..."
        )
    
    with col2:
        st.markdown("### Sample SAP")
        st.markdown("""
        The text area on the left contains a sample SAP. Click **Parse SAP** to see it converted to structured JSON.
        """)
    
    if st.button("🧠 Parse SAP with LLM", key="parse_button"):
        with st.spinner("Parsing with Claude..."):
            parsed = parse_sap_with_llm(sap_text)
        
        st.success("✓ SAP parsed successfully!")
        
        st.subheader("Parsed Design Record")
        st.json(parsed)
        
        # Download button
        st.download_button(
            label="📥 Download as JSON",
            data=json.dumps(parsed, indent=2),
            file_name=f"parsed_sap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

# ==================== PAGE: DESIGN SOLVER ====================
elif page == "🎨 Design Solver":
    st.header("Create Your Trial Design")
    st.markdown("Define assumptions → Get SOLARA input with rationale")
    
    # Get landscape for reference
    landscape = analyze_assumption_landscape(MOCK_TRIALS)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Your Design")
        
        trial_id = st.text_input("Trial ID", value="MY-TRIAL-2024")
        
        response_rate = st.slider(
            "Assumed Response Rate (%)",
            min_value=0,
            max_value=100,
            value=42,
            step=1
        ) / 100
        
        control_rate = st.slider(
            "Control Response Rate (%)",
            min_value=0,
            max_value=100,
            value=25,
            step=1
        ) / 100
        
        effect_size = st.slider(
            "Effect Size (Odds Ratio)",
            min_value=0.5,
            max_value=3.0,
            value=1.65,
            step=0.05
        )
        
        power = st.slider(
            "Power (%)",
            min_value=50,
            max_value=99,
            value=90,
            step=1
        ) / 100
    
    with col2:
        st.subheader("Historical Reference")
        st.info(f"""
        **Response Rate:** {landscape['response_rate']['min']:.0%}–{landscape['response_rate']['max']:.0%} (mean {landscape['response_rate']['mean']:.0%})
        
        **Effect Size:** {landscape['effect_size_or']['min']:.2f}–{landscape['effect_size_or']['max']:.2f} (mean {landscape['effect_size_or']['mean']:.2f})
        
        **Power:** {landscape['power']['min']:.0%}–{landscape['power']['max']:.0%} (mean {landscape['power']['mean']:.0%})
        """)
    
    if st.button("🚀 Generate SOLARA Input", key="generate_button"):
        design = {
            "trial_id": trial_id,
            "assumed_response_rate": response_rate,
            "control_response_rate": control_rate,
            "effect_size_or": effect_size,
            "power": power
        }
        
        with st.spinner("Generating SOLARA input..."):
            solara_input = generate_solara_input(design, landscape)
        
        st.success("✓ SOLARA input generated!")
        
        st.subheader("📋 Design Parameters")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Response Rate", f"{response_rate:.0%}")
        col2.metric("Effect Size (OR)", f"{effect_size:.2f}")
        col3.metric("Power", f"{power:.0%}")
        col4.metric("Control Rate", f"{control_rate:.0%}")
        
        st.subheader("💭 Rationale (Why these assumptions?)")
        for rationale in solara_input['rationale_for_solara']:
            is_warning = "⚠" in rationale
            st.markdown(
                f"""<div class="{'rationale-warning' if is_warning else 'rationale-good'}">{rationale}</div>""",
                unsafe_allow_html=True
            )
        
        st.subheader("🔍 Key Insights")
        for insight in solara_input['key_insights']:
            st.markdown(f"• {insight}")
        
        st.divider()
        
        st.subheader("📤 Export for SOLARA")
        st.json(solara_input)
        
        st.download_button(
            label="📥 Download SOLARA Input",
            data=json.dumps(solara_input, indent=2),
            file_name=f"solara_input_{trial_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

# ==================== PAGE: COMPARE DESIGNS ====================
elif page == "📈 Compare Designs":
    st.header("Compare Multiple Designs")
    st.markdown("Evaluate different design strategies")
    
    landscape = analyze_assumption_landscape(MOCK_TRIALS)
    
    st.subheader("Design Strategies")
    
    col1, col2, col3 = st.columns(3)
    
    designs = {}
    
    with col1:
        st.markdown("### Conservative")
        designs['conservative'] = {
            "trial_id": "CONSERVATIVE",
            "assumed_response_rate": st.slider("RR %", 30, 50, 38, key="cons_rr") / 100,
            "control_response_rate": st.slider("Control %", 15, 30, 22, key="cons_ctrl") / 100,
            "effect_size_or": st.slider("OR", 1.0, 2.5, 1.5, 0.05, key="cons_or"),
            "power": st.slider("Power %", 80, 95, 90, key="cons_pw") / 100
        }
    
    with col2:
        st.markdown("### Balanced")
        designs['balanced'] = {
            "trial_id": "BALANCED",
            "assumed_response_rate": st.slider("RR %", 30, 50, 42, key="bal_rr") / 100,
            "control_response_rate": st.slider("Control %", 15, 30, 25, key="bal_ctrl") / 100,
            "effect_size_or": st.slider("OR", 1.0, 2.5, 1.65, 0.05, key="bal_or"),
            "power": st.slider("Power %", 80, 95, 90, key="bal_pw") / 100
        }
    
    with col3:
        st.markdown("### Optimistic")
        designs['optimistic'] = {
            "trial_id": "OPTIMISTIC",
            "assumed_response_rate": st.slider("RR %", 30, 50, 46, key="opt_rr") / 100,
            "control_response_rate": st.slider("Control %", 15, 30, 28, key="opt_ctrl") / 100,
            "effect_size_or": st.slider("OR", 1.0, 2.5, 1.8, 0.05, key="opt_or"),
            "power": st.slider("Power %", 80, 95, 88, key="opt_pw") / 100
        }
    
    if st.button("📊 Compare Designs"):
        st.subheader("Comparison Results")
        
        rr_range = landscape['response_rate']
        or_range = landscape['effect_size_or']
        pw_range = landscape['power']
        
        comparison_data = []
        
        for name, design in designs.items():
            rr = design['assumed_response_rate']
            orr = design['effect_size_or']
            pw = design['power']
            
            rr_ok = rr_range['min'] <= rr <= rr_range['max']
            or_ok = or_range['min'] <= orr <= or_range['max']
            pw_ok = pw >= (pw_range['mean'] - 0.03)
            
            risk_score = (rr_ok + or_ok + pw_ok) / 3
            risk_level = "🟢 LOW" if risk_score >= 0.8 else ("🟡 MEDIUM" if risk_score >= 0.5 else "🔴 HIGH")
            
            comparison_data.append({
                "Design": name.title(),
                "Response Rate": f"{rr:.0%}",
                "Effect Size": f"{orr:.2f}",
                "Power": f"{pw:.0%}",
                "Risk Level": risk_level,
                "Score": f"{risk_score:.0%}"
            })
        
        df = pd.DataFrame(comparison_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.divider()
        
        st.subheader("Detailed Analysis")
        for name, design in designs.items():
            solara_input = generate_solara_input(design, landscape)
            
            with st.expander(f"📋 {design['trial_id']}"):
                for rationale in solara_input['rationale_for_solara']:
                    st.markdown(f"• {rationale}")

# ==================== PAGE: ABOUT ====================
elif page == "ℹ️ About":
    st.header("About SOLARA Demo")
    
    st.markdown("""
    ### 🔬 What is This?
    
    A demonstration of **AI-derived trial design intelligence** that helps you:
    - Parse unstructured trial documents with Claude LLM
    - Analyze historical trials to understand typical design assumptions
    - Ground your trial design in empirical evidence
    - Generate SOLARA input with comparative rationale
    
    ### 📊 Historical Data
    
    The demo includes 6 realistic NSCLC trials:
    - KEYNOTE-024, KEYNOTE-407, ATTRACT-2
    - CheckMate-057, JIPANG-2, MYSTIC
    
    These are used to create the **assumption landscape** for comparison.
    
    ### 🚀 How It Works
    
    1. **Parse** - LLM extracts structured data from unstructured SAPs
    2. **Analyze** - Aggregates historical trials into assumption ranges
    3. **Compare** - Checks your design against historical precedent
    4. **Generate** - Creates SOLARA input with evidence-based rationale
    
    ### 📚 Documentation
    
    - [GitHub Repository](https://github.com/yourusername/solara-demo)
    - [Technical README](https://github.com/yourusername/solara-demo#readme)
    - [API Documentation](https://github.com/yourusername/solara-demo/blob/main/README.md)
    
    ### 🔧 Technology
    
    - **Framework:** Streamlit
    - **LLM:** Anthropic Claude
    - **Backend:** Python
    - **Deployment:** Streamlit Cloud
    
    ### 📝 Version
    
    SOLARA Demo v1.0 | Built with ❤️ for clinical trial design
    """)
    
    st.divider()
    
    st.markdown("""
    **Questions?** Create an issue on GitHub or contact the development team.
    """)

# ==================== FOOTER ====================
st.divider()
st.markdown("""
<div style="text-align: center; opacity: 0.6;">
    
**SOLARA Demo v1.0** | AI-Powered Trial Design Intelligence | [GitHub](https://github.com) | [Docs](https://github.com)

</div>
""", unsafe_allow_html=True)
