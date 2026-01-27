import os
from groq import Groq
from typing import Dict, Any
import json
from src.config import GROQ_API_KEY, GROQ_MODEL

class EvaluatorAgent:
    """LLM-powered agent to evaluate candidate answers"""
    
    def __init__(self):
        if not GROQ_API_KEY:
            raise ValueError("Groq API Key (GROQ_API_KEY) is not set in EvaluatorAgent!")
        # OPTIMIZATION: Added timeout
        self.client = Groq(api_key=GROQ_API_KEY, timeout=15.0)
        self.model_name = GROQ_MODEL
    
    def evaluate_answer(self, question: str, answer: str, question_type: str, 
                       rubric: Dict[str, Any], job_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Evaluate a candidate's answer"""
        
        # MANDATORY OPTIMIZATION: Skip LLM call for low-signal turns
        # Check this FIRST so we don't flag "No" or "I'm good" as gibberish for these types
        if question_type.lower() in ["warmup", "candidate_questions", "wrapup"]:
            return {
                "technical": 5, "communication": 5, "structure": 5, "confidence": 5,
                "strengths": ["Completed turn"],
                "improvements": [],
                "brief_reasoning": "Deterministic score for low-signal turn orientation/conclusion."
            }

        # CRITICAL: Pre-filter gibberish BEFORE LLM call (bypasses lenient LLM)
        if self._is_gibberish(answer):
            return {
                "technical": 0,
                "communication": 0,
                "structure": 0,
                "confidence": 0,
                "strengths": [],
                "improvements": ["Answer appears to be gibberish, random characters, or completely invalid"],
                "brief_reasoning": "Gibberish or nonsensical response detected"
            }
        
        # Add STAR structure checking ONLY for behavioral questions
        star_check = ""
        if question_type.lower() == 'behavioral':
            star_check = """
CRITICAL: This is a BEHAVIORAL question. Check for STAR method:
- Situation: Does the answer describe a specific context?
- Task: Is the challenge/goal clearly stated?
- Action: Are specific actions taken described?
- Result: Is there a measurable outcome mentioned?

Deduct 3-4 points if answer lacks STAR structure. Score 3-5 if very vague.
"""
        else:
            star_check = """
NOTE: This is NOT a behavioral question. DO NOT look for or penalize for lack of STAR structure.
Reward clarity, technical accuracy, and professional conciseness.
"""
        
        if job_data is None:
            job_data = {}
            
        job_title = job_data.get('title', 'Candidate')
        job_level = job_data.get('level', 'Mid')
        skills_list = job_data.get('must_have_skills', [])
        skills_str = ', '.join(skills_list[:5]) if skills_list else "general skills"

        prompt = f"""You are an expert interviewer evaluating a candidate's answer for a {job_title} position ({job_level} level).
        Skills Focus: {skills_str}

Question Type: {question_type}
Question: {question}
Candidate Answer: {answer}

Evaluation Rubric:
- Must Mention: {rubric.get('mustMention', [])}
- Good to Mention: {rubric.get('goodToMention', [])}
- Red Flags: {rubric.get('redFlags', [])}

{star_check}

CRITICAL: Detect gibberish and non-answers:
- Gibberish (random letters like "EDNRHCNHTVY", "RTRY"): Score 0-1 on ALL dimensions
- One-word answers or "I don't know": Score 0-2
- Extremely vague answers with no specifics: Score 1-3

Evaluate the answer on a scale of 0-10:
1. Technical (if applicable) - correctness, complexity, accuracy
   - 9-10: Mastery; expert-level depth, handles edge cases
   - 7-8: Solid; correctly answers and provides good examples (PROCEED level)
   - 5-6: Fair; correct but brief or lacks specific detail/depth
   - 2-4: Weak; partially incorrect or very vague
   - 0-1: Failed; non-answer or incorrect

2. Communication - clarity, structure, professional tone
   - 9-10: Exceptional; extremely well-articulated, concise, and professional
   - 7-8: Clear; easy to follow, well-structured (PROCEED level)
   - 5-6: Understandable; gets the point across but may ramble or be too brief
   - 2-4: Poor; difficult to follow or unprofessional
   - 0-1: Incoherent or one-word answers

3. Structure - organization, logical flow, STAR method (if behavioral)
   - 8-10: Perfect flow; clearly uses STAR for behavioral
   - 6-7: Good flow; mostly logical (PROCEED level)
   - 3-5: Loose structure; jumps around or misses key context
   - 0-2: No structure

4. Confidence - ownership and assertiveness
   - 8-10: High; strong ownership (e.g., "I took lead", "I decided")
   - 6-7: Moderate; appropriate for most roles (PROCEED level)
   - 3-5: Low; passive or hesistant
   - 0-2: Lacks ownership

SCORING PHILOSOPHY:
- Be generous and supportive. If the candidate provides a clear, technically accurate, and professional answer, they SHOULD receive an 8 or 9.
- Reward technical depth: If the candidate mentions specific industry-standard tools, optimizations, or robust patterns (e.g., dbt, Airflow, MERGE logic, Indexing, STAR method), GIVE a 9 or 10. High detail is a major strength.
- Reward structure: A candidate who uses the STAR method (Situation, Task, Action, Result) for behavioral questions or a structured "step-by-step" approach for technical questions SHOULD get an 8-10.
- DO NOT penalize for "missing more depth" if the answer provided is already correct and professionally sufficient for the target level ({job_level}).
- 7 is for "Correct but basic" - it is a strong PASSING score.
- 5-6 is only for answers that are incomplete, very brief, or vague.

Return ONLY a JSON object:
{{
    "technical": <0-10>,
    "communication": <0-10>,
    "structure": <0-10>,
    "confidence": <0-10>,
    "strengths": ["specific strength with evidence"],
    "improvements": ["ONLY key areas to improve. Leave EMPTY if answer is strong (8-10). Do not nitpick."],
    "red_flags": ["CRITICAL issues, dealbreakers, or severe technical errors"],
    "brief_reasoning": "One sentence explaining the score"
}}"""
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                model=self.model_name,
                response_format={"type": "json_object"}
            )
            result = self._parse_evaluation(chat_completion.choices[0].message.content)
            return result
        except Exception as e:
            # Fallback evaluation
            return self._fallback_evaluation(answer)
    
    def _parse_evaluation(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM evaluation response"""
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            json_str = response_text[start:end]
            data = json.loads(json_str)
            return data
        except:
            return self._fallback_evaluation("")
    
    def _is_gibberish(self, answer: str) -> bool:
        """Detect gibberish/nonsense answers using multiple heuristics"""
        if not answer or not answer.strip():
            return True
        
        word_count = len(answer.split())
        char_count = len(answer.strip())
        
        # Heuristic 1: Very short answers (≤2 words or <10 chars)
        if word_count <= 2 or char_count < 10:
            return True
        
        # Heuristic 2: Mostly uppercase/random (Only check if answer is long enough)
        if char_count > 50:
            uppercase_ratio = sum(1 for c in answer if c.isupper()) / char_count
            if uppercase_ratio > 0.85: # Increased from 0.7 to allow for SQL/Acronyms
                return True
        
        # Heuristic 3: Very low vowel ratio (gibberish like "RTRY" has few vowels)
        vowels = set('aeiouAEIOU')
        alpha_chars = [c for c in answer if c.isalpha()]
        if alpha_chars:
            vowel_ratio = sum(1 for c in alpha_chars if c in vowels) / len(alpha_chars)
            if vowel_ratio < 0.2:  # Less than 20% vowels
                return True
        
        # Heuristic 4: Contains common nonsense patterns
        nonsense_patterns = ['asdf', 'qwer', 'zxcv', 'hjkl', 'rtyu']
        answer_lower = answer.lower()
        if any(pattern in answer_lower for pattern in nonsense_patterns):
            return True
        
        return False
    
    def _fallback_evaluation(self, answer: str) -> Dict[str, Any]:
        """Fallback evaluation based on simple heuristics"""
        word_count = len(answer.split())
        char_count = len(answer.strip())
        
        # Detect gibberish: very short, single word, or mostly uppercase/random
        is_gibberish = (
            word_count <= 2 or 
            char_count < 10 or
            (sum(1 for c in answer if c.isupper()) / max(char_count, 1)) > 0.7  # >70% uppercase
        )
        
        if is_gibberish:
            # Gibberish or non-answer: score 0-1
            score = 0
        else:
            # Simple scoring based on answer length - default to neutral 5 for non-gibberish
            score = min(10, max(5, word_count // 5)) 
        
        return {
            "technical": score,
            "communication": score,
            "structure": score,
            "confidence": score,
            "strengths": ["Provided a response"] if not is_gibberish else [],
            "improvements": ["Could elaborate more"] if not is_gibberish else [],
            "red_flags": ["Answer appears to be gibberish or incomplete"] if is_gibberish else [],
            "brief_reasoning": "Gibberish or invalid response" if is_gibberish else "Answer evaluated based on length and completeness"
        }
    
    def aggregate_scores(self, evaluations: list) -> Dict[str, int]:
        """Aggregate scores from all evaluations with category-specific weighting"""
        if not evaluations:
            return {"technical": 0, "communication": 0, "culture": 0, "overall": 0}
        
        # Technical score: Only from technical/scenario questions
        tech_turns = [e for e in evaluations if e.get("type", "").lower() in ["technical", "scenario"]]
        if tech_turns:
            technical_avg = sum(e.get("technical", 0) for e in tech_turns) / len(tech_turns)
        else:
            # Fallback to general tech score if no explicit tech turns labeled
            technical_avg = sum(e.get("technical", 0) for e in evaluations) / len(evaluations)
            
        # Communication: All turns matter
        communication_avg = sum(e.get("communication", 0) for e in evaluations) / len(evaluations)
        
        # Culture: Derived from structure and confidence
        culture_avg = (sum(e.get("structure", 0) for e in evaluations) + 
                       sum(e.get("confidence", 0) for e in evaluations)) / (2 * len(evaluations))
        
        overall = (technical_avg + communication_avg + culture_avg) / 3
        
        return {
            "technical": int(technical_avg * 10),
            "communication": int(communication_avg * 10),
            "culture": int(culture_avg * 10),
            "overall": int(overall * 10)
        }
