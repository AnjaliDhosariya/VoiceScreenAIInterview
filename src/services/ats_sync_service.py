import requests
from datetime import datetime
from typing import Dict, Any
from src.db.supabase_client import supabase

class ATSSyncService:
    """Handles synchronization with ATS (mock)"""
    
    @staticmethod
    def sync_to_ats(interview_id: str, candidate_id: str, job_id: str, 
                   transcript: list, scores: Dict[str, Any], 
                   recommendation: str, summary: Dict[str, Any]) -> bool:
        """Sync interview results to mock ATS"""
        
        payload = {
            "candidateId": candidate_id,
            "jobId": job_id,
            "interviewId": interview_id,
            "transcript": transcript,
            "scores": {
                "technical": scores.get("technical") if scores else 0,
                "communication": scores.get("communication") if scores else 0,
                "culture": scores.get("culture") if scores else 0,
                "overall": scores.get("overall") if scores else 0
            },
            "recommendation": recommendation,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            # Call mock ATS endpoint
            response = requests.post(
                "http://localhost:8080/mock-ats/webhook",
                json=payload,
                timeout=5
            )
            
            success = response.status_code == 200
            
            # Log sync attempt
            ATSSyncService._log_sync(interview_id, payload, "success" if success else "fail")
            
            return success
            
        except Exception as e:
            ATSSyncService._log_sync(interview_id, payload, "fail")
            return False
    
    @staticmethod
    def _log_sync(interview_id: str, payload: Dict[str, Any], status: str):
        """Log ATS sync attempt"""
        data = {
            "interview_id": interview_id,
            "payload": payload,
            "status": status,
            "created_at": datetime.utcnow().isoformat()
        }
        supabase.table("ats_sync_logs").insert(data).execute()
