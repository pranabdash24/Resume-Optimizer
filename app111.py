import streamlit as st
import tempfile
import google.generativeai as genai
import plotly.graph_objects as go
import pdfplumber
from streamlit.components.v1 import html

# Configure Gemini
GOOGLE_API_KEY = st.secrets["general"]["API_KEY"]
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro-latest')

# Custom CSS styling
st.markdown("""
<style>
    /* Theme-aware variables */
    :root {
        --primary: #4CAF50;
        --bg-color: var(--background-color);
        --text-color: var(--primary-text-color);
        --secondary-bg: var(--secondary-background-color);
        --border-color: var(--border-color);
    }

    .main {
        max-width: 800px;
        padding: 2rem;
        color: var(--text-color);
    }
    
    .header {
        padding: 2rem;
        border-radius: 15px;
        background: var(--secondary-bg);
        margin-bottom: 2rem;
        border: 1px solid var(--border-color);
    }

     /* Button styling */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        background:rgba(45, 175, 132, 0.62)!important;
        color: white!important;
        padding: 12px!important;
        transition: all 0.3s!important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(76,175,80,0.3);
    }
    .metric-box {
        padding: 1.5rem;
        border-radius: 15px;
        background: var(--secondary-bg);
        text-align: center;
        margin: 1rem 0;
        border: 1px solid var(--border-color);
    }
    
    .suggestion-box {
        padding: 1.5rem;
        background: var(--secondary-bg);
        border-radius: 15px;
        margin: 1.5rem 0;
        border: 1px solid var(--border-color);
    }
    
    .stPlotlyChart {
        border-radius: 15px;
        background: var(--secondary-bg)!important;
        padding: 15px;
        margin: 2rem 0;
        border: 1px solid var(--border-color);
    }

    /* Dark mode text contrast */
    pre {
        color: var(--text-color)!important;
    }
</style>
""", unsafe_allow_html=True)

def extract_keywords(text, source_type):
    """Extract keywords using Gemini"""
    emoji = "📄" if source_type == "resume" else "📑"
    prompt = f"""
    {emoji} Analyze this {source_type} and extract key technical skills, tools, certifications, 
    and domain-specific terms. Return comma-separated lowercase keywords:
    
    {text}
    """
    response = model.generate_content(prompt)
    return [kw.strip() for kw in response.text.lower().split(",") if kw.strip()]

def calculate_match(resume_kws, jd_kws):
    """Calculate matching score and keywords"""
    matched = set(resume_kws) & set(jd_kws)
    missing = set(jd_kws) - set(resume_kws)
    score = (len(matched)/len(jd_kws))*100 if jd_kws else 0
    return score, matched, missing

def create_score_gauge(score):
    """Create compact theme-aware gauge"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={
            'suffix': "%",
            'font': {'size': 30, 'color': 'var(--text-color)'},
            'valueformat': ".1f"
        },
        domain={'x': [0, 1], 'y': [0, 1]},
        title={
            'text': "🏆 ATS Compatibility Score",
            'font': {'size': 18, 'color': 'var(--text-color)'}
        },
        gauge={
            'axis': {
                'range': [0, 100],
                'tickfont': {'size': 12, 'color': 'var(--text-color)'},
                'tickcolor': 'var(--text-color)'
            },
            'bar': {'color': "rgba(29, 70, 202, 0.68)"},
            'steps': [
                {'range': [0, 50], 'color': 'rgba(244, 67, 54, 0.9)'},
                {'range': [50, 75], 'color': 'rgba(255, 193, 7, 0.9)'},
                {'range': [75, 100], 'color': 'rgba(76, 175, 80, 0.9)'},
            ],
            'bgcolor': 'var(--bg-color)'
        }
    ))
    
    fig.update_layout(
        height=300,  # Reduced size
        margin=dict(t=60, b=20, l=20, r=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'family': "Arial"}
    )
    return fig

def enhance_resume_analysis(resume_text, missing_kws, jd):
    """Generate enhanced resume text"""
    prompt = f"""
    🔧 Improve this resume for the job description below. 
    Maintain original structure while naturally incorporating these keywords: {', '.join(missing_kws)}
    
    📝 Original Resume:
    {resume_text}
    
    📌 Job Description:
    {jd}
    
    Return ONLY the enhanced resume text with identical section headers.
    """
    response = model.generate_content(prompt)
    return response.text

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF"""
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join([page.extract_text() for page in pdf.pages])

# ... [keep all previous imports and configurations] ...

def main():
    st.markdown("<div class='header'><h1 style='margin:0;'>🚀 Resume Optimizer</h1><p style='margin:0; color:#6c757d;'>AI-Powered Resume Analysis & Optimization</p></div>", unsafe_allow_html=True)
    
    # File Upload Section
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            uploaded_file = st.file_uploader("📤 Upload PDF Resume", type=["pdf"])
        with col2:
            jd = st.text_area("📝 Paste Job Description", height=150)

    if uploaded_file and jd and st.button("✨ Analyze & Optimize"):
        with st.spinner("🔍 Analyzing resume..."):
            # Process PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(uploaded_file.getbuffer())
                resume_text = extract_text_from_pdf(tmp_pdf.name)
            
            # Keyword analysis
            resume_kws = extract_keywords(resume_text, "resume")
            jd_kws = extract_keywords(jd, "job description")
            score, matched, missing = calculate_match(resume_kws, jd_kws)
            
            # Results Display
            st.markdown("---")
            
            # Gauge Chart
            with st.container():
                st.plotly_chart(create_score_gauge(score), use_container_width=True)
            
            # Stats Below Gauge
            with st.container():
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("<div class='metric-box'>", unsafe_allow_html=True)
                    st.metric("✅ Matched Keywords", len(matched))
                    st.markdown("</div>", unsafe_allow_html=True)
                with col2:
                    st.markdown("<div class='metric-box'>", unsafe_allow_html=True)
                    st.metric("❌ Missing Keywords", len(missing))
                    st.markdown("</div>", unsafe_allow_html=True)
            
            # Keyword Breakdown
            st.markdown("---")
            with st.expander("🔑 Detailed Keyword Analysis", expanded=True):
                tab1, tab2 = st.tabs(["🎯 Matched Keywords", "⚠️ Missing Keywords"])
                with tab1:
                    st.write(", ".join(matched) if matched else "No matches found")
                with tab2:
                    st.write(", ".join(missing) if missing else "Perfect match!")

            # Enhanced Resume
            st.markdown("---")
            enhanced_text = enhance_resume_analysis(resume_text, missing, jd)
            st.subheader("💎 Enhanced Resume Preview")
            
            with st.container():
                st.markdown(f"""
                <div class='suggestion-box'>
                    <pre style='font-family: Arial; line-height: 1.6;'>{enhanced_text}</pre>
                </div>
                """, unsafe_allow_html=True)
                
                # Copy Functionality
                html(f"""
                <script>
                function copyText() {{
                    navigator.clipboard.writeText(`{enhanced_text}`);
                    alert('Resume copied to clipboard!');
                }}
                </script>
                <button onclick="copyText()" style='
                    background: #4CAF50;
                    color: white;
                    padding: 12px 24px;
                    border: none;
                    border-radius: 8px;
                    cursor: pointer;
                    margin-top: 1rem;
                    font-size: 16px;
                    transition: all 0.3s;
                '>📋 Copy Enhanced Resume</button>
                """, height=60)

if __name__ == "__main__":
    main()