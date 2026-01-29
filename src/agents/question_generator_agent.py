import os
from groq import Groq
from typing import Dict, Any, List, TYPE_CHECKING
import json
from src.config import GROQ_API_KEY, GROQ_MODEL
from src.services.job_service import job_service
from src.agents.candidate_state import CandidateState

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
        candidate_state: Any = None,
        q_type_override: str = None # NEW: specific type requested by controller
    ) -> Dict[str, Any]:
        """Generate next question based on interview flow with adaptive difficulty"""
        
        # Get job description from service
        job_data = job_service.get_job(job_id)
        if not job_data:
            job_data = {"title": "General Position", "level": "Entry", "must_have_skills": []}
        
        # Determine question type: Use override if provided, else default to technical
        # The planning logic is now centralized in AgenticInterviewer
        q_type = q_type_override if q_type_override else "technical"
        
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
        
        # Common context
        job_title = job_data.get('title', 'Position')
        job_level = job_data.get('level', 'Mid-Level')

        # Shared personalization rule
        personalization_rule = """
CONTEXT CONNECTIVITY RULE:
- Look at the "Conversation History" for specific facts (e.g., an internship, a project, a specific tool, or an area of interest mentioned by the candidate).
- Whenever possible, BRIDGE the next question to these facts to make the interview feel adaptive and connected (e.g., "Earlier you mentioned your internship at X. Could you tell me about a time there where...").
- Do not repeat facts, but use them to frame the next challenge.
"""

        # SPECIAL HANDLING: Warmup questions should be catchy and engaging
        if q_type == 'warmup':
            return f"""You are an energetic and professional interviewer for a {job_level} {job_title} role.

Generate a CATCHY and ENGAGING warmup question to kick off the interview.
Respond using a valid JSON object.

CRITICAL RULES FOR WARMUP:
1. Make it welcoming but stimulating - not just "tell me about yourself"
2. Connect their background specifically to this {job_title} opportunity
3. Tone: Professional, enthusiastic, and curious
4. Avoid dense technical scenarios (no data dumps or specific numbers yet)
5. Aim for 30-50 words - enough to set a great stage

GOOD EXAMPLES (CATCHY):
- "To kick things off, what specific experiences have prepared you to tackle the challenges of a {job_title} role?"
- "It's great to connect with you! I'd love to hear the story of your career journey so far and what sparked your passion for becoming a {job_title}."
- "Hi there! To set the stage, could you bridge the gap between your past projects and why you see this {job_title} position as your next big move?"

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
            return f"""You are an interviewer for a {job_level} {job_title}.

Generate a MOTIVATION question to understand what drives the candidate.

{personalization_rule}

CRITICAL RULES FOR MOTIVATION:
1. Focus on WHY they want this specific role/company
2. Ask about their career goals or what energizes them
3. NO "Tell me about a time..." (that is Behavioral)
4. NO technical scenarios (that is Technical)
5. DO NOT ask about their background/experience (already covered in warmup)
6. Keep it professional but personal

