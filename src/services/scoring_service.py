from datetime import datetime
from src.db.supabase_client import supabase

class ScoringService:
    """Handles interview scoring"""
    
    @staticmethod
    def save_scores(interview_id: str, technical: int, communication: int, culture: int, 
                   overall: int, recommendation: str, reasoning: dict):
        """Save interview scores"""
        data = {
            "interview_id": interview_id,
            "technical_score": technical,
            "communication_score": communication,
            "culture_score": culture,
            "overall_score": overall,
            "recommendation": recommendation,
            "reasoning": reasoning,
            "created_at": datetime.utcnow().isoformat()
        }
        supabase.table("interview_scores").insert(data).execute()
    
    @staticmethod
    def get_scores(interview_id: str):
        """Get scores for an interview"""
        response = supabase.table("interview_scores").select("*").eq("interview_id", interview_id).execute()
        return response.data[0] if response.data else None
