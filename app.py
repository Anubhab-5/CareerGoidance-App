import streamlit as st
import google.generativeai as genai
import re
import os
import time
import json
from io import BytesIO
from dotenv import load_dotenv
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Load environment variables
load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

# Environment Validation
if not API_KEY:
    st.error("❌ Missing Google API Key - Check .env file")
    st.stop()

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize Session States
required_states = {
    'show_main': False,
    'history': [],
    'api_errors': 0,
    'last_request': None,
    'error': False
}

for key, value in required_states.items():
    if key not in st.session_state:
        st.session_state[key] = value

def clean_input(text):
    """Sanitize user input while preserving spaces"""
    return re.sub(r'[^\w\s@.,-]', '', text).strip() if text else ""

def validate_inputs(**kwargs):
    """Comprehensive input validation"""
    errors = []
    
    for field, value in kwargs.items():
        if len(value) < 3:
            errors.append(f"{field.replace('_', ' ').title()} too short (min 3 chars)")
        if len(value) > 500:
            errors.append(f"{field.replace('_', ' ').title()} exceeds 500 chars")
            
    if re.search(r'[^\w\s@.,-]', kwargs.get('user_name', '')):
        errors.append("Invalid characters in name")
        
    return errors

def get_career_advice(interests, skills, education, goals):
    """Get AI-generated career advice with comprehensive error handling"""
    prompt = f"""
You are an expert career counselor mentoring a B.Tech or other students in India. Provide highly personalized, realistic, and actionable career advice based on:
- Interests: {interests}
- Skills: {skills}
- Education: {education}
- Career Goals: {goals}

**Requirements**:
- Suggest 4 best career paths relevant to the user’s profile, each including:
  1. **Job Title and Description**: Describe the role and its impact in India’s job market.
  2. **Required Skills**: List technical and soft skills, with tools or certifications.
  3. **Skill Gaps**: Compare user's current skills with required skills for each suggested career path, highlighting key areas for improvement.
  4. **Steps to Achieve**: Provide a 3-5 step roadmap tailored to a B.Tech and other student in india (e.g., projects, internships, courses).
  5. **Market Insights**: Include average salary (INR), demand, and remote work options.
  6. **Challenges and Solutions**: Address obstacles (e.g., competition) with practical solutions.
- Provide general advice on:
  - Building a resume (e.g., GitHub, LinkedIn).
  - Networking (e.g., meetups, online platforms).
  - Skill development (e.g., free/paid resources like Coursera, YouTube, Internshala).
  - Interview tips for Indian companies.
- Use a motivational tone to inspire confidence.
- Always Format with clear headings (##), bullet(**) and sub bullet points for readability.
"""
    try:
        response = model.generate_content(
            prompt,
            safety_settings={
                'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
                'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE'
            },
            generation_config={'temperature': 0.7}
        )
        
        if not response.text:
            raise ValueError("Empty response from AI model")
            
        return response.text

    except genai.types.GenerativeServiceError as e:
        st.session_state.api_errors += 1
        return f"🚨 API Error: Service unavailable. Please try again later. Details: {str(e)}"
    except Exception as e:
        error_type = type(e).__name__
        st.error(f"⚠️ Critical System Error: {error_type} - Contact support")
        st.session_state.error = True
        raise

def generate_pdf(content, title):
    """Generate PDF document from text content"""
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Add title
        story.append(Paragraph(f"<b>{title}</b>", styles['Title']))
        story.append(Spacer(1, 12))
        
        # Process content
        for line in content.split('\n'):
            if line.startswith('#'):
                style = styles['Heading2']
            else:
                style = styles['BodyText']
            story.append(Paragraph(line, style))
            story.append(Spacer(1, 3))
            
        doc.build(story)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"PDF generation failed: {str(e)}")
        return None

def export_json(data):
    """Export data as JSON"""
    return json.dumps(data, indent=2, ensure_ascii=False)

def export_text(content):
    """Export as formatted text file"""
    return content.encode('utf-8')

