import streamlit as st
import requests
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8080"

# Page config
st.set_page_config(
    page_title="VoiceScreen AI - Interview System",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS - Modern Professional Design
st.markdown("""
    <style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global Styles */
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        padding: 1.5rem 2rem;
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Header Styles */
    h1, h2, h3 {
        color: #1a1a1a;
        font-weight: 700;
    }
    
    /* Button Styles */
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.75rem 1.5rem;
        font-size: 1rem;
        font-weight: 600;
        border-radius: 12px;
        border: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(102, 126, 234, 0.25);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(102, 126, 234, 0.35);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Form Submit Button - Primary */
    div[data-testid="stForm"] button[type="submit"] {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        box-shadow: 0 4px 6px rgba(17, 153, 142, 0.25);
    }
    
    div[data-testid="stForm"] button[type="submit"]:hover {
        background: linear-gradient(135deg, #38ef7d 0%, #11998e 100%);
        box-shadow: 0 6px 12px rgba(17, 153, 142, 0.35);
    }
    
    /* Card Boxes */
    .success-box {
        padding: 1.25rem;
        border-radius: 12px;
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-left: 4px solid #28a745;
        color: #155724;
        margin: 1.5rem 0;
        box-shadow: 0 2px 8px rgba(40, 167, 69, 0.1);
    }
    
    .warning-box {
        padding: 1.25rem;
        border-radius: 12px;
        background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
        border-left: 4px solid #ffc107;
        color: #856404;
        margin: 1.5rem 0;
        box-shadow: 0 2px 8px rgba(255, 193, 7, 0.1);
        font-size: 1.05rem;
        line-height: 1.6;
    }
    
    .info-box {
        padding: 1.25rem;
        border-radius: 12px;
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border-left: 4px solid #17a2b8;
        color: #0c5460;
        margin: 1.5rem 0;
        box-shadow: 0 2px 8px rgba(23, 162, 184, 0.1);
    }
    
    /* Question Card */
    .question-card {
        background: white;
        padding: 2rem;
        border-radius: 16px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        border: 1px solid #e0e0e0;
        margin: 1.5rem 0;
    }
    
    /* Progress Bar */
    .progress-container {
        background: #f0f0f0;
        border-radius: 12px;
        height: 10px;
        margin: 1rem 0;
        overflow: hidden;
    }
    
    .progress-bar {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        height: 100%;
        transition: width 0.3s ease;
        border-radius: 12px;
    }
    
    /* Recommendation Badges */
    .recommendation-proceed {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1.5rem;
    }
    
    .recommendation-hold {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1.5rem;
    }
    
    .recommendation-reject {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1.5rem;
    }
    
    /* Text Area Styling */
    .stTextArea textarea {
        border-radius: 12px;
        border: 2px solid #e0e0e0;
        padding: 1rem;
        font-size: 1rem;
        transition: border-color 0.3s ease;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Metric Cards */
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #667eea;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'interview_id' not in st.session_state:
    st.session_state.interview_id = None
if 'status' not in st.session_state:
    st.session_state.status = 'NOT_STARTED'
if 'turn_no' not in st.session_state:
    st.session_state.turn_no = 0
if 'qa_history' not in st.session_state:
    st.session_state.qa_history = []
if 'final_report' not in st.session_state:
    st.session_state.final_report = None
if 'selected_job' not in st.session_state:
    st.session_state.selected_job = None

def create_interview(candidate_id, job_id):
    """Create a new interview"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/hr/interview/create",
            json={
                "candidateId": candidate_id,
                "jobId": job_id,
                "channel": "simulation",
                "consentRequired": True
            }
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Failed to connect to backend: {e}")
        return None

def get_disclosure(interview_id):
    """Get disclosure text"""
    try:
        response = requests.get(f"{API_BASE_URL}/hr/interview/{interview_id}/disclosure")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error fetching disclosure: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def submit_consent(interview_id, consent):
    """Submit consent"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/hr/interview/{interview_id}/consent",
            json={"consent": consent}
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def get_chat_history(interview_id):
    """Get full chat history"""
    try:
        response = requests.get(f"{API_BASE_URL}/hr/interview/{interview_id}/turns")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []

def get_next_question(interview_id):
    """Get next question"""
    try:
        response = requests.get(f"{API_BASE_URL}/hr/interview/{interview_id}/next-question")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def submit_answer(interview_id, turn_no, answer):
    """Submit answer"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/hr/interview/{interview_id}/answer",
            json={"turnNo": turn_no, "answer": answer}
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def finish_interview(interview_id):
    """Finish interview"""
    try:
        response = requests.post(f"{API_BASE_URL}/hr/interview/{interview_id}/finish")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

def get_report(interview_id):
    """Get full report"""
    try:
        response = requests.get(f"{API_BASE_URL}/hr/interview/{interview_id}/report")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# Main App
def main():
    # Header
    col1, col2 = st.columns([2, 1])
    with col1:
        st.title("🤖 VoiceScreen AI - Interview System")
        st.markdown("*Autonomous AI-Led Phone Interview Platform*")
        # Display job role prominently if interview started
        # if 'selected_job' in st.session_state and st.session_state.selected_job:
        #     st.markdown(f"### 💼 Position: **{st.session_state.selected_job}**")
    with col2:
        if st.session_state.interview_id:
            st.metric("Interview ID", st.session_state.interview_id)
    
    st.divider()
    
    # Sidebar
    with st.sidebar:
        st.header("Role")
        
        # Show job role in sidebar
        if 'selected_job' in st.session_state and st.session_state.selected_job:
            st.info(f"💼 **{st.session_state.selected_job}**")
            st.divider()
        
        status_color = {
            'NOT_STARTED': '🔴',
            'CREATED': '🟡',
            'DISCLOSURE_DONE': '🟡',
            'CONSENT_GRANTED': '🟢',
            'INTERVIEW_IN_PROGRESS': '🔵',
            'COMPLETED': '✅',
        }
        st.header("Interview Status")
        st.markdown(f"### {status_color.get(st.session_state.status, '⚪')} {st.session_state.status}")
        
        if st.session_state.turn_no > 0:
            st.metric("Questions Asked", st.session_state.turn_no)
        
        st.divider()
        
        if st.button("🔄 Reset Interview"):
            st.session_state.interview_id = None
            st.session_state.status = 'NOT_STARTED'
            st.session_state.turn_no = 0
            st.session_state.qa_history = []
            st.session_state.final_report = None
            st.rerun()
    
    # Main content
    if st.session_state.status == 'NOT_STARTED':
        show_start_screen()
    elif st.session_state.status == 'CREATED':
        show_disclosure()
    elif st.session_state.status == 'CONSENT_GRANTED' or st.session_state.status == 'INTERVIEW_IN_PROGRESS':
        show_interview()
    elif st.session_state.status == 'COMPLETED':
        show_results()

def show_start_screen():
    """Show interview start screen"""
    st.header("🎙️ Start New Interview")
    
    st.markdown("### Select Job Role")
    
    # Define available jobs with display names
    job_options = {
        "JOB-DA-FRESHER": "📊 Data Analyst - Fresher (0-1 years)",
        "JOB-DA-MID": "📊 Data Analyst - Mid-Level (2-4 years)",
        "JOB-DE-FRESHER": "🔧 Data Engineer - Junior (0-2 years)",
        "JOB-DE-SENIOR": "🔧 Data Engineer - Senior (5-8 years)",
        "JOB-DS-FRESHER": "🔬 Data Scientist - Junior (0-2 years)",
        "JOB-DS-SENIOR": "🔬 Data Scientist - Senior (5-8 years)",
        "JOB-ML-JUNIOR": "🤖 AI/ML Engineer - Junior (1-3 years)",
        "JOB-ML-SENIOR": "🤖 AI/ML Engineer - Senior (5-8 years)"
    }
    
    # Job role selection with better UX
    selected_job_display = st.selectbox(
        "Choose the position to interview for:",
        options=list(job_options.values()),
        help="Select the role and experience level"
    )
    
    # Get the job_id from the selected display name
    job_id = [k for k, v in job_options.items() if v == selected_job_display][0]
    
    # Show job details in an expander
    with st.expander("📋 View Job Details"):
        job_details = {
            "JOB-DA-FRESHER": {
                "skills": "SQL, Excel, Data Visualization",
                "focus": "Entry-level analytics, reporting, data cleaning"
            },
            "JOB-DA-MID": {
                "skills": "Advanced SQL, Python/R, Tableau/Power BI, Statistics",
                "focus": "Complex analytics, A/B testing, stakeholder presentations"
            },
            "JOB-DE-FRESHER": {
                "skills": "SQL, Python, ETL/ELT, Database fundamentals",
                "focus": "Pipeline development, data quality, basic automation"
            },
            "JOB-DE-SENIOR": {
                "skills": "Python, Spark, Kafka, Cloud (AWS/GCP), Airflow, SQL optimization",
                "focus": "Architecture, scalability, real-time processing, mentorship"
            },
            "JOB-DS-FRESHER": {
                "skills": "Python, Statistics, ML basics, SQL, Visualization",
                "focus": "Model building, EDA, A/B testing, presentations"
            },
            "JOB-DS-SENIOR": {
                "skills": "Advanced ML, Deep Learning, MLOps, Causal Inference, Python",
                "focus": "End-to-end ML, business impact, experimentation, leadership"
            },
            "JOB-ML-JUNIOR": {
                "skills": "Python, ML frameworks, Docker, REST APIs, CI/CD",
                "focus": "Model deployment, API development, monitoring"
            },
            "JOB-ML-SENIOR": {
                "skills": "PyTorch/TF, Kubernetes, ML infrastructure, LLMs, Distributed systems",
                "focus": "ML platform architecture, LLM integration, optimization, mentorship"
            }
        }
        
        details = job_details.get(job_id, {})
        st.markdown(f"**Required Skills:** {details.get('skills', 'N/A')}")
        st.markdown(f"**Focus Areas:** {details.get('focus', 'N/A')}")
    
    st.markdown("---")
    
    # Candidate ID input
    candidate_id = st.text_input(
        "👤 Candidate ID", 
        value="",  # No default value - user must type
        placeholder="Enter candidate ID (e.g., CAND-001)",
        help="Enter candidate identifier"
    )
    
    # Display selected job ID
    st.info(f"**Selected Job ID:** `{job_id}`")
    
    st.markdown("---")
    
    if st.button("🚀 Start Interview", type="primary", use_container_width=True):
        # Validate Candidate ID - strict format: CAND-XXX (3 digits)
        import re
        
        if not candidate_id or not candidate_id.strip():
            st.error("⚠️ Please enter a Candidate ID before starting the interview.")
        elif not re.match(r'^CAND-\d{3}$', candidate_id.strip()):
            st.error("⚠️ Please enter a valid Candidate ID in format: CAND-XXX (e.g., CAND-001, CAND-123)")
        else:
            with st.spinner("Creating interview session..."):
                result = create_interview(candidate_id.strip(), job_id)
                if result:
                    st.session_state.interview_id = result['interviewId']
                    st.session_state.status = 'CREATED'
                    st.session_state.selected_job = selected_job_display  # Store for display
                    st.success(f"✅ Interview created: {result['interviewId']}")
                    time.sleep(1)
                    st.rerun()

def show_disclosure():
    """Show disclosure and consent"""
    st.header("📜 Disclosure & Consent")
    
    # Cache disclosure in session state to prevent redundant loading
    if 'disclosure_text' not in st.session_state:
        with st.spinner("Loading disclosure..."):
            disclosure = get_disclosure(st.session_state.interview_id)
            if disclosure:
                st.session_state.disclosure_text = disclosure["disclosureText"]
            else:
                st.session_state.disclosure_text = None
    
    if st.session_state.disclosure_text:
        st.markdown(f'<div class="info-box">{st.session_state.disclosure_text}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ I Consent", type="primary"):
                result = submit_consent(st.session_state.interview_id, "yes")
                if result and result['consentStatus'] == 'GRANTED':
                    st.session_state.status = 'CONSENT_GRANTED'
                    st.success("Consent granted! Starting interview...")
                    time.sleep(1)
                    st.rerun()
        
        with col2:
            if st.button("❌ I Do Not Consent"):
                result = submit_consent(st.session_state.interview_id, "no")
                if result:
                    st.warning("Interview ended due to consent denial.")
                    st.session_state.status = 'NOT_STARTED'

def show_interview():
    """Show interview Q&A interface"""
    st.header("💬 Interview in Progress")
    
    # Get next question
    st.subheader("Current Question")
    
    # Initialize last_fetched_turn if not exists
    if 'last_fetched_turn' not in st.session_state:
        st.session_state.last_fetched_turn = 0
    
    # Only fetch question if we need a new one AND haven't already fetched this turn
    should_fetch_question = (
        'current_question' not in st.session_state or 
        st.session_state.get('show_next', False)
    ) and st.session_state.turn_no >= st.session_state.last_fetched_turn
    
    if should_fetch_question:
        with st.spinner("Generating question..."):
            question = get_next_question(st.session_state.interview_id)
            if question:
                st.session_state.current_question = question
                st.session_state.status = 'INTERVIEW_IN_PROGRESS'
                st.session_state.show_next = False
                st.session_state.last_fetched_turn = question.get('turnNo', st.session_state.turn_no + 1)
    
    if 'current_question' in st.session_state:
        q = st.session_state.current_question
        
        # NEW: Check if agent decided to terminate interview
        if q.get('final', False):
            st.markdown('<div class="success-box"><strong>Interview Completed</strong><br>The interview has been completed based on the AI agent\'s assessment.</div>', unsafe_allow_html=True)
            st.info(f"📋 Total questions asked: {q.get('totalQuestions', 'N/A')}")
            
            with st.status("Finalizing Interview & Generating Report...", expanded=True) as status:
                st.write("🔄 Analyzing and scoring responses in parallel...")
                finish_result = finish_interview(st.session_state.interview_id)
                
                if finish_result:
                    st.write("📊 Compiling insights and recommendations...")
                    st.session_state.final_report = finish_result
                    st.session_state.status = 'COMPLETED'
                    st.session_state.interview_complete = True
                    del st.session_state.current_question
                    
                    st.write("🚀 Synchronizing results...")
                    status.update(label="✅ All Done! Redirecting...", state="complete", expanded=False)
                    time.sleep(1)
                    st.rerun()
                else:
                    status.update(label="❌ Report generation failed", state="error")
            return
        
        # Display Progress Indicator
        progress_text = q.get('totalQuestions', 'In Progress')
        if '/' in str(progress_text):
            current_num = st.session_state.turn_no
            st.markdown(f"**Progress:** Question {current_num} {progress_text}")
            # Calculate progress percentage
            try:
                parts = str(progress_text).split('/')[1].split('-')
                max_q = int(parts[1]) if len(parts) > 1 else 15
                progress = min(100, (current_num / max_q) * 100)
                st.markdown(f'<div class="progress-container"><div class="progress-bar" style="width: {progress}%"></div></div>', unsafe_allow_html=True)
            except:
                pass
        
        # Auto-finish interview after wrapup question (Q10) - FALLBACK for non-agentic mode
        if q.get('questionType') == 'wrapup':
            # CHECK: Did agent respond to candidate's previous question?
            # Fetch history to find out
            history = get_chat_history(st.session_state.interview_id)
            if history:
                # Look for the last agent turn that isn't this wrapup question
                # Specifically, look for Turn 9 (candidate_questions) Agent Response
                prev_turn_no = q.get('turnNo', 10) - 1
                agent_responses = [
                    t for t in history 
                    if t['speaker'] == 'agent' 
                    and t.get('turn_no') == prev_turn_no
                    and "Do you have any questions" not in t.get('text', '')
                ]
                
                if agent_responses:
                    last_response = agent_responses[-1]['text']
                    st.markdown(f"""
                    <div style="background-color: #f0f7ff; border-left: 5px solid #0066cc; padding: 15px; margin-bottom: 20px; border-radius: 4px;">
                        <strong>🤖 Interviewer Response:</strong><br>
                        {last_response}
                    </div>
                    """, unsafe_allow_html=True)
            
            # UI FIX: Show as completion message, not a question
            st.markdown('<div class="success-box"><strong>🎉 Interview Complete!</strong></div>', unsafe_allow_html=True)
            st.info(f"💬 {q['question']}")  # Show wrap-up message, but not as a "question"
            # st.balloons()  # Removed: User requested no celebration animation
            
            with st.status("Completing Interview...", expanded=True) as status:
                st.write("🔄 Finalizing evaluations...")
                finish_result = finish_interview(st.session_state.interview_id)
                
                if finish_result:
                    st.write("✨ Generating final analysis...")
                    st.session_state.final_report = finish_result
                    st.session_state.status = 'COMPLETED'
                    st.session_state.interview_complete = True
                    del st.session_state.current_question
                    
                    status.update(label="✅ Success! Redirecting...", state="complete", expanded=False)
                    time.sleep(3)  # Give user time to read the response!
                    st.rerun()
                else:
                    status.update(label="❌ Error generating report", state="error")
            return  # Exit early, don't show answer input for wrapup
        
        # Special handling for candidate_questions (Q9) - allow "No questions" or actual questions
        if q.get('questionType') == 'candidate_questions':
            st.markdown(f'<div class="info-box"><strong>🎤 Your Turn - Question {q["turnNo"]}:</strong><br><br>{q["question"]}</div>', unsafe_allow_html=True)
            st.caption("💡 You can ask about the role, team, company culture, or say 'No questions' to proceed.")
        else:
            # Question type badge
            type_emoji = {
                'warmup': '👋',
                'behavioral': '🎯',
                'technical': '💻',
                'motivation': '🚀',
                'scenario': '🔍',
                'culture': '🤝'
            }
            emoji = type_emoji.get(q['questionType'], '❓')
            st.markdown(f'<div class="warning-box"><strong>{emoji} Question {q["turnNo"]} ({q["questionType"].title()}):</strong><br><br>{q["question"]}</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Answer Input Section
        st.markdown("### 💬 Your Answer")
        st.caption("Provide a detailed, structured response using the STAR method for behavioral questions.")
        
        # Use form to batch operations
        with st.form(key=f"answer_form_{q['turnNo']}", clear_on_submit=True):
            # Text-only mode (original)
            answer = st.text_area(
                "Type Your Answer:",
                height=150,
                placeholder="Type your answer here...",
                help="Provide a detailed, structured response",
                key=f"answer_input_{q['turnNo']}"
            )
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                submit_clicked = st.form_submit_button("📤 Submit Answer", type="primary", use_container_width=True)
            
            with col2:
                finish_clicked = st.form_submit_button("🏁 Finish Interview", use_container_width=True)
        
        # Handle submit answer
        if submit_clicked:
            if answer and answer.strip():  # Validate after click
                with st.spinner("Submitting answer..."):
                    result = submit_answer(st.session_state.interview_id, q["turnNo"], answer)
                    if result:
                        st.session_state.qa_history.append({
                            'question': q['question'],
                            'answer': answer,
                            'type': q['questionType']
                        })
                        st.session_state.turn_no = q["turnNo"]
                        st.session_state.show_next = True
                        del st.session_state.current_question
                        st.success("Answer submitted successfully!")
                        time.sleep(0.5)
                        st.rerun()
            else:
                st.warning("Please enter an answer before submitting.")
        
        # Handle finish interview
        if finish_clicked:
            with st.spinner("Generating report..."):
                report = finish_interview(st.session_state.interview_id)
                if report:
                    st.session_state.final_report = report
                    st.session_state.status = 'COMPLETED'
                    st.success("Interview completed!")
                    time.sleep(1)
                    st.rerun()

def show_results():
    """Show interview results"""
    st.header("📊 Interview Results")
    
    # Get report from session state or fetch from API
    if not st.session_state.final_report:
        with st.spinner("Loading interview results..."):
            st.session_state.final_report = get_report(st.session_state.interview_id)
    
    if st.session_state.final_report:
        report = st.session_state.final_report
        
        #  Recommendation
        rec = report.get('recommendation', 'UNKNOWN')
        rec_class = f"recommendation-{rec.lower()}"
        st.markdown(f'<div class="{rec_class}">🎯 RECOMMENDATION: {rec}</div>', unsafe_allow_html=True)
        
        st.divider()
        
        # Scores
        col1, col2, col3, col4 = st.columns(4)
        
        scores = report.get('scores', {})
        with col1:
            st.metric("📈 Overall Score", f"{report.get('overallScore', 0)}/100")
        with col2:
            st.metric("💻 Technical", f"{scores.get('technical', 0)}/100")
        with col3:
            st.metric("💬 Communication", f"{scores.get('communication', 0)}/100")
        with col4:
            st.metric("🤝 Culture Fit", f"{scores.get('culture', 0)}/100")
        
        st.divider()
        
        # Highlights & Concerns
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("✨ Highlights")
            highlights = report.get('summary', {}).get('highlights', report.get('highlights', []))
            if highlights:
                for highlight in highlights:
                    st.markdown(f"- ✅ {highlight}")
            else:
                st.info("No specific highlights identified.")
        
        with col2:
            st.subheader("⚠️ Concerns")
            concerns = report.get('summary', {}).get('concerns', report.get('concerns', []))
            if concerns:
                for concern in concerns:
                    st.markdown(f"- ⚠️ {concern}")
            else:
                st.success("No concerns identified!")
        
        st.divider()
        
        # Full Report
        if st.button("📄 View Full Report"):
            full_report = get_report(st.session_state.interview_id)
            if full_report:
                st.json(full_report)
    else:
        st.error("❌ Could not load interview results. Please try refreshing the page.")

if __name__ == "__main__":
    main()
