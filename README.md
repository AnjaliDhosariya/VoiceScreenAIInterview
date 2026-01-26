# VoiceScreen AI - Autonomous Interview Agent

## Overview
VoiceScreen AI is an autonomous interview backend service that conducts structured AI-led interviews, evaluates candidates, and generates comprehensive reports with hiring recommendations.

## Features
- ✅ AI-driven interview flow with state management
- ✅ Dynamic question generation using Groq LLM
- ✅ Real-time answer evaluation
- ✅ Signal processing (talk ratio, sentiment, response quality)
- ✅ Executive summary with PROCEED/HOLD/REJECT recommendation
- ✅ Mock ATS integration
- ✅ Full transcript and report generation

## Tech Stack
- **Framework**: FastAPI
- **Database**: Supabase (PostgreSQL)
- **LLM**: Groq (Llama 3.3)
- **State Management**: LangGraph (State Machine)
- **Validation**: Pydantic

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file in the root directory:
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
GROQ_API_KEY=your_groq_api_key
```

### 3. Database Setup
Ensure your Supabase project is active. Then, go to the **SQL Editor** in Supabase dashboard and execute the migration scripts located in `src/db/migrations/`:

**Order of execution:**
1. `src/db/migrations/001_add_constraints.sql` (Creates constraints)
2. `src/db/migrations/002_fix_status_constraint.sql` (Fixes 500 error for status)

Base tables required:
- `interview_sessions`
- `interview_turns`
- `interview_scores`
- `interview_signals`
- `ats_sync_logs`

### 4. Run the Backend Server
```bash
python run.py
```

**Alternative methods:**
```bash
# Method 1: Using uvicorn directly (recommended)
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload

# Method 2: Python module
python -m uvicorn src.main:app --host 0.0.0.0 --port 8080
```

The backend server will start on `http://localhost:8080`

### 5. Run the Frontend (Optional)
```bash
python run_frontend.py
```

Or directly:
```bash
streamlit run frontend_app.py
```

The Streamlit frontend will open at `http://localhost:8501`

**Features:**
- 🎙️ Interactive interview interface
- 📋 Real-time status tracking
- 💬 Q&A flow with history
- 📊 Results dashboard with scores
- 🎯 Recommendation display

## API Documentation

### Base URL
```
http://localhost:8080
```

### Endpoints

#### 1. Create Interview
```http
POST /hr/interview/create
```
**Request:**
```json
{
  "candidateId": "CAND-001",
  "jobId": "JOB-101",
  "channel": "simulation",
  "consentRequired": true
}
```

#### 2. Get Disclosure
```http
GET /hr/interview/{interviewId}/disclosure
```

#### 3. Submit Consent
```http
POST /hr/interview/{interviewId}/consent
```
**Request:**
```json
{
  "consent": "yes"
}
```

#### 4. Get Next Question
```http
GET /hr/interview/{interviewId}/next-question
```

#### 5. Submit Answer
```http
POST /hr/interview/{interviewId}/answer
```
**Request:**
```json
{
  "turnNo": 1,
  "answer": "I once worked with..."
}
```

#### 6. Finish Interview
```http
POST /hr/interview/{interviewId}/finish
```

#### 7. Get Report
```http
GET /hr/interview/{interviewId}/report
```

## Testing with Postman/cURL

### Complete Interview Flow

1. **Create Interview**
```bash
curl -X POST http://localhost:8080/hr/interview/create \
  -H "Content-Type: application/json" \
  -d '{
    "candidateId": "CAND-001",
    "jobId": "JOB-101",
    "channel": "simulation",
    "consentRequired": true
  }'
```

2. **Get Disclosure**
```bash
curl http://localhost:8080/hr/interview/INT-{timestamp}/disclosure
```

3. **Submit Consent**
```bash
curl -X POST http://localhost:8080/hr/interview/INT-{timestamp}/consent \
  -H "Content-Type: application/json" \
  -d '{"consent": "yes"}'
```

4. **Get Question & Answer (Repeat 5-10 times)**
```bash
# Get question
curl http://localhost:8080/hr/interview/INT-{timestamp}/next-question

# Submit answer
curl -X POST http://localhost:8080/hr/interview/INT-{timestamp}/answer \
  -H "Content-Type: application/json" \
  -d '{
    "turnNo": 1,
    "answer": "Your answer here"
  }'
```

5. **Finish Interview**
```bash
curl -X POST http://localhost:8080/hr/interview/INT-{timestamp}/finish
```

6. **Get Report**
```bash
curl http://localhost:8080/hr/interview/INT-{timestamp}/report
```

## Interview Flow States

```
CREATED → DISCLOSURE_DONE → CONSENT_GRANTED → INTERVIEW_IN_PROGRESS → COMPLETED → SYNCED_TO_ATS
```

## Scoring Logic

### Recommendation Rules
- **PROCEED**: overall ≥ 75 AND no red flags AND consent granted
- **HOLD**: overall 60-74 OR missing 1 must-have skill
- **REJECT**: overall < 60 OR major red flags

### Evaluation Criteria
- Technical (0-100): Correctness and depth of technical answers
- Communication (0-100): Clarity, structure, articulation
- Culture (0-100): Confidence, ownership, team fit

## Project Structure
```
src/
  ├── main.py                          # FastAPI entry point
  ├── config.py                        # Configuration
  ├── routes/
  │   └── interview_routes.py          # API routes
  ├── controllers/
  │   └── interview_controller.py      # Business logic
  ├── services/
  │   ├── session_service.py           # Session management
  │   ├── question_service.py          # Question handling
  │   ├── scoring_service.py           # Scoring logic
  │   ├── signals_service.py           # Signal processing
  │   ├── summary_service.py           # Summary generation
  │   ├── ats_sync_service.py          # ATS integration
  │   └── compliance_service.py        # Consent/Disclosure
  ├── agents/
  │   ├── question_generator_agent.py  # LLM question generation
  │   └── evaluator_agent.py           # LLM evaluation
  ├── db/
  │   └── supabase_client.py           # Database client
  └── schemas/
      └── interview_schema.py          # Pydantic models
```

## License
MIT