# Modern Glassmorphism UI Configuration
st.set_page_config(page_title="Career Guidance", page_icon="💼", layout="centered")
st.markdown("""
    <style>
    :root {
        --bg: #141414;
        --surface: rgba(33, 38, 45, 0.8);
        --primary: #58a6ff;
        --text: #ffffff;
        --border: rgba(240,246,252,0.1);
    }

    .stApp {
        background: var(--bg);
        color: var(--text);
        font-family: 'Segoe UI', system-ui;
    }

    .glass-card {
        background: var(--surface);
        backdrop-filter: blur(10px);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    }
    .glass-card:hover {
            box-shadow: 0 12px 48px rgba(0,0,0,1);
    }

    .stButton>button {
        background: var(--primary) !important;
        color: var(--bg) !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: 600 !important;
        transition: transform 0.2s ease;
    }

    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 12px 48px rgba(0,0,0,1);
    }

    .stTextInput>div>div>input {
        background: rgba(33, 38, 45, 0.6) !important;
        color: var(--text) !important;
        border: 1px solid var(--border) !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
    }
    .stTextInput>div>div>input:hover {
            border: 2px solid var(--primary) !important;
    }

    .history-item {
        background: rgba(33, 38, 45, 0.6);
        border-left: 3px solid var(--primary);
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Welcome Page
if not st.session_state.show_main:
    st.markdown("""
        <div style="text-align: center; padding: 2rem 0.5rem 0.5rem;">
            <h1 style="font-size: 3rem; color: #58a6ff; margin-bottom: 1rem;">
                🚀Welcome to Career Guidance📖
            </h1>
            <p style="color: #8b949e; margin-bottom: 1rem;">
                AI-powered career guidance for all
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    _, col, _ = st.columns([1,2,1])
    with col:
        if st.button("Get Started", key="start_btn"):
            st.session_state.show_main = True
            st.rerun()
    
    st.markdown("---")
    st.markdown("""
        <div style="text-align: center; color: #484f58; padding: 1.5rem 0;">
            <small>Made with ❤️ by Team Rush Adrenalin</small>
        </div>
    """, unsafe_allow_html=True)
    st.stop()

# Main Application
st.markdown("""
    <div style="font-size: 3.5rem; margin-bottom: 1rem; color: #58a6ff;">
        <b>Career Guider📖</b>
    </div>
    <p>Good career needs good guidance</p>
""", unsafe_allow_html=True)

# Profile Form
with st.form("profile_form"):
    with st.container():
        st.markdown("### Your Profile")
        cols = st.columns(2)
        with cols[0]:
            user_name = st.text_input("Full Name", placeholder="John Doe")
            education = st.text_input("Education", placeholder="B.Tech CSE")
        with cols[1]:
            skills = st.text_input("Skills", placeholder="Python, Communication")
            goals = st.text_input("Goals", placeholder="AI Engineer")
        interests = st.text_input("Interests", placeholder="Machine Learning")
        
        submitted = st.form_submit_button("Generate Career Plan →")

# Form Handling
if submitted:
    if st.session_state.api_errors > 3:
        st.error("🚧 Too many errors - Please try again after 15 minutes")
        st.stop()

    if st.session_state.last_request and (datetime.now() - st.session_state.last_request).seconds < 5:
        st.warning("⏳ Please wait 5 seconds between requests")
        st.stop()

    if not all([user_name, interests, skills, education, goals]):
        st.error("Please complete all fields")
    else:
        cleaned = {k: clean_input(v) for k,v in locals().items() 
                 if k in ['user_name', 'interests', 'skills', 'education', 'goals']}
        
        validation_errors = validate_inputs(**cleaned)
        if validation_errors:
            for error in validation_errors:
                st.error(error)
        else:
            with st.spinner("Analyzing your profile..."):
                advice = get_career_advice(
                    cleaned['interests'],
                    cleaned['skills'],
                    cleaned['education'],
                    cleaned['goals']
                )
            
            st.session_state.history.append({
                "name": cleaned['user_name'],
                "timestamp": datetime.now().strftime("%d %b %Y %H:%M"),
                "inputs": cleaned,
                "advice": advice
            })
            st.session_state.last_request = datetime.now()

# Current Plan Display with Export
if st.session_state.history:
    latest = st.session_state.history[-1]
    with st.container():
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"""
                <div class="glass-card">
                    <div style="font-size: 1.2rem; margin-bottom: 1rem;">
                        {latest['name']}'s Career Plan
                    </div>
                    <div style="color: #ffffff; line-height: 1.6;">
                        {latest['advice']}
                    </div>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.download_button(
                label="📄 PDF",
                data=generate_pdf(latest['advice'], f"Career Plan - {latest['name']}"),
                file_name=f"career_plan_{latest['timestamp'].replace(' ', '_')}.pdf",
                mime="application/pdf",
                key="pdf_export"
            )
            st.download_button(
                label="📝 Text",
                data=export_text(latest['advice']),
                file_name=f"career_plan_{latest['timestamp'].replace(' ', '_')}.txt",
                mime="text/plain",
                key="text_export"
            )

# History Section with Export
if len(st.session_state.history) > 0:
    st.markdown("### History")
    
    # Bulk Export in Sidebar
    with st.sidebar:
        st.markdown("### 📤 Bulk Export")
        export_format = st.selectbox("Format", ["JSON", "Text", "PDF"])
        if st.button(f"Export All History as {export_format}"):
            if export_format == "JSON":
                data = export_json(st.session_state.history)
                st.download_button(
                    label="Download JSON",
                    data=data,
                    file_name="career_history.json",
                    mime="application/json"
                )
            elif export_format == "PDF":
                combined_content = "\n\n".join(
                    [f"{item['name']} ({item['timestamp']})\n\n{item['advice']}" 
                    for item in st.session_state.history]
                )
                pdf_file = generate_pdf(combined_content, "Full Career History")
                if pdf_file:
                    st.download_button(
                        label="Download PDF",
                        data=pdf_file,
                        file_name="full_career_history.pdf",
                        mime="application/pdf"
                    )
            else:  # Text format
                text_content = "\n\n".join(
                    [f"{item['name']} ({item['timestamp']})\n\n{item['advice']}" 
                    for item in st.session_state.history]
                )
                st.download_button(
                    label="Download Text",
                    data=export_text(text_content),
                    file_name="full_career_history.txt",
                    mime="text/plain"
                )

    # Individual History Items
    for entry in reversed(st.session_state.history):
        with st.expander(f"{entry['name']} - {entry['timestamp']}"):
            col_left, col_right = st.columns([4, 1])
            with col_left:
                st.markdown(f"""
                    <div class="history-item">
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem;">
                            <div>
                                <p><strong>Education:</strong> {entry['inputs']['education']}</p>
                                <p><strong>Interests:</strong> {entry['inputs']['interests']}</p>
                            </div>
                            <div>
                                <p><strong>Skills:</strong> {entry['inputs']['skills']}</p>
                                <p><strong>Goals:</strong> {entry['inputs']['goals']}</p>
                            </div>
                        </div>
                        <div style="margin-top: 1rem; color: #8b949e;">
                            {entry['advice']}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            with col_right:
                st.download_button(
                    label="📄 PDF",
                    data=generate_pdf(entry['advice'], f"Career Plan - {entry['name']}"),
                    file_name=f"career_plan_{entry['timestamp'].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    key=f"pdf_{entry['timestamp']}"
                )
                st.download_button(
                    label="📝 Text",
                    data=export_text(entry['advice']),
                    file_name=f"career_plan_{entry['timestamp'].replace(' ', '_')}.txt",
                    mime="text/plain",
                    key=f"text_{entry['timestamp']}"
                )
                st.download_button(
                    label="📦 JSON",
                    data=export_json(entry),
                    file_name=f"career_plan_{entry['timestamp'].replace(' ', '_')}.json",
                    mime="application/json",
                    key=f"json_{entry['timestamp']}"
                )

# Error Boundary Component
if st.session_state.get('error'):
    st.markdown("""
        <div class="glass-card" style="border: 2px solid #ff4b4b; background: rgba(255,75,75,0.1);">
            <h3>⚠️ System Error</h3>
            <p>Our team has been notified. Please try:</p>
            <ul>
                <li>Refresh the page</li>
                <li>Check your internet connection</li>
                <li>Simplify your inputs</li>
            </ul>
            <small>Error Code: 500-{int(time.time())}</small>
        </div>
    """, unsafe_allow_html=True)
    st.session_state.error = False

# Sidebar Components
with st.sidebar:
    st.markdown("### Quick Tips")
    st.markdown("""
        <div class="glass-card" style="padding: 1rem;">
            ▸ List specific technical skills  
            ▸ Mention relevant projects  
            ▸ Include certifications  
            ▸ Update regularly
        </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.history:
        profile = st.session_state.history[-1]
        st.markdown("### 🙋Your Profile")
        st.markdown(f"""
            <div class="glass-card" style="padding: 1rem;">
                Name: {profile['name']}<br>
                Education: {profile['inputs']['education']}<br>
                Skills: {profile['inputs']['skills']}<br>
                Goals: {profile['inputs']['goals']}
            </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #484f58; padding: 1.5rem 0;">
        <small>Made with ❤️ by Team Rush Adrenalin</small>
    </div>
""", unsafe_allow_html=True)