# VoiceScreen AI - Autonomous Agentic Interviewer

VoiceScreen AI is an autonomous interview system that conducts structured, AI-led technical and behavioral interviews. It leverages large language models (Groq Llama 3) and a sophisticated state-machine architecture to evaluate candidates with high-fidelity across technical, communication, and cultural dimensions.

---

## 🚀 Key Features

### 1. Adaptive Interview Flow & Intelligence
- **8-Step Master Plan**: Ensures a balanced evaluation across:
    - **Warmup**: Catchy intro connecting background to role.
    - **Behavioral (x2)**: Strict STAR-method situational probes.
    - **Motivation**: Alignment with role and company technical vision.
    - **Technical (x2)**: Domain-specific deep dives from Job Description.
    - **Scenario**: Hypothetical business or professional crisis management.
    - **Culture**: Team-fit and working style preferences.
- **Dynamic Difficulty Scaling**: Implicit real-time scaling (Easy/Medium/Hard) based on the candidate's last 3 responses.
- **Second-Chance Extension**: Automatically extends the interview if a candidate shows a single technical gap but is otherwise strong, allowing for recovery.

### 2. Gaming & Fraud Protection
- **Relevance Gate**: Strictly detects and penalizes "canned" responses. If a candidate provides an irrelevant answer (e.g., a behavioral story for a technical question), the system mandates a **0/10 technical score**.
- **Similarity Recognition**: Real-time word-overlap check (>85%) against previous turns to identify copy-pasted or repetitive answers across questions.
- **Auto-Reject Protocol**: Automatic termination and "REJECT" recommendation for candidates attempting to bypass evaluation loops.

### 3. Role-Aware Logic
- **Junior/Fresher Mastery**: Rewards strong conceptual knowledge in entry-level candidates while prioritizing logic and structure.
- **Senior Strategic Bar**: Enforces high-level deep dives into architecture, trade-offs, and edge cases.
- **STAR Method Enforcement**: Penalizes behavioral answers that lack Situation, Task, Action, and Result evidence.

### 4. High-Fidelity Reporting
- **Intelligent Summarization**: Automatically suppresses generic LLM nitpicks ("expand more") and placeholder highlights ("provided a response") to focus on genuine hiring signals.
- **Unified Scorecard**: Aggregates Technical (weighted), Communication, and Culture scores into a single 0-100 index.
- **Deterministic Orientation**: Eliminates "False Gibberish" flags by deterministically scoring non-substantive turns (Consent, Wrap-up, Q&A).

---

## 🏗️ Technical Architecture

The system operates as a multi-agent orchestration layer powered by **LangGraph** and **Groq**:

- **AgenticInterviewer (The Decision Engine)**: Manages state progression, chooses the next topic (Skill Filter), and handles second-chance logic.
- **QuestionGeneratorAgent (Execution)**: Crafts adaptive questions that "bridge" to facts mentioned in the candidate's history.
- **EvaluatorAgent (The Grader)**: Performs atomic evaluation of each turn against a dynamically generated rubric.
- **SummaryService (The Synthesizer)**: Applies the "Priority Waterfall" (Gaming -> Disqualifiers -> Smoothing) to determine the final recommendation.

---

## ⚙️ Setup & Installation

### 1. Prerequisites
- Python 3.9+
- Groq API Key
- Supabase Project

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```

### 4. Database Setup
Execute migration scripts in the Supabase SQL Editor in the following order:
1. `src/db/migrations/001_add_constraints.sql` (Creates core constraints)
2. `src/db/migrations/002_fix_status_constraint.sql` (Fixes stability issues)

**Base Tables Required**: `interview_sessions`, `interview_turns`, `interview_scores`, `interview_signals`, `ats_sync_logs`.

---

## 🚦 Running the Application

### 1. Run the Backend Server
```bash
python run.py
```
*Alternatively (Recommended for Dev)*:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```
The server will start at `http://localhost:8080`.

### 2. Run the (Optional) Frontend
```bash
python run_frontend.py
```
The Streamlit dashboard will open at `http://localhost:8501`.

---

## � API Documentation

### Base URL: `http://localhost:8080`

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/hr/interview/create` | `POST` | Initialize a new interview session. |
| `/hr/interview/{id}/disclosure` | `GET` | Retrieve legal/privacy disclosure. |
| `/hr/interview/{id}/consent` | `POST` | Submit candidate consent ("yes"/"no"). |
| `/hr/interview/{id}/next-question` | `GET` | Trigger the next agentic question. |
| `/hr/interview/{id}/answer` | `POST` | Submit an answer and trigger evaluation. |
| `/hr/interview/{id}/finish` | `POST` | Finalize scoring and generate summary. |
| `/hr/interview/{id}/report` | `GET` | Retrieve the final high-fidelity report. |

---

## � Scoring & Recommendation Logic

The system uses a **Priority Waterfall** to ensure safe and accurate decisions:

### Recommendation Rules
- **PROCEED**: Overall Score ≥ 75 **AND** no major red flags.
- **HOLD**: Overall Score 60-74 **OR** mixed signals (e.g., high tech, low communication).
- **REJECT**: Overall Score < 60 **OR** >2 Irrelevant/Repetitive turns **OR** Critical Red Flags.

### Evaluation Criteria (0-100)
- **Technical**: Correctness, depth, and edge-case handling.
- **Communication**: Clarity, structure, professional tone, and articulation.
- **Culture**: Confidence, ownership, and alignment with high-performance team values.

---

## 📁 Project Structure

```text
.
├── src/
│   ├── agents/
│   │   ├── agentic_interviewer.py   # Decision Engine & State Machine
│   │   ├── candidate_state.py       # Candidate State Model
│   │   ├── evaluator_agent.py       # LLM Grading Logic
│   │   ├── interview_flow_graph.py  # LangGraph Workflow Definition
│   │   └── question_generator_agent.py # Adaptive Question Generation
│   ├── controllers/
│   │   └── interview_controller.py  # Main Interview Orchestration
│   ├── db/
│   │   ├── migrations/
│   │   │   ├── 001_add_constraints.sql
│   │   │   └── 002_fix_status_constraint.sql
│   │   ├── schema_candidate_states.sql
│   │   └── supabase_client.py       # Database Connection
│   ├── frontend/
│   │   └── frontend_app.py          # Streamlit UI
│   ├── routes/
│   │   └── interview_routes.py      # API Endpoints
│   ├── schemas/
│   │   └── interview_schema.py      # Pydantic Models
│   ├── services/
│   │   ├── ats_sync_service.py      # Mock ATS Integration
│   │   ├── compliance_service.py    # Disclosure & Consent
│   │   ├── job_service.py           # Job Description Management
│   │   ├── question_service.py      # Question Content Logic
│   │   ├── scoring_service.py       # Score Persistence
│   │   ├── session_service.py       # Session Lifecycle
│   │   ├── signals_service.py       # Audio/Text Signals
│   │   ├── state_persistence.py     # Resume/Save State
│   │   └── summary_service.py       # Report Generation
│   ├── config.py                    # Environment Configuration
│   └── main.py                      # Application Entry Point
├── job_descriptions.json            # Mock Job Data
├── question_generation_logic.md     # Logic Documentation (Gen)
├── scoring_and_evaluation_logic.md  # Logic Documentation (Eval)
├── requirements.txt                 # Dependencies
├── run.py                           # Backend Launcher
├── run_frontend.py                  # Frontend Launcher
└── README.md                        # Documentation
```

---

## 📄 Documentation Deep-Dives
- [Question Generation Logic]
- [Scoring & Evaluation Logic]

---

## 📄 License
This project is licensed under the MIT License.
