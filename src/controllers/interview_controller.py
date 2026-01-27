import concurrent.futures
from typing import List, Dict, Any, Optional
from src.services.session_service import SessionService
from src.services.question_service import QuestionService
from src.services.compliance_service import ComplianceService
from src.services.scoring_service import ScoringService
from src.services.signals_service import SignalsService
from src.services.summary_service import SummaryService
from src.services.ats_sync_service import ATSSyncService
from src.agents.question_generator_agent import QuestionGeneratorAgent
from src.agents.evaluator_agent import EvaluatorAgent
from src.agents.interview_flow_graph import interview_graph, InterviewState
# NEW: Agentic interviewer imports
from src.agents.agentic_interviewer import AgenticInterviewer
from src.services.state_persistence import StatePersistence
from src.services.job_service import job_service

class InterviewController:
    """Business logic for interview operations"""
    
    def __init__(self):
        # NEW: Use agentic interviewer instead of basic question generator
        self.agentic_interviewer = AgenticInterviewer()
        self.evaluator_agent = EvaluatorAgent()
        self.graph = interview_graph.get_graph()
        # Store state in memory (in production, use persistent storage)
        self.state_store = {}
    
    def create_interview(self, candidate_id: str, job_id: str, channel: str, consent_required: bool) -> Dict[str, Any]:
        """Create a new interview session"""
        # P1: Check if candidate already has an active interview
        existing_interview_id = SessionService.check_active_interview(candidate_id)
        if existing_interview_id:
            raise ValueError(f"Candidate {candidate_id} already has an active interview: {existing_interview_id}")
        
        interview_id = SessionService.create_session(candidate_id, job_id, channel, consent_required)
        
        # Initialize LangGraph state
        initial_state: InterviewState = {
            "interview_id": interview_id,
            "candidate_id": candidate_id,
            "job_id": job_id,
            "status": "CREATED",
            "consent_granted": False,
            "current_turn": 0,
            "max_turns": 10,
            "questions_asked": [],
            "answers_received": [],
            "evaluation_scores": [],
            "error": None
        }
        self.state_store[interview_id] = initial_state
        
        return {
            "interviewId": interview_id,
            "status": "CREATED",
            "nextStep": "DISCLOSURE"
        }
    
    def get_disclosure(self, interview_id: str) -> Dict[str, Any]:
        """Get disclosure text and update status"""
        session = SessionService.get_session(interview_id)
        if not session:
            raise ValueError(f"Interview {interview_id} not found")
        
        disclosure_text = ComplianceService.get_disclosure_text()
        
        # Only update status and save disclosure if status is CREATED
        # This prevents duplicate disclosure when called multiple times
        if session['status'] == 'CREATED':
            # Update status
            SessionService.update_session_status(interview_id, "DISCLOSURE_DONE")
            
            # Save disclosure as a system turn (only once)
            QuestionService.save_turn(interview_id, 0, "system", disclosure_text)
        
        return {
            "interviewId": interview_id,
            "disclosureText": disclosure_text,
            "statusAfter": session['status'] if session['status'] != 'CREATED' else "DISCLOSURE_DONE"
        }
    
    def submit_consent(self, interview_id: str, consent: str) -> Dict[str, Any]:
        """Process consent response"""
        session = SessionService.get_session(interview_id)
        if not session:
            raise ValueError(f"Interview {interview_id} not found")
        
        is_consent_granted = ComplianceService.validate_consent(consent)
        
        # Update LangGraph state
        if interview_id in self.state_store:
            self.state_store[interview_id]["consent_granted"] = is_consent_granted
            self.state_store[interview_id]["status"] = "CONSENT_GRANTED" if is_consent_granted else "ENDED"
        
        if is_consent_granted:
            SessionService.update_consent(interview_id, "granted", consent)
            SessionService.update_session_status(interview_id, "CONSENT_GRANTED")
            
            return {
                "consentStatus": "GRANTED",
                "status": "CONSENT_GRANTED",
                "nextStep": "START_INTERVIEW"
            }
        else:
            SessionService.update_consent(interview_id, "denied", consent)
            SessionService.update_session_status(interview_id, "ENDED")
            
            return {
                "consentStatus": "DENIED",
                "status": "ENDED",
                "nextStep": None
            }
    
    def get_next_question(self, interview_id: str) -> Dict[str, Any]:
        """Generate and return next question using agentic interviewer"""
        session = SessionService.get_session(interview_id)
        if not session:
            raise ValueError(f"Interview {interview_id} not found")
        
        # Start interview if not started
        if session["status"] == "CONSENT_GRANTED":
            SessionService.start_interview(interview_id)
        
        # NEW: Load or create candidate state
        state = StatePersistence.get_or_create_state( # Changed to use StatePersistence
            interview_id=interview_id,
            candidate_id=session["candidate_id"],
            job_id=session["job_id"]
        )
        
        # FIX: Fetch real conversation history (memory)
        turns = QuestionService.get_turns(interview_id)
        
        # NEW: Agent generates next question (makes autonomous decisions)
        try:
            question_data = self.agentic_interviewer.generate_next_question(
                state=state, 
                job_id=session["job_id"],
                previous_answers=turns # Pass real history
            )
        except Exception as e:
            print(f"CRITICAL ERROR in agent generation: {e}")
            import traceback
            traceback.print_exc()
            
            # CRITICAL FIX: Increment turn count to prevent infinite loop
            # If we don't increment, we'll keep asking Q3 forever upon error
            state.question_count += 1
            StatePersistence.save_state(state)
            
            # Fallback question to prevent crash (AVOID BACKGROUND - already covered in warmup)
            question_data = {
                "type": "motivation",
                "question": "What aspects of this role are you most excited about?",
                "rubric": {"mustMention": ["Interest", "Goals"]}
            }
        
        if not question_data:
            # Agent decided to finish
            SessionService.finish_interview(interview_id)
            # Return with required fields to satisfy API validation
            return {
                "turnNo": state.question_count,
                "questionType": "completion",
                "question": "",
                "expectedSignals": [],
                "status": "COMPLETED",
                "final": True,
                "message": "Interview completed",
                "totalQuestions": state.question_count
            }
        
        # Performance/Accuracy Fix: Save state immediately so turn tracking is updated 
        # before the candidate can request the next turn.
        StatePersistence.save_state(state)
        
        # Calculate actual turn number (now synchronized by agentic interviewer)
        next_turn_no = state.question_count
        
        # Save question as agent turn
        QuestionService.save_turn(interview_id, next_turn_no, "agent", question_data["question"])
        
        return {
            "turnNo": next_turn_no,
            "questionType": question_data["type"],
            "question": question_data["question"],
            "expectedSignals": question_data.get("rubric", {}).get("mustMention", []),
            "agentDifficulty": state.current_difficulty, # Directly from state
            "totalQuestions": f"{state.question_count + 1}/10-15"
        }
    
    def submit_answer(self, interview_id: str, turn_no: int, answer: str) -> Dict[str, Any]:
        """Process candidate answer (Deferred Evaluation to save API hits)"""
        try:
            session = SessionService.get_session(interview_id)
            if not session:
                raise ValueError(f"Interview {interview_id} not found")
            
            # Save answer immediately to transcript
            QuestionService.save_turn(interview_id, turn_no, "candidate", answer)
            
            # CHECK: If previous question was candidate_questions type, generate LLM response
            turns = QuestionService.get_turns(interview_id)
            # Find the question that corresponds to this answer
            question_turn = None
            for turn in reversed(turns):
                if turn["speaker"] == "agent" and turn["turn_no"] == turn_no:
                    question_text = turn.get("text", "").lower()
                    if "do you have any questions" in question_text or "questions for me" in question_text:
                        question_turn = turn
                        break
            
            # If it's candidate_questions and candidate asked something (not declining)
            if question_turn:
                answer_lower = answer.lower().strip()
                is_declining = any(phrase in answer_lower for phrase in [
                    "no question", "no, thank", "nothing", "i don't have", "i'm good", "that's all", "nope"
                ])
                
                if not is_declining and len(answer.strip()) > 10:  # Candidate asked something
                    try:
                        llm_response = self.agentic_interviewer.generate_answer_to_candidate_question(
                            candidate_question=answer,
                            job_id=session["job_id"]
                        )
                        
                        # Save the LLM's response as an additional turn
                        QuestionService.save_turn(
                            interview_id=interview_id,
                            turn_no=turn_no,
                            speaker="agent",
                            text=llm_response
                        )
                        
                        print(f"[INFO] Generated response to candidate question: {llm_response[:100]}...")
                    except Exception as e:
                        print(f"[ERROR] Failed to generate response to candidate question: {e}")
            
            # API REDUCTION: We no longer evaluate every answer as it comes in.
            # We will evaluate in the final report or only when deep context is needed.
            
            return {
                "received": True,
                "status": "INTERVIEW_IN_PROGRESS",
                "nextStep": "NEXT_QUESTION"
            }
        except Exception as e:
            print(f"[ERROR] submit_answer failed: {str(e)}")
            raise
    
    def get_turns(self, interview_id: str) -> List[Dict[str, Any]]:
        """Get full transcript of the interview"""
        try:
            return QuestionService.get_turns(interview_id)
        except Exception as e:
            print(f"[ERROR] get_turns failed: {str(e)}")
            raise
            
    def finish_interview(self, interview_id: str) -> Dict[str, Any]:
        """Finish interview and generate report with absolute robustness"""
        try:
            session = SessionService.get_session(interview_id)
            if not session:
                raise ValueError(f"Interview {interview_id} not found")
            
            # 1. Gather all data
            turns = QuestionService.get_turns(interview_id)
            print(f"[DEBUG] Processing {len(turns)} turns for {interview_id}")
            
            # 2. Parallel Evaluation (Core Intelligence)
            try:
                job_data = job_service.get_job(session["job_id"])
                evaluations = self._evaluate_all_answers(turns, job_data)
            except Exception as e:
                print(f"[ERROR] Parallel evaluation failed: {e}")
                evaluations = []
            
            # 3. Score Aggregation
            scores = self.evaluator_agent.aggregate_scores(evaluations)
            
            # 4. Signals Calculation
            try:
                signals = SignalsService.calculate_signals(interview_id, turns)
                SignalsService.save_signals(interview_id, signals)
            except Exception as e:
                print(f"[ERROR] SignalsService failed: {e}")
                signals = {"talk_ratio": 0.5, "sentiment": "neutral", "call_quality_score": 100}
            
            # 5. Summary Generation (now includes evaluations)
            try:
                summary = SummaryService.generate_summary(interview_id, scores, turns, evaluations)
            except Exception as e:
                print(f"[ERROR] SummaryService failed: {e}")
                summary = {
                    "recommendation": "HOLD",
                    "highlights": ["Data gathered successfully"],
                    "concerns": ["Internal summary generator error"],
                    "num_questions_answered": len([t for t in turns if t["speaker"] == "candidate"])
                }
            
            # 6. Database Persistence
            try:
                ScoringService.save_scores(
                    interview_id,
                    scores["technical"],
                    scores["communication"],
                    scores["culture"],
                    scores["overall"],
                    summary["recommendation"],
                    {"highlights": summary["highlights"], "concerns": summary["concerns"]}
                )
            except Exception as e:
                print(f"[ERROR] Database save failed: {e}")
            
            # 7. Final status update
            try:
                SessionService.finish_interview(interview_id)
            except Exception as e:
                print(f"[ERROR] Status update failed: {e}")
            
            # 8. ATS Sync (Async-like)
            try:
                transcript = [{"turn": t["turn_no"], "speaker": t["speaker"], "text": t["text"]} for t in turns]
                ATSSyncService.sync_to_ats(
                    interview_id,
                    session["candidate_id"],
                    session["job_id"],
                    transcript,
                    scores if scores else {"technical":0, "communication":0, "culture":0, "overall":0},
                    summary["recommendation"],
                    summary
                )
            except Exception as e:
                print(f"[WARN] ATS sync skipped/failed: {e}")
            
            # Return final results
            return {
                "interviewId": interview_id,
                "recommendation": summary["recommendation"],
                "overallScore": scores["overall"],
                "scores": scores,
                "highlights": summary["highlights"],
                "concerns": summary["concerns"],
                "status": "COMPLETED"
            }
            
        except Exception as e:
            # ULTIMATE FALLBACK: Never return 500
            print(f"[CRITICAL] finish_interview crashed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "interviewId": interview_id,
                "recommendation": "HOLD",
                "overallScore": 50,
                "scores": {"technical": 50, "communication": 50, "culture": 50, "overall": 50},
                "highlights": ["Interview completed successfully"],
                "concerns": ["Technical error during final report generation"],
                "status": "COMPLETED"
            }
    
    def get_report(self, interview_id: str) -> Dict[str, Any]:
        """Get full interview report"""
        session = SessionService.get_session(interview_id)
        if not session:
            raise ValueError(f"Interview {interview_id} not found")
        
        turns = QuestionService.get_turns(interview_id)
        scores = ScoringService.get_scores(interview_id)
        signals = SignalsService.get_signals(interview_id)
        
        transcript = [
            {
                "turnNo": t["turn_no"],
                "speaker": t["speaker"],
                "text": t["text"],
                "timestamp": t["timestamp"]
            }
            for t in turns
        ]
        
        return {
            "interviewId": interview_id,
            "candidateId": session["candidate_id"],
            "jobId": session["job_id"],
            "status": session["status"],
            "transcript": transcript,
            "scores": scores,
            "signals": signals,
            "summary": scores.get("reasoning", {}) if scores else {}
        }
    
    def _extract_qa_pairs(self, turns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract question-answer pairs from turns with turn numbers"""
        qa_pairs = []
        questions = {t["turn_no"]: t["text"] for t in turns if t["speaker"] == "agent"}
        answers = {t["turn_no"]: t["text"] for t in turns if t["speaker"] == "candidate"}
        
        # Match by turn number to ensure alignment
        for turn_no in sorted(questions.keys()):
            if turn_no in answers:
                qa_pairs.append({
                    "turn_no": turn_no,
                    "question": questions[turn_no],
                    "answer": answers[turn_no]
                })
        
        return qa_pairs
    
    def _evaluate_all_answers(self, turns: List[Dict[str, Any]], job_data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Evaluate all Q&A pairs in parallel to reduce latency"""
        print(f"[DEBUG] Starting parallel evaluation of {len(turns)} turns")
        qa_pairs = self._extract_qa_pairs(turns)
        
        # Performance Choice: Use ThreadPoolExecutor for parallel API calls
        MAX_WORKERS = 5
        evaluations = []
        
        # Map turn numbers to types from the agent's plan
        plan = self.agentic_interviewer.BASE_QUESTION_PLAN
        
        def safe_evaluate(qa):
            try:
                turn_no = qa.get("turn_no", 0)
                # Determine type from plan (turn_no 1 is index 0)
                q_type = "technical"
                if 1 <= turn_no <= len(plan):
                    q_type = plan[turn_no - 1]["type"]
                
                print(f"[DEBUG] Evaluating turn {turn_no} ({q_type})...")
                
                return self.evaluator_agent.evaluate_answer(
                    qa["question"],
                    qa["answer"],
                    q_type,
                    {"mustMention": [], "goodToMention": [], "redFlags": []},
                    job_data
                )
            except Exception as e:
                print(f"[ERROR] Individual evaluation failed: {e}")
                return {
                    "technical": 5, "communication": 5, "structure": 5, "confidence": 5,
                    "strengths": ["Evaluation failed - data saved"],
                    "improvements": ["Model timeout or rate limit reached"]
                }

        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            results = list(executor.map(safe_evaluate, qa_pairs))
            evaluations.extend([r for r in results if r])
        
        print(f"[DEBUG] Completed parallel evaluation. Got {len(evaluations)} results.")
        return evaluations
