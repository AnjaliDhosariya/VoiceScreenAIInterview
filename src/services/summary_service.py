from typing import List, Dict, Any
from src.services.question_service import QuestionService

class SummaryService:
    """Generates interview summaries and recommendations"""
    
    @staticmethod
    def generate_summary(interview_id: str, scores: Dict[str, Any], turns: List[Dict[str, Any]], 
                        evaluations: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate executive summary from interview"""
        
        # Extract candidate turns
        candidate_turns = [t for t in turns if t["speaker"] == "candidate"]
        
        # Generate highlights and concerns based on scores and evaluations
        highlights = SummaryService._generate_highlights(scores, evaluations)
        concerns = SummaryService._generate_concerns(scores, evaluations, candidate_turns)
        
        # Determine recommendation
        num_answers = len(candidate_turns)
        recommendation = SummaryService._determine_recommendation(
            scores.get("overall", 0), 
            num_answers
        )
        
        return {
            "highlights": highlights,
            "concerns": concerns,
            "recommendation": recommendation,
            "num_questions_answered": num_answers,
            "areas_to_probe": SummaryService._areas_to_probe(concerns)
        }
    
    @staticmethod
    def _generate_highlights(scores: Dict[str, Any], evaluations: List[Dict[str, Any]]) -> List[str]:
        """Generate highlights from actual evaluations"""
        highlights = []
        
        if evaluations:
            for eval_data in evaluations:
                strengths = eval_data.get('strengths', [])
                for strength in strengths:
                    if strength and len(strength) > 10 and strength not in highlights:
                        highlights.append(strength)
        
        # Fallback to score-based
        if len(highlights) < 2:
            if scores.get("technical", 0) >= 70:
                highlights.append("Demonstrated solid technical grasp of core concepts")
            if scores.get("communication", 0) >= 70:
                highlights.append("Maintained clear and professional communication")
        
        return highlights[:5]
    
    @staticmethod
    def _generate_concerns(scores: Dict[str, Any], evaluations: List[Dict[str, Any]], turns: List[Any]) -> List[str]:
        """Generate concerns from actual evaluations"""
        concerns = []
        
        if evaluations:
            for eval_data in evaluations:
                improvements = eval_data.get('improvements', [])
                for improvement in improvements:
                    if improvement and len(improvement) > 10 and improvement not in concerns:
                        concerns.append(improvement)
        
        # Fallback to score-based
        if len(concerns) < 1:
            if scores.get("technical", 0) < 60:
                concerns.append("Limited depth shown in technical explanations")
            if scores.get("communication", 0) < 60:
                concerns.append("Communication could be more structured")
            
        # Add termination note if too few questions
        if len(turns) < 10: 
            concerns.append("Interview terminated early - limited signal gathered")
            
        return concerns[:5]
    
    @staticmethod
    def _determine_recommendation(overall_score: int, num_questions: int) -> str:
        """Determine recommendation based on score and completion"""
        
        # Strong performers should proceed regardless of question count
        if overall_score >= 75:
            return "PROCEED"
        
        # For lower scores, consider interview length
        if num_questions < 10:
            # Early termination with decent scores: HOLD for further assessment
            if overall_score >= 60:
                return "HOLD"
            return "REJECT"
        
        # Full interview completed
        if overall_score >= 60:
            return "HOLD"
        return "REJECT"
    
    @staticmethod
    def _areas_to_probe(concerns: List[str]) -> List[str]:
        """Suggest areas to probe"""
        return [f"Deep dive on: {concern}" for concern in concerns[:3]]
