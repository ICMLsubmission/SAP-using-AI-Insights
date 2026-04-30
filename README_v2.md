# SAP Design by AI Insights

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://icmlsubmission-sap-design.streamlit.app)

**Transform unstructured trial documents into structured intelligence and derive assumption landscapes through AI-powered analysis.**

## 🎯 Three-Step Workflow

```
STEP 1: Upload SAPs (PDF/Word documents)
          ↓
STEP 2: AI Parses Each → Structured Intelligence Table
          ↓
STEP 3: Analyze Multiple → Assumption Landscape (Final Output)
```

## ✨ Features

### Step 1: Document Upload
- 📄 Upload PDF or Word documents containing Statistical Analysis Plans
- 🔄 Support for multiple documents at once
- 📦 Simple drag-and-drop interface

### Step 2: AI-Powered Parsing
- 🧠 Claude extracts ~14 key fields from each SAP:
  - Trial ID, Indication, Phase
  - Response rates, Effect sizes, Power
  - Sample sizes, Analysis methods
  - Study population, Treatment info
- 📊 Creates structured intelligence table
- ✓ Real-time parsing progress display

### Step 3: Assumption Landscape Analysis
- 📈 Aggregates all parsed trials
- 📊 Computes statistics: min, max, mean, median
- 📋 Shows typical ranges for all metrics
- 📥 Export as JSON or CSV

## 🚀 Quick Start

### Local Python
```bash
# Install dependencies
pip install -r requirements_v2.txt

# Run the app
streamlit run streamlit_app_v2.py

# Opens at http://localhost:8501
```

### Live Web App
Click the Streamlit badge above → **https://icmlsubmission-sap-design.streamlit.app**

No Python needed. Just upload and analyze!

## 📋 Extracted Fields (Schema)

Each parsed SAP includes:

| Field | Description | Example |
|-------|-------------|---------|
| trial_id | Trial identifier | KEYNOTE-024 |
| indication | Disease area | NSCLC |
| phase | Trial phase | III |
| primary_endpoint | Primary endpoint | PFS, OS, ORR |
| assumed_response_rate | Expected response rate | 0.45 (45%) |
| control_response_rate | Control arm RR | 0.28 (28%) |
| effect_size_or | Odds ratio | 1.8 |
| power | Statistical power | 0.90 (90%) |
| alpha | Significance level | 0.05 |
| sample_size | Total enrollment | 305 |
| primary_analysis | Analysis method | Cox regression |
| study_population | Eligibility criteria | PD-L1 ≥50% |
| treatment | Intervention | Pembrolizumab |

## 📊 Assumption Landscape Output

After analyzing multiple SAPs, get summary statistics:

```
Response Rate Range:    35%–45% (mean 41%)
Control Rate Range:     20%–28% (mean 25%)
Effect Size (OR):       1.3–1.8 (mean 1.58)
Power:                  82%–90% (mean 88%)
Sample Size:            198–582 (mean 327)
```

## 📁 Files

### Core Application
- **`sap_design_core.py`** - Core logic (PDF extraction, LLM parsing, landscape analysis)
- **`streamlit_app_v2.py`** - Web interface
- **`requirements_v2.txt`** - Python dependencies

### Demo Documents
- **`SAP_KEYNOTE-024.pdf`** / **`.docx`** - KEYNOTE-024 trial SAP
- **`SAP_ATTRACT-2.pdf`** / **`.docx`** - ATTRACT-2 trial SAP
- **`SAP_CheckMate-057.pdf`** / **`.docx`** - CheckMate-057 trial SAP

## 🔧 Installation

### Prerequisites
- Python 3.8+
- (Optional) Anthropic API key for real LLM parsing

### Setup
```bash
# Clone repository
git clone https://github.com/yourusername/ICMLsubmission.git
cd ICMLsubmission

# Install dependencies
pip install -r requirements_v2.txt

# (Optional) Set API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Run
streamlit run streamlit_app_v2.py
```

## 🌐 Deployment to Streamlit Cloud

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add SAP Design by AI Insights"
   git push origin main
   ```

2. **Deploy**
   - Go to https://streamlit.io/cloud
   - Click "New app"
   - Select your GitHub repo
   - Select `streamlit_app_v2.py`
   - Click "Deploy"

**Your live app:** https://yourusername-sap-design.streamlit.app

## 💡 Example Workflow

1. **Upload** 3 NSCLC trial SAPs
2. **Parse** - AI extracts fields from each document
3. **View** - Structured intelligence table with all trials
4. **Analyze** - Generate assumption landscape
5. **Export** - Download table and landscape as JSON/CSV

## 🔐 Security & Privacy

- ✅ Documents processed locally (with Anthropic API)
- ✅ No data stored or logged
- ✅ API keys encrypted (Streamlit Secrets)
- ✅ All analysis on-demand

## 🚀 Tech Stack

- **Framework:** Streamlit
- **LLM:** Anthropic Claude
- **Document Processing:** PyPDF2, python-docx
- **Data:** Pandas, JSON
- **Deployment:** Streamlit Cloud

## 📞 Support

- **Questions?** Open a GitHub issue
- **Found a bug?** Report with details
- **Want to contribute?** Submit a pull request

## 📄 License

[Your License Here]

---

**SAP Design by AI Insights v1.0** | Transform trial documents into intelligence | [GitHub](https://github.com/yourusername/ICMLsubmission)
