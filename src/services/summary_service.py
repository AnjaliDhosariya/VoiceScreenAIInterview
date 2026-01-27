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
        recommendation, reasoning = SummaryService._determine_recommendation(
            overall_score=scores.get("overall", 0), 
            num_questions=num_answers,
            scores=scores,
            evaluations=evaluations
        )
        
        return {
            "highlights": highlights,
            "concerns": concerns,
            "recommendation": recommendation,
            "recommendation_reasoning": reasoning,
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
    def _determine_recommendation(overall_score: int, num_questions: int, scores: Dict[str, Any] = None, 
                                 evaluations: List[Dict[str, Any]] = None) -> tuple[str, str]:
        """
        Determine recommendation based on multiple signals with detailed reasoning.
        
        Returns: (recommendation, reasoning)
        """
        # Extract additional signals
        technical_score = scores.get("technical", 0) if scores else 0
        communication_score = scores.get("communication", 0) if scores else 0
        culture_score = scores.get("culture", 0) if scores else 0
        
        # Count red/green flags from evaluations
        actual_red_flags = []
        improvements = []
        green_flags = []
        if evaluations:
            for eval_data in evaluations:
                actual_red_flags.extend(eval_data.get('red_flags', []))
                improvements.extend(eval_data.get('improvements', []))
                green_flags.extend(eval_data.get('strengths', []))
        
        red_flag_count = len([f for f in actual_red_flags if f and len(f) > 10])
        improvement_count = len([i for i in improvements if i and len(i) > 10])
        green_flag_count = len([g for g in green_flags if g and len(g) > 10])
        
        # ====================
        # REJECT CRITERIA
        # ====================
        
        # Critical: Severe performance
        if overall_score < 40: # Lowered from 45
            return "REJECT", f"Overall score too low ({overall_score}/100) - does not meet minimum bar"
        
        # Critical: Actual Red Flags (Major issues)
        if red_flag_count >= 4: # Increased from 3
            return "REJECT", f"Multiple critical red flags identified ({red_flag_count}) - severe gaps in core requirements"
        
        if red_flag_count >= 2 and overall_score < 50: # Only reject for 2 red flags if score is very weak
            return "REJECT", f"Multiple red flags ({red_flag_count}) combined with very weak performance ({overall_score}/100)"
        
        # Critical: Too many minor concerns when score is already weak
        if improvement_count >= 8 and overall_score < 50: # Increased threshold and lowered score trigger
            return "REJECT", f"Too many concerns identified ({improvement_count} improvements) with weak overall score ({overall_score}/100)"

        # Critical: Technical incompetence for technical roles
        if technical_score < 30 and technical_score > 0:  # Lowered from 35
            return "REJECT", f"Critical technical gaps (technical score: {technical_score}/100) - does not meet role requirements"
        
        # Early termination with poor performance
        if num_questions < 8:
            if overall_score < 50: # Lowered from 55
                if red_flag_count >= 1 or improvement_count >= 4:
                    return "REJECT", f"Early termination with weak performance ({overall_score}/100) and multiple concerns - insufficient potential"
                return "HOLD", f"Early termination with borderline performance ({overall_score}/100, {num_questions} questions) - need more signal"
            return "HOLD", f"Insufficient coverage ({num_questions} questions, need ≥8) despite decent score ({overall_score}/100) - require full assessment"
        
        # Complete interview with poor performance
        if num_questions >= 10 and overall_score < 45: # Lowered from 50
            return "REJECT", f"Completed {num_questions} questions but performance remains weak ({overall_score}/100) - not a fit"
        
        # ====================
        # PROCEED CRITERIA
        # ====================
        
        # Must have minimum coverage
        if num_questions >= 8 and overall_score >= 65: # Lowered threshold from 75 to 65
            # Additional validation checks
            checks_passed = 0
            reasons = []
            
            # Check 1: Technical strength
            if technical_score >= 65: # Lowered from 70
                checks_passed += 1
                reasons.append("solid technical skills")
            
            # Check 2: Communication strength
            if communication_score >= 65: # Lowered from 70
                checks_passed += 1
                reasons.append("clear communication")
            
            # Check 3: Positive signal ratio
            if green_flag_count >= red_flag_count:
                checks_passed += 1
                reasons.append("positive signal ratio")
            
            # Check disqualifiers
            # Logic: In longer interviews, more minor improvements are expected.
            # Only trigger HOLD if improvements are > 1.25x the number of turns.
            max_improvements = max(10, int(num_questions * 1.25))
            
            if red_flag_count >= 3: # Increased from 2
                return "HOLD", f"Potential candidate ({overall_score}/100) but has {red_flag_count} red flags - technical deep-dive recommended"
            
            # EXCEPTION: If overall score is excellent (>= 80), allow more improvements
            # High performers often get many nitpicky "improvements" from the LLM
            if overall_score >= 80:
                 max_improvements = max_improvements * 1.5
            
            if improvement_count >= max_improvements and overall_score < 80:
                return "HOLD", f"Good overall score ({overall_score}/100) but numerous improvement areas identified ({improvement_count}) - review specific feedback"
            
            if technical_score < 60 and technical_score > 0:
                return "HOLD", f"Good overall ({overall_score}/100) but technical gaps (technical: {technical_score}/100) - recommend technical deep-dive"
            
            # Need at least 2 of 3 validation checks for PROCEED
            if checks_passed >= 2:
                reason_str = ", ".join(reasons)
                return "PROCEED", f"Strong performance ({overall_score}/100 across {num_questions} questions) with {reason_str} - recommend next round"
            else:
                return "HOLD", f"Good overall score ({overall_score}/100) but mixed signals - needs more specific validation"
        
        # ====================
        # HOLD CRITERIA
        # ====================
        
        # Borderline performance with full coverage
        if num_questions >= 8:
            reasons = []
            
            # Technical-Communication imbalance
            if technical_score >= 75 and communication_score < 60:
                return "HOLD", f"Strong technical ({technical_score}/100) but communication concerns ({communication_score}/100) - assess client-facing readiness"
            
            if communication_score >= 75 and technical_score < 60 and technical_score > 0:
                return "HOLD", f"Strong communication ({communication_score}/100) but technical gaps ({technical_score}/100) - requires technical validation"
            
            # Borderline overall score
            if 60 <= overall_score < 75:
                if red_flag_count > green_flag_count:
                    return "HOLD", f"Moderate performance ({overall_score}/100) with more concerns than strengths - borderline candidate"
                
                # If score is close to 75 (e.g., 70-74), lean towards PROCEED if no red flags
                if overall_score >= 70 and red_flag_count == 0:
                     return "PROCEED", f"Solid performance ({overall_score}/100) with no red flags - recommend next round"
                     
                return "HOLD", f"Moderate performance ({overall_score}/100) across {num_questions} questions - additional assessment needed"
            
            # Low but not rejectable
            if overall_score < 60:
                return "HOLD", f"Below target performance ({overall_score}/100) - marginal fit, needs careful consideration"
        
        # Default: insufficient coverage
        return "HOLD", f"Insufficient interview coverage ({num_questions} questions, target ≥8) - need more signal before decision"
    
    @staticmethod
    def _areas_to_probe(concerns: List[str]) -> List[str]:
        """Suggest areas to probe"""
        return [f"Deep dive on: {concern}" for concern in concerns[:3]]
