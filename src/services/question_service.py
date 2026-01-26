from datetime import datetime
from typing import List, Dict, Any
from src.db.supabase_client import supabase

class QuestionService:
    """Handles interview turns (questions and answers)"""
    
    @staticmethod
    def save_turn(interview_id: str, turn_no: int, speaker: str, text: str):
        """Save a turn (agent question or candidate answer)"""
        data = {
            "interview_id": interview_id,
            "turn_no": turn_no,
            "speaker": speaker,
            "text": text,
            "timestamp": datetime.utcnow().isoformat()
        }
        supabase.table("interview_turns").insert(data).execute()
    
    @staticmethod
    def get_turns(interview_id: str) -> List[Dict[str, Any]]:
        """Get all turns for an interview"""
        response = supabase.table("interview_turns").select("*").eq("interview_id", interview_id).order("turn_no").execute()
        return response.data if response.data else []
    
    @staticmethod
    def get_last_turn_number(interview_id: str) -> int:
        """Get the last turn number"""
        response = supabase.table("interview_turns").select("turn_no").eq("interview_id", interview_id).order("turn_no", desc=True).limit(1).execute()
        return response.data[0]["turn_no"] if response.data else 0
