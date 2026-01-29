import os
from groq import Groq
from typing import Dict, Any, List
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
        if self._is_gibberish(answer, question_type):
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

ROLE-AWARE GRADING STANDARDS:
- FOR JUNIOR/FRESHER: Prioritize **Logic, Structure, and Communication**. 
    - **Mastery Reward**: If a Junior candidate demonstrates knowledge of advanced concepts (e.g., expert-level methodologies, complex industry-specific frameworks, or sophisticated problem-solving tools) that exceed typical entry-level expectations, **REWARD THEM IN THE 8-9 RANGE**.
    - **Logical Pass**: If they explain their baseline process clearly and use a logical structure (like STAR), give them a score of 7.5-8 even if they don't mention advanced tools or techniques.
- **COMMUNICATION & STRUCTURE REWARD**: If a candidate (Junior or Senior) uses the **STAR method perfectly** or provides an **exceptionally well-organized, step-by-step professional explanation**, **YOU MUST AWARD A SCORE OF 8.5-9.5** in Communication and Structure.
    - **NO "SAFE" SCORING**: Do not default to a "safe" 7.0-7.5 if the structure is excellent. A well-organized answer is a major differentiator; reward it accordingly.
- FOR SENIOR/EXPERIENCED: Maintain a very high technical bar. Expect deep-dives into edge cases, high-level strategy, and complex optimizations relevant to the field.

CRITICAL QUALITY RULES:
1. ONLY flag an answer as "gibberish" or "invalid" if it is truly random characters or completely unrelated to human language.
2. DO NOT flag technical terminology, industry jargon, or acronyms as gibberish.
3. Be lenient with long, professional explanations.

Evaluate the answer on a scale of 0-10:
1. Technical (if applicable) - correctness, complexity, accuracy
   - 9-10: Exceptional; expert-level depth with absolute precision within the domain.
   - 8-9: Advanced; shows depth beyond target level (Excellent for Juniors).
   - 7-7.5: Solid; core concepts handled professionally (Strong Pass).
   - 5-6: Fair; correct baseline but brief or lacks depth.
   - 0-4: Weak/Failed; incorrect or nonsensical.

2. Communication - clarity, structure, professional tone
   - 9-10: Exceptional; extremely well-articulated, concise, and professional. 
   - 8.5-9.5: Excellent; mandated for perfect STAR usage or exceptional organization.
   - 7-8: Clear; easy to follow (Strong Pass).
   - 5-6: Understandable; gets the point across but may ramble.
   - 0-4: Poor.

3. Structure - organization, logical flow, STAR method (if behavioral)
   - 9-10: Perfect flow; masterfully organized.
   - 8.5-9.5: Excellent; clear logical steps or **Perfect STAR method**.
   - 7-8: Good; mostly logical (Solid).
   - 0-6: Loose or No structure.

4. Confidence - ownership and assertiveness
   - 8-10: High; strong ownership (e.g., "I took lead", "I decided").
   - 6-7: Moderate; appropriate for most roles.
   - 3-5: Low; passive or hesistant.
   - 0-2: Lacks ownership.

SCORING PHILOSOPHY:
- **FOR BEHAVIORAL QUESTIONS**: Focus **SOLELY** on Logic, STAR Structure, and Communication. If they use STAR, they **MUST** get an 8.5-9.5 regardless of technical depth.
- **FOR TECHNICAL QUESTIONS**: Reward depth and use of specific industry-standard tools or robust patterns. High detail is a major strength.
- **FOR ALL QUESTIONS**: Be generous and supportive. If the answer is clear, accurate, and professional for the {job_level} level, give an 8 or 9.
- DO NOT penalize for "missing more depth" if the answer is already sufficient for the target level.
- 5-6 is only for incomplete, very brief, or vague answers.

