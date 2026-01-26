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
                       rubric: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a candidate's answer"""
        
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
        
        # MANDATORY OPTIMIZATION: Skip LLM call for low-signal turns
        # These turns don't impact the core competence score
        if question_type.lower() in ["warmup", "candidate_questions", "wrapup"]:
            return {
                "technical": 5, "communication": 5, "structure": 5, "confidence": 5,
                "strengths": ["Completed turn"],
                "improvements": [],
                "brief_reasoning": "Deterministic score for low-signal turn orientation/conclusion."
            }

        # Add STAR structure checking for behavioral questions
        star_check = ""
        if question_type.lower() in ['behavioral', 'motivation', 'culture']:
            star_check = """
CRITICAL for behavioral questions - Check for STAR method:
- Situation: Does the answer describe a specific context?
- Task: Is the challenge/goal clearly stated?
- Action: Are specific actions taken described?
- Result: Is there a measurable outcome mentioned?

Deduct 3-4 points if answer lacks STAR structure. Score 3-5 if very vague (e.g., "I tried my best").
"""
        
        prompt = f"""You are an expert interviewer evaluating a candidate's answer.

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
1. Technical (if applicable) - correctness, depth, examples, accuracy
   - 8-10: Demonstrates mastery with specific examples
   - 5-7: Correct but lacks depth
   - 2-4: Very vague or partially incorrect
   - 0-1: Gibberish, nonsense, or refuses to answer

2. Communication - clarity, structure, conciseness
   - 8-10: Clear, well-structured, professional
   - 5-7: Understandable but could be clearer
   - 2-4: Vague, rambling, or unclear
   - 0-1: Gibberish, incoherent, or single word

3. Structure - organization, logical flow, STAR method
   - 8-10: Excellent structure, follows STAR if behavioral
   - 5-7: Some structure but missing elements
   - 2-4: No clear structure, very vague
   - 0-1: No structure, gibberish, or refuses to answer

4. Confidence - ownership, assertiveness, specificity
   - 8-10: Strong ownership with specific actions (e.g., "I implemented...")
   - 5-7: Moderate ownership (e.g., "I tried...")
   - 2-4: Passive language (e.g., "mostly adapted", "did my best")
   - 0-1: No ownership, gibberish, or avoids answering

IMPORTANT: Scores should vary based on answer quality. Avoid giving all identical scores.

Return ONLY a JSON object:
{{
    "technical": <0-10>,
    "communication": <0-10>,
    "structure": <0-10>,
    "confidence": <0-10>,
    "strengths": ["specific strength with evidence"],
    "improvements": ["specific area to improve"],
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
        
        # Heuristic 2: Mostly uppercase/random (>70% uppercase)
        uppercase_ratio = sum(1 for c in answer if c.isupper()) / max(char_count, 1)
        if uppercase_ratio > 0.7:
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
            # Simple scoring based on answer length
            score = min(10, max(2, word_count // 10))
        
        return {
            "technical": score,
            "communication": score,
            "structure": score,
            "confidence": score,
            "strengths": ["Provided a response"] if not is_gibberish else [],
            "improvements": ["Answer appears to be gibberish or incomplete"] if is_gibberish else ["Could elaborate more"],
            "brief_reasoning": "Gibberish or invalid response" if is_gibberish else "Answer evaluated based on length and completeness"
        }
    
    def aggregate_scores(self, evaluations: list) -> Dict[str, int]:
        """Aggregate scores from all evaluations"""
        if not evaluations:
            return {
                "technical": 0,
                "communication": 0,
                "culture": 0,
                "overall": 0
            }
        
        # Calculate averages
        technical_scores = [e.get("technical", 0) for e in evaluations]
        communication_scores = [e.get("communication", 0) for e in evaluations]
        structure_scores = [e.get("structure", 0) for e in evaluations]
        confidence_scores = [e.get("confidence", 0) for e in evaluations]
        
        technical_avg = sum(technical_scores) / len(technical_scores)
        communication_avg = sum(communication_scores) / len(communication_scores)
        culture_avg = (sum(structure_scores) + sum(confidence_scores)) / (2 * len(evaluations))
        
        overall = (technical_avg + communication_avg + culture_avg) / 3
        
        return {
            "technical": int(technical_avg * 10),
            "communication": int(communication_avg * 10),
            "culture": int(culture_avg * 10),
            "overall": int(overall * 10)
        }
