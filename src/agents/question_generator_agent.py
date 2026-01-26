import os
from groq import Groq
from typing import Dict, Any, List
import json
from src.config import GROQ_API_KEY, GROQ_MODEL
from src.services.job_service import job_service

class QuestionGeneratorAgent:
    """LLM-powered agent to generate interview questions"""
    
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("Groq API Key (GROQ_API_KEY) is not set in QuestionGeneratorAgent!")
        # OPTIMIZATION: Added timeout to prevent hanging connections
        self.client = Groq(api_key=GROQ_API_KEY, timeout=15.0)
        self.model_name = GROQ_MODEL
    
    def generate_question(
        self, 
        turn_no: int, 
        job_id: str, 
        previous_answers: List[Dict[str, Any]],
        difficulty: str = "medium",
        candidate_state: Any = None
    ) -> Dict[str, Any]:
        """Generate next question based on interview flow with adaptive difficulty"""
        
        # Get job description from service
        job_data = job_service.get_job(job_id)
        if not job_data:
            job_data = {"title": "General Position", "level": "Entry", "must_have_skills": []}
        
        # Determine question type from plan
        question_plan = [
            "warmup", "behavioral", "behavioral", "motivation", 
            "technical", "technical", "scenario", "culture", 
            "candidate_questions", "wrapup"
        ]
        q_type = question_plan[turn_no - 1] if turn_no <= len(question_plan) else "technical"
        
        # Create prompt for LLM
        prompt = self._create_prompt(q_type, job_data, previous_answers, difficulty, candidate_state)
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                response_format={"type": "json_object"}
            )
            data = json.loads(chat_completion.choices[0].message.content)
            return data
        except Exception as e:
            import traceback
            print(f"[ERROR] LLM Question Generation Failed: {e}")
            traceback.print_exc()
            return self._fallback_question(q_type, job_data)
    
    def _create_prompt(
        self, 
        q_type: str, 
        job_data: Dict[str, Any], 
        previous_answers: List[Dict[str, Any]],
        difficulty: str = "medium",
        candidate_state: Any = None
    ) -> str:
        """Create optimized, concise prompt for question generation"""
        
        # SPECIAL HANDLING: Warmup questions should be catchy and engaging
        if q_type == 'warmup':
            job_title = job_data.get('title', 'Position')
            return f"""You are an energetic and professional interviewer for a {job_title} role.

Generate a CATCHY and ENGAGING warmup question to kick off the interview.
Respond using a valid JSON object.

CRITICAL RULES FOR WARMUP:
1. Make it welcoming but stimulating - not just "tell me about yourself"
2. Connect their background specifically to this {job_title} opportunity
3. Tone: Professional, enthusiastic, and curious
4. Avoid dense technical scenarios (no data dumps or specific numbers yet)
5. Aim for 30-50 words - enough to set a great stage

GOOD EXAMPLES (CATCHY):
- "Welcome! I've reviewed your background and I'm excited to dive in. To kick things off, what specific experiences have prepared you to tackle the challenges of a {job_title} role?"
- "It's great to connect with you! I'd love to hear the story of your career journey so far and what sparked your passion for becoming a {job_title}."
- "Hi there! To set the stage, could you bridge the gap between your past projects and why you see this {job_title} position as your next big move?"

BAD EXAMPLES (TOO SIMPLE OR TOO COMPLEX):
- "Tell me about yourself." (Too boring)
- "You have a 500GB database..." (Too technical/complex)
- "What is your experience?" (Too generic)

Output Format:
{{
    "question": "your catchy warmup question here",
    "type": "warmup",
    "rubric": {{
        "mustMention": ["background", "interest", "connection to role"],
        "goodToMention": ["passion", "specific experiences"],
        "redFlags": ["vague", "low energy", "negative"]
    }}
}}"""
        
        elif q_type == 'motivation':
            return f"""You are an interview for {job_title}.

Generate a MOTIVATION question to understand what drives the candidate.

CRITICAL RULES FOR MOTIVATION:
1. Focus on WHY they want this specific role/company
2. Ask about their career goals or what energizes them
3. NO "Tell me about a time..." (that is Behavioral)
4. NO technical scenarios (that is Technical)
5. Keep it professional but personal

Respond using a valid JSON object.

GOOD EXAMPLES:
- "What specifically about this {job_title} role at our company aligns with your career goals?"
- "What part of being a {job_title} do you find most energizing and why?"
- "We have a fast-paced environment. What kind of work culture allows you to do your best work?"

Output Format:
{{
    "question": "your motivation question here",
    "type": "motivation",
    "rubric": {{
        "mustMention": ["alignment", "interest"],
        "goodToMention": ["specific goals", "values"],
        "redFlags": ["just wants money", "no research"]
    }}
}}"""
        
        # OPTIMIZATION: Concise context for other question types
        job_title = job_data.get('title', 'Position')
        skills_str = ', '.join(job_data.get('must_have_skills', [])[:5])
        
        difficulty_notes = {
            "easy": "Focus on fundamentals, clear and supportive tone.",
            "medium": "Standard industry level, require specific examples.",
            "hard": "Advanced mastery, test deep expertise and edge cases."
        }
        
        # Build history context (last 3 turns)
        history = self._format_history(previous_answers)
        
        # Focus area for technical questions
        focus_area = ""
        if q_type == 'technical' and candidate_state and hasattr(candidate_state, 'next_skill_to_test'):
            focus_area = f"Target skill: {candidate_state.next_skill_to_test}"

        prompt = f"""You are an interviewer for {job_title}. 
Question Type: {q_type}. Difficulty: {difficulty} ({difficulty_notes.get(difficulty)}).
Skills Focus: {skills_str}. {focus_area}

Conversation History:
{history}

Generate a JSON object for the next question. 

CRITICAL DISTINCTION:
- Behavioral questions: Use STAR method (Situation, Task, Action, Result). Ask "Tell me about a time when..."
- Culture questions: Ask about preferences, values, and ideal work environments. NO storytelling. Examples: "What work environment brings out your best?", "How do you define a healthy team culture?"
- Motivation questions: Ask "WHY this role?", "Where do you see yourself?", "What drives you?". NO technical scenarios.

Criteria:
1. Dynamic, JD-specific question.
2. For Behavioral: Use STAR method.
3. For Culture: Ask for preferences/values (NOT past situations).
4. For Motivation: Ask about drivers/goals (NOT skills).
5. For Technical: Practical scenario-based (no generic theory).

Output Format:
{{
    "question": "string",
    "type": "{q_type}",
    "rubric": {{
        "mustMention": ["list"],
        "goodToMention": ["list"],
        "redFlags": ["list"]
    }}
}}"""
        return prompt
    
    def _format_history(self, turns: List[Dict[str, Any]]) -> str:
        """Format turn-based history for the prompt"""
        if not turns:
            return "No previous turns."
        
        # Only take last 5 turns to keep prompt small
        formatted = []
        for t in turns[-5:]:
            speaker = "Interviewer" if t["speaker"] == "agent" else "Candidate"
            formatted.append(f"{speaker}: {t['text']}")
        
        return "\n".join(formatted)
    
    def _fallback_question(self, q_type: str, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simple fallback questions"""
        job_title = job_data.get('title', 'Data Analyst') if job_data else 'Data Analyst'
        fallbacks = {
            "warmup": f"Welcome! To kick things off, I'd love to hear a bit about your journey. What specific experiences have prepared you for this {job_title} role?",
            "behavioral": "Tell me about a time you handled a difficult project deadline.",
            "technical": f"What are the most important tools you use for {job_title} tasks?",
            "motivation": f"Why are you interested in this {job_title} role specifically?",
            "culture": "How do you define a healthy team culture?"
        }
        return {
            "question": fallbacks.get(q_type, "Could you tell me more about your background?"),
            "type": q_type,
            "rubric": {"mustMention": [], "goodToMention": [], "redFlags": []}
        }