Return ONLY a JSON object:
{{
    "technical": <0-10>,
    "communication": <0-10>,
    "structure": <0-10>,
    "confidence": <0-10>,
    "strengths": ["specific strength with evidence"],
    "improvements": ["Only include critical technical or structural gaps. DO NOT include generic advice like 'elaborate more' or 'be more specific' if the answer already satisfies the prompt professionally. Leave EMPTY for strong (8-10) answers."],
    "red_flags": ["If the answer is irrelevant or canned, you MUST include the EXACT string 'Irrelevant answer' here. Also include CRITICAL issues, dealbreakers, or severe technical errors"],
    "brief_reasoning": "One sentence explaining the score. If answer is irrelevant, state 'Irrelevant answer' explicitly."
}}
SCORING MANDATE (CRITICAL):
- RELEVANCE GATE: If the answer is "canned" or irrelevant, YOU MUST score 0-1 for Technical and add 'Irrelevant answer' to red_flags.
- DO NOT award points for structure/STAR if the content is irrelevant.
- NEGATIVE EXAMPLE: Question: "Explain React Caching", Answer: "I am a hard worker who loves teams." -> Result: {{"technical": 0, "red_flags": ["Irrelevant answer"], "brief_reasoning": "Answer did not address caching."}}
- DEEP DIVE REWARD (JUNIOR/FRESHER): If a candidate at this level provides a detailed, conceptual deep-dive (e.g. explaining statistical implications of missing data or complex database aggregations), **YOU MUST AWARD 8.5-9.5**.
- NO SEARCHING FOR IMPROVEMENTS: If an answer is professionally sufficient, leave "improvements" EMPTY. Do not search for minor flaws to fill space.
- DO NOT hallucinate technical depth if the answer doesn't contain any specific technical responses to the prompt.
"""
        
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
    
    def quick_evaluate(self, question: str, answer: str, question_type: str, job_level: str = "Mid") -> Dict[str, Any]:
        """High-speed, low-latency evaluation for adaptive difficulty logic"""
        # Skip for metadata turns
        if question_type.lower() in ["warmup", "candidate_questions", "wrapup"]:
            return {"technical": 5, "communication": 5, "structure": 5, "confidence": 5, "overall": 5}

        if self._is_gibberish(answer, question_type):
            return {"technical": 0, "communication": 0, "structure": 0, "confidence": 0, "overall": 0}

        prompt = f"""Rate this interview answer from 0-10 for a {job_level} level position.
Question Type: {question_type}
Question: {question}
Answer: {answer}

SCORING RULES:
- 7-10: CORRECT and PROFESSIONAL (Role-appropriate quality).
- **For Juniors**: Prioritize Logic and STAR structure. 7-8 is a standard PASS.
- **For Seniors**: High bar; expect depth and advanced concepts.
- 5-6: BASIC or BRIEF (Max 5 if only 1-2 sentences).
- 0-4: VAGUE/Inaccurate.

Return ONLY a JSON object: {{"score": <number>}}"""

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
                response_format={"type": "json_object"},
                max_tokens=20 # Hard limit for speed
            )
            data = json.loads(chat_completion.choices[0].message.content)
            score_raw = data.get("score", 5)
            try:
                score = float(score_raw)
            except (ValueError, TypeError):
                score = 5.0

            # Map single score to all dimensions for state compatibility
            return {
                "technical": score,
                "communication": score,
                "structure": score,
                "confidence": score,
                "overall": score
            }
        except:
            return {"technical": 5, "communication": 5, "structure": 5, "confidence": 5, "overall": 5}

    def _parse_evaluation(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM evaluation response"""
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            json_str = response_text[start:end]
            data = json.loads(json_str)
            
            # Normalize scores to floats
            for field in ["technical", "communication", "structure", "confidence"]:
                if field in data:
                    try:
                        data[field] = float(data[field])
                    except (ValueError, TypeError):
                        data[field] = 5.0
                else:
                    data[field] = 5.0
                    
            return data
        except:
            return self._fallback_evaluation("")
    
    def _is_gibberish(self, answer: str, question_type: str = "technical") -> bool:
        """Detect gibberish/nonsense answers using multiple heuristics"""
        if not answer or not answer.strip():
            return True
        
        # VALIDATION FIX: Allow very short answers for non-substantive types
        if question_type.lower() in ["candidate_questions", "wrapup", "warmup", "consent"]:
            # Even "no" or "yes" is valid here.
            return False
            
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
            # Reduced from 0.2 to 0.15 to allow for very dense technical jargon
            if vowel_ratio < 0.15: 
                return True
        
        # Heuristic 4: Contains keyboard mash patterns (now more strict)
        nonsense_patterns = ['asdfg', 'qwerty', 'zxcvb'] # Longer strings
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
            technical_avg = self._calculate_smoothed_avg([e.get("technical", 0) for e in tech_turns])
        else:
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

    def _calculate_smoothed_avg(self, scores: List[float]) -> float:
        """Low prioritize a single bad score if candidate recovered (3+ answers in category)."""
        if len(scores) < 3:
            return sum(scores) / len(scores) if scores else 0.0
        min_score = min(scores)
        others = [s for s in scores if s != min_score]
        if len(others) < len(scores) - 1: others.append(min_score) 
        avg_others = sum(others) / len(others)
        if avg_others - min_score > 4.0:
            return (avg_others * 0.7) + (min_score * 0.3)
        return sum(scores) / len(scores)
