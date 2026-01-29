from typing import Dict, Any, List, Literal, Optional, Tuple
from datetime import datetime
from src.agents.candidate_state import CandidateState, Decision
from src.agents.question_generator_agent import QuestionGeneratorAgent
from src.services.job_service import job_service

class AgenticInterviewer:
    """
    Autonomous interview agent that makes intelligent decisions within bounds (10-12 questions).
    
    This agent:
    - Decides when to terminate (after 10 min, before 12 max)
    - Chooses difficulty levels based on performance
    - Selects which technical skills to test
    - Adds follow-up questions when needed
    - Maintains and evolves candidate state
    """
    
    # Constants
    MIN_CORE_QUESTIONS = 8  # Core evaluation questions (Strict 8-step plan)
    MIN_QUESTIONS = 10  # Minimum total including candidate Q&A + wrap-up
    MAX_QUESTIONS = 12  # Strict limit to prevent long interviews
    END_INTERVIEW_BUFFER = 2  # Slots for candidate Q&A + wrap-up
    
    # Core 8-question evaluation plan (Verified User Request)
    BASE_QUESTION_PLAN = [
        {"type": "warmup", "description": "Intro + warm-up (easy)"},
        {"type": "behavioral", "description": "Behavioral question 1 (conflict/stakeholder)"},
        {"type": "behavioral", "description": "Behavioral question 2 (ownership/result)"},
        {"type": "motivation", "description": "Role motivation question"},
        {"type": "technical", "description": "JD-specific domain Q1"},
        {"type": "technical", "description": "JD-specific domain Q2"},
        {"type": "scenario", "description": "Scenario/case question (role-appropriate)"},
        {"type": "culture", "description": "Culture fit question"}
    ]
    
    def __init__(self):
        self.question_generator = QuestionGeneratorAgent()
    
    # ============================================================
    # DECISION LOGIC (TRUE AGENCY)
    # ============================================================
    
    def should_continue_after_minimum(self, state: CandidateState) -> Tuple[bool, str]:
        """
        Decide whether to continue interview after 8 core questions.
        Strategy: Stop if we have enough data (Avg >= 7.0), only probe if weak/unclear.
        """
        # Must complete at least 8 core questions
        if state.question_count < self.MIN_CORE_QUESTIONS:
            return True, f"Must complete minimum {self.MIN_CORE_QUESTIONS} core questions"
        
        # Cannot exceed MAX
        if state.question_count >= self.MAX_QUESTIONS - self.END_INTERVIEW_BUFFER:
            return False, "Reached maximum questions limit"
        
        # AGENT AUTONOMOUS DECISIONS (Limit to ONE extra question total):
        
        # If we have already asked more than core questions, force move to wrap-up
        if state.question_count >= self.MIN_CORE_QUESTIONS + 1:
            return False, "Already provided one extension question - ending interview"

        # Check for EXACTLY one technical/scenario failure while others are strong
        # This implementation follows the "add only 1 extra question" rule.
        important_categories = ["behavioral", "motivation", "technical", "scenario"]
        failed_cats = []
        strong_cats = []
        
        for cat in important_categories:
            scores = state.category_scores.get(cat, [])
            if not scores: continue
            
            avg_cat = sum(scores) / len(scores)
            min_cat = min(scores)
            
            # Failure defined as low average or a specific very poor answer
            if avg_cat < 6.0 or min_cat < 4.5:
                failed_cats.append(cat)
            elif avg_cat >= 7.5:
                 strong_cats.append(cat)
        
        # Extension Rule: Only for technical or scenario failure, and only if other areas are solid.
        if len(failed_cats) == 1 and failed_cats[0] in ["technical", "scenario"] and len(strong_cats) >= 2:
            state.second_chance_category = failed_cats[0]
            return True, f"Second Chance: Validating {failed_cats[0]} with one additional question since other areas are strong."

        # Default: End interview after 8 questions
        return False, "Sufficient data gathered or general performance does not warrant extension"
    
    def should_add_followup(self, state: CandidateState) -> Tuple[bool, str, str]:
        """
        Decide if we need to add a follow-up question based on last answer.
        
        Returns: (should_add, followup_type, reasoning)
        followup_type: "clarify" | "deep_dive" | "probe_red_flag"
        """
        # Only if we haven't hit max questions
        if state.question_count >= self.MAX_QUESTIONS:
            return False, "", "Already at maximum questions"
        
        # Don't add follow-ups before completing core 8
        if state.question_count < self.MIN_CORE_QUESTIONS:
            return False, "", "Must complete core plan first"
        
        # Reset follow-up logic if candidate shows strong recovery
        if state.strong_answer_count >= 1 and state.last_question_type in ["technical", "scenario"]:
            return False, "", "Candidate showed strength - skipping further technical follow-ups"

        # Add follow-up if answer was vague or weak (score < 5)
        if state.last_score < 5 and state.last_question_type in ["behavioral", "technical", "scenario"]:
            return True, "clarify", f"Vague/weak answer (score {state.last_score}/10) - need clarification"
        
        # Add follow-up if answer showed exceptional insight (score >= 9)
        if state.last_score >= 9 and state.last_question_type in ["technical", "scenario"]:
            return True, "deep_dive", f"Exceptional answer (score {state.last_score}/10) - explore deeper"
        
        # Add follow-up if red flag was detected
        if state.red_flags and len(state.red_flags) > len(state.decisions_made) - 5:
            # Recent red flag (within last 5 decisions)
            return True, "probe_red_flag", f"Red flag detected: {state.red_flags[-1]}"
        
        return False, "", "No follow-up needed"
    
    def decide_difficulty(self, state: CandidateState, step_no: int) -> Literal["easy", "medium", "hard"]:
        """
        Decide difficulty level for next question based on performance trend.
        """
        # First few questions (1-3) - start at medium
        if step_no <= 2 or not state.performance_trend:
            return "medium"
        
        # Calculate recent average (last 3 scores)
        avg = state.recent_avg_score
        
        # Strong performance → challenge them
        if avg >= 8.0:
            return "hard"
        
        # Struggling → simplify
        elif avg < 5.0:
            return "medium"
        
        # Average → standard difficulty
        else:
            return "medium"
    
    def select_technical_skill(self, state: CandidateState, job_id: str, step_no: int) -> str:
        """
        Intelligently select which technical skill to test from JD must-have skills.
        
        Agent decides based on:
        - Which skills haven't been tested yet
        - Which skills are most important for the role
        - Whether to address weak areas (if follow-up)
        """
        # Get job data
        job_data = job_service.get_job(job_id)
        if not job_data:
            return "general technical knowledge"
        
        must_have_skills = job_data.get('must_have_skills', [])
        if not must_have_skills:
            return "general technical knowledge"
        
        # Remove already tested skills
        untested = [s for s in must_have_skills if s not in state.skills_tested]
        
        # [REFINEMENT] If must_have_skills are exhausted, try nice_to_have or focus areas
        if not untested:
            nice_to_have = job_data.get('nice_to_have_skills', [])
            focus_areas = job_data.get('technical_focus_areas', [])
            untested = [s for s in nice_to_have + focus_areas if s not in state.skills_tested]
        
        # If this is Q5 (first technical) - pick primary skill
        if step_no == 5:
            # Return first untested, or first if all tested
            return untested[0] if untested else must_have_skills[0]
        
        # If this is Q6 (second technical) - pick complementary skill
        elif step_no == 6:
            # Return second untested, or second if all tested
            if len(untested) >= 2:
                return untested[1]
            elif len(untested) == 1:
                return untested[0]
            else:
                return must_have_skills[1] if len(must_have_skills) > 1 else must_have_skills[0]
        
        # If this is a follow-up technical (Q11-15)
        else:
            # If candidate showed weakness, test core skills again at higher difficulty
            if state.avg_score < 6.0 and state.skills_tested:
                # Re-test a skill they struggled with
                return list(state.skills_tested)[0]
            else:
                # Test new skill
                return untested[0] if untested else must_have_skills[0]
    
    def decide_termination(self, state: CandidateState) -> Decision:
        """
        Make termination decision and return as a Decision object.
        """
        should_continue, reasoning = self.should_continue_after_minimum(state)
        
        action = "continue" if should_continue else "terminate"
        
        return Decision(
            timestamp=datetime.utcnow().isoformat(),
            question_number=state.question_count,
            decision_type="terminate" if not should_continue else "continue",
            action=action,
            reasoning=reasoning,
            context={
                "avg_score": state.avg_score,
                "red_flags_count": len(state.red_flags),
                "green_flags_count": len(state.green_flags),
                "question_count": state.question_count
            }
        )
    
    # ============================================================
    # STATE MANAGEMENT
    # ============================================================
    
    def update_state_after_evaluation(
        self, 
        state: CandidateState, 
        evaluation: Dict[str, Any],
        question: str,
        question_type: str,
        answer: str
    ) -> CandidateState:
        """
        Update candidate state based on evaluation results.
        
        Called after each answer is evaluated.
        """
        # Calculate overall score from evaluation with defensive casting
        try:
            technical = float(evaluation.get("technical", 0))
            communication = float(evaluation.get("communication", 0))
            structure = float(evaluation.get("structure", 0))
            confidence = float(evaluation.get("confidence", 0))
            
            overall = (technical + communication + structure + confidence) / 4.0
        except (ValueError, TypeError):
            overall = 5.0
        
        # Update performance with category tracking
        state.update_performance(overall, category=question_type)
        
        # Update context
        state.last_question = question
        state.last_question_type = question_type
        state.last_answer = answer
        
        # Extract and add signals
        strengths = evaluation.get("strengths", [])
        improvements = evaluation.get("improvements", [])
        
        for strength in strengths:
            if strength not in state.green_flags:
                state.green_flags.append(strength)
        
        for improvement in improvements:
            if improvement not in state.red_flags:
                state.red_flags.append(improvement)
        
        # Adapt difficulty for next question
        new_difficulty = self.decide_difficulty(state, state.question_count + 1)
        if new_difficulty != state.current_difficulty:
            state.current_difficulty = new_difficulty
            state.add_decision(Decision(
                timestamp=datetime.utcnow().isoformat(),
                question_number=state.question_count,
                decision_type="difficulty",
                action=f"changed_to_{new_difficulty}",
                reasoning=f"Performance trend indicates {new_difficulty} difficulty appropriate",
                context={"recent_avg": state.recent_avg_score}
            ))
        
        return state
    
    # ============================================================
    # QUESTION GENERATION
    # ============================================================
    
    def generate_next_question(
        self, 
        state: CandidateState, 
        job_id: str,
        previous_answers: List[Dict[str, Any]] = []
    ) -> Optional[Dict[str, Any]]:
        """
        Generate the next question using the question generator with agent decisions.
        
        Agent decides:
        - Difficulty level
        - Which technical skill to test (if technical question)
        - Whether it's a follow-up or core question
        - [OPTIMIZATION] Deterministic templates for low-signal turns
        """
        # Determine if this is a core question or follow-up
        turn_no = state.question_count + 1
        
        # Core questions (1-8): Substantive evaluation
        if turn_no <= self.MIN_CORE_QUESTIONS:
            question_config = self.BASE_QUESTION_PLAN[turn_no - 1]
            q_type = question_config["type"]
            
            # Generate warmup question dynamically via LLM based on job role
            if q_type == "warmup":
                question_data = self.question_generator.generate_question(
                    turn_no=turn_no,
                    job_id=job_id,
                    previous_answers=[],
                    difficulty="easy",
                    candidate_state=state,
                    q_type_override=q_type  # PASS EXPLICIT TYPE
                )
                state.question_count = turn_no
                state.last_question = question_data["question"]
                state.last_question_type = q_type
                state.topics_covered.add(q_type)
                return question_data

            difficulty = self.decide_difficulty(state, turn_no)
            
            # If technical question, decide which skill
            if q_type == "technical":
                skill = self.select_technical_skill(state, job_id, turn_no)
                state.next_skill_to_test = skill
                state.skills_tested.add(skill)
                
                state.add_decision(Decision(
                    timestamp=datetime.utcnow().isoformat(),
                    question_number=turn_no,
                    decision_type="skill_selection",
                    action=f"selected_{skill}",
                    reasoning=f"Strategically selected {skill} from must-have skills",
                    context={"skills_tested": list(state.skills_tested)}
                ))
            
            # Generate question (LLM required)
            question_data = self.question_generator.generate_question(
                turn_no=turn_no,
                job_id=job_id,
                previous_answers=previous_answers,
                difficulty=difficulty,
                candidate_state=state,
                q_type_override=q_type  # PASS EXPLICIT TYPE FROM PLAN
            )
            
            # Update state
            state.question_count = turn_no
            state.last_question = question_data["question"]
            state.last_question_type = q_type
            state.topics_covered.add(q_type)
            
            # [FORCE TYPE] Ensure LLM drift doesn't change the intended plan type
            question_data["type"] = q_type
            
            return question_data
        
        
        # Follow-up/Remedial questions (9-13): Based on performance
        elif turn_no <= self.MAX_QUESTIONS - self.END_INTERVIEW_BUFFER:
            # CRITICAL FIX: Prevent infinite loops
            # If we've already asked candidate_questions, move to wrap-up
            if "candidate_questions" in state.topics_covered:
                # If wrap-up also done, end interview
                if "wrapup" in state.topics_covered:
                    return None
                return self._generate_wrapup(state, turn_no)
            
            decision = self.decide_termination(state)
            state.add_decision(decision)
            
            # If termination requested, jump to candidate Q&A
            if decision.action == "terminate":
                return self._generate_candidate_questions(state, turn_no)
            
            should_add, followup_type, reasoning = self.should_add_followup(state)
            
            # Force extension if decided to continue
            if not should_add and decision.action == "continue":
                should_add = True
                followup_type = "deep_dive"
                reasoning = "Extending interview to probe deeper capabilities"

            if should_add:
                state.add_decision(Decision(
                    timestamp=datetime.utcnow().isoformat(),
                    question_number=turn_no,
                    decision_type="add_followup",
                    action=followup_type,
                    reasoning=reasoning,
                    context={"last_score": state.last_score}
                ))
                
                difficulty = "hard"
                
                # FORCE TECHNICAL for follow-ups unless probing specific soft skill
                q_type_followup = "technical"
                
                # NEW: Second Chance Override
                if state.second_chance_category:
                    q_type_followup = state.second_chance_category
                    # [SAFETY] Prevent repetition - could add logic here to pick a DIFFERENT skill
                    print(f"[DEBUG] Triggering Second Chance question for category: {q_type_followup}")
                
                question_data = self.question_generator.generate_question(
                    turn_no=turn_no,
                    job_id=job_id,
                    previous_answers=previous_answers,
                    difficulty=difficulty,
                    candidate_state=state,
                    q_type_override=q_type_followup # PASS EXPLICIT TYPE
                )
                
                # Clear second chance flag after use
                state.second_chance_category = None
                
                state.question_count = turn_no
                state.last_question = question_data["question"]
                state.last_question_type = q_type_followup
                
                return question_data
            else:
                # No more follow-ups, move to candidate Q&A
                return self._generate_candidate_questions(state, turn_no)
        
        # Candidate Q&A phase (fallback for turn 13)
        elif turn_no == self.MAX_QUESTIONS - 1:
            if "candidate_questions" in state.topics_covered:
                return self._generate_wrapup(state, turn_no)
            return self._generate_candidate_questions(state, turn_no)
        
        # Wrap-up (always last, fallback for turn 15)
        elif turn_no == self.MAX_QUESTIONS:
            if "wrapup" in state.topics_covered:
                return None  # Interview already ended
            return self._generate_wrapup(state, turn_no)
        
        # Hard stop at MAX_QUESTIONS
        else:
            return None
    
    def _generate_candidate_questions(self, state: CandidateState, turn_no: int) -> Dict[str, Any]:
        """Generate candidate Q&A question"""
        question_data = {
            "question": "That covers all my questions. Do you have any questions for me about the role, the team, or the company?",
            "type": "candidate_questions",
            "rubric": {"mustMention": [], "goodToMention": [], "redFlags": []}
        }
        state.question_count = turn_no
        state.last_question = question_data["question"]
        state.last_question_type = "candidate_questions"
        state.topics_covered.add("candidate_questions")
        return question_data
    
    def generate_answer_to_candidate_question(self, candidate_question: str, job_id: str) -> str:
        """Generate LLM response to candidate's question about the role/company"""
        job_data = job_service.get_job(job_id)
        job_title = job_data.get('title', 'Position') if job_data else 'Position'
        
        try:
            response = self.question_generator.client.chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": f"""You are an AI interviewer for a {job_title} position.
                    
The candidate has asked you this question:
"{candidate_question}"

Provide a professional, helpful, and honest response. Keep it concise (2-3 sentences).
If you don't have specific information, be honest and suggest they follow up with the hiring manager.

Respond naturally and professionally."""
                }],
                model=self.question_generator.model_name,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[ERROR] Failed to generate answer to candidate question: {e}")
            return "That's a great question! The hiring manager will be able to provide more specific details about that during the next round of interviews."
    
    def _generate_wrapup(self, state: CandidateState, turn_no: int) -> Dict[str, Any]:
        """Generate wrap-up message"""
        question_data = {
            "question": "Thank you for your time today! We'll review your responses and get back to you with next steps shortly. Have a great day!",
            "type": "wrapup",
            "rubric": {"mustMention": [], "goodToMention": [], "redFlags": []}
        }
        state.question_count = turn_no
        state.last_question = question_data["question"]
        state.last_question_type = "wrapup"
        state.topics_covered.add("wrapup")
        return question_data