Respond using a valid JSON object.

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
        
        elif q_type == 'behavioral':
             return f"""You are an interviewer for a {job_level} {job_title}.

Generate a BEHAVIORAL question using the STAR method (Situation, Task, Action, Result).

{personalization_rule}

CRITICAL RULES FOR BEHAVIORAL:
1. Ask "Tell me about a time when..." or "Describe a situation where..."
2. Focus on SOFT SKILLS: Conflict resolution, Leadership, Teamwork, Adaptability, Ownership, Integrity.
3. DO NOT ask domain-specific skills questions (e.g., "Tell me about a time you used a specific tool").
4. DO NOT ask about code or tools. Focus on PEOPLE and PROCESS logic.

Respond using a valid JSON object.

Output Format:
{{
    "question": "your behavioral question here",
    "type": "behavioral",
    "rubric": {{
        "mustMention": ["STAR structure", "specific example", "outcome"],
        "goodToMention": ["learning", "collaboration"],
        "redFlags": ["blaming others", "vague", "no result"]
    }}
}}"""

        elif q_type == 'culture':
            return f"""You are an interviewer for a {job_level} {job_title}.

Generate a CULTURE and VALUES question to see if the candidate aligns with a high-performing team.

{personalization_rule}

CRITICAL RULES FOR CULTURE:
1. Focus on PREFERENCES and VALUES (e.g., communication style, team environment, feedback).
2. NO "Tell me about a time when..." (that is Behavioral).
3. NO technical scenarios (that is Technical/Scenario).
4. Tone: Collaborative, observant, and professional.

Respond using a valid JSON object.

Output Format:
{{
    "question": "your culture question here",
    "type": "culture",
    "rubric": {{
        "mustMention": ["preferences", "team alignment"],
        "goodToMention": ["communication", "growth mindset"],
        "redFlags": ["toxic traits", "prefers working in total isolation"]
    }}
}}"""

        elif q_type == 'scenario':
            return f"""You are an interviewer for a {job_level} {job_title}.

Generate a SCENARIO-based Case Study question. This should be a 'Problem Solving' challenge.

{personalization_rule}

CRITICAL RULES FOR SCENARIO:
1. Present a HYPOTHETICAL business or professional crisis (e.g., "A critical deadline is at risk", "A key resource is unavailable", "A major stakeholder changed requirements").
2. Ask "How would you handle this?" or "Walk me through your first 3 steps."
3. Focus on SYSTEM-LEVEL thinking and prioritization.
4. DO NOT ask generic technical questions like "How do you use SQL?". Give a complex context.

Respond using a valid JSON object.

Output Format:
{{
    "question": "your scenario question here",
    "type": "scenario",
    "rubric": {{
        "mustMention": ["prioritization", "structured approach", "communication"],
        "goodToMention": ["scalability", "risk mitigation"],
        "redFlags": ["panics", "no structured plan", "ignores stakeholders"]
    }}
}}"""
        
        # Context for TECHNICAL questions
        skills_str = ', '.join(job_data.get('must_have_skills', [])[:5])
        
        difficulty_notes = {
            "easy": "Focus on fundamentals, clear and supportive tone.",
            "medium": "Standard industry level, require specific examples.",
            "hard": "Advanced mastery, test deep expertise and edge cases."
        }
        
        # Build history context
        history = self._format_history(previous_answers)
        
        # Focus area for technical questions
        focus_area = ""
        if q_type == 'technical' and candidate_state and hasattr(candidate_state, 'next_skill_to_test'):
            focus_area = f"Target skill: {candidate_state.next_skill_to_test}"

        topics_covered = getattr(candidate_state, 'topics_covered', '') if candidate_state else ''

        prompt = f"""You are an interviewer for a {job_level} {job_title}. 
Question Type: {q_type}. Difficulty: {difficulty} ({difficulty_notes.get(difficulty)}).
Skills Focus: {skills_str}. {focus_area}
Previous Topics Covered: {topics_covered}

{personalization_rule}

DIVERSITY & ANTI-REPETITION RULES:
1. DO NOT ask about a topic/skill if it appears in "Previous Topics Covered".
2. DO NOT repeat the same Scenario structure.
3. VARY the context: Use different industries and data problems.

CRITICAL: DO NOT ask about candidate's background overview - this was already covered in warmup.

Conversation History:
{history}

CRITICAL: DO NOT repeat topics confirmed in history. 
Seek depth in UNTESTED areas of the job description or BRIDGE to specific details mentioned in the Conversation History for a deeper probe.

Generate a JSON object for the next question. 
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
        job_title = job_data.get('title', 'Professional Role') if job_data else 'Professional Role'
        fallbacks = {
            "warmup": f"Welcome! To kick things off, I'd love to hear a bit about your journey. What specific experiences have prepared you for this {job_title} role?",
            "behavioral": "Tell me about a time you handled a difficult project deadline.",
            "technical": f"What are the most important industry-standard tools or methodologies you use for {job_title} tasks?",
            "motivation": f"Why are you interested in this {job_title} role specifically?",
            "culture": "How do you define a healthy team culture?"
        }
        return {
            "question": fallbacks.get(q_type, "Could you tell me more about your background?"),
            "type": q_type,
            "rubric": {"mustMention": [], "goodToMention": [], "redFlags": []}
        }
