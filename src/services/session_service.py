import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from src.db.supabase_client import supabase
from tenacity import retry, stop_after_attempt, wait_exponential

class SessionService:
    """Handles interview session database operations"""
    
    @staticmethod
    def check_active_interview(candidate_id: str) -> Optional[str]:
        """
        Check if candidate has an active interview.
        Returns interview_id if exists, None otherwise.
        """
        response = supabase.table("interview_sessions")\
            .select("id")\
            .eq("candidate_id", candidate_id)\
            .in_("status", ["CREATED", "INTERVIEW_IN_PROGRESS"])\
            .execute()
        
        return response.data[0]["id"] if response.data else None
    
    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    def create_session(candidate_id: str, job_id: str, channel: str, consent_required: bool) -> str:
        """Create a new interview session with UUID and retry logic"""
        # Generate UUID-based interview ID (guaranteed unique)
        interview_id = f"INT-{uuid.uuid4()}"
        
        data = {
            "id": interview_id,
            "candidate_id": candidate_id,
            "job_id": job_id,
            "status": "CREATED",
            "channel": channel,
            "consent_status": "pending" if consent_required else "not_required",
            "created_at": datetime.utcnow().isoformat()
        }
        
        supabase.table("interview_sessions").insert(data).execute()
        return interview_id
    
    @staticmethod
    def get_session(interview_id: str) -> Optional[Dict[str, Any]]:
        """Get interview session by ID"""
        response = supabase.table("interview_sessions").select("*").eq("id", interview_id).execute()
        return response.data[0] if response.data else None
    
    @staticmethod
    def update_session_status(interview_id: str, status: str, **kwargs):
        """Update session status and other fields"""
        update_data = {"status": status}
        update_data.update(kwargs)
        supabase.table("interview_sessions").update(update_data).eq("id", interview_id).execute()
    
    @staticmethod
    def update_consent(interview_id: str, consent_status: str, consent_text: str = None):
        """Update consent status"""
        data = {"consent_status": consent_status}
        if consent_text:
            data["consent_text"] = consent_text
        supabase.table("interview_sessions").update(data).eq("id", interview_id).execute()
    
    @staticmethod
    def start_interview(interview_id: str):
        """Mark interview as started"""
        supabase.table("interview_sessions").update({
            "status": "INTERVIEW_IN_PROGRESS",
            "started_at": datetime.utcnow().isoformat()
        }).eq("id", interview_id).execute()
    
    @staticmethod
    def finish_interview(interview_id: str):
        """Mark interview as completed"""
        supabase.table("interview_sessions").update({
            "status": "COMPLETED",
            "ended_at": datetime.utcnow().isoformat()
        }).eq("id", interview_id).execute()
