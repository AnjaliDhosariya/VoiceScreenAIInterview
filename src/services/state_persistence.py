from typing import Optional, Dict, Any
import json
from datetime import datetime
from src.db.supabase_client import supabase
from src.agents.candidate_state import CandidateState

class StatePersistence:
    """Handles saving and loading candidate state to/from database"""
    
    TABLE_NAME = "candidate_states"
    
    @staticmethod
    def save_state(state: CandidateState) -> bool:
        """Save candidate state to database"""
        try:
            data = {
                "interview_id": state.interview_id,
                "state_data": state.to_dict(),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Upsert (insert or update)
            supabase.table(StatePersistence.TABLE_NAME).upsert(data).execute()
            return True
        except Exception as e:
            print(f"Error saving state: {e}")
            return False
    
    @staticmethod
    def load_state(interview_id: str) -> Optional[CandidateState]:
        """Load candidate state from database"""
        try:
            response = supabase.table(StatePersistence.TABLE_NAME)\
                .select("*")\
                .eq("interview_id", interview_id)\
                .execute()
            
            if not response.data:
                return None
            
            state_data = response.data[0]["state_data"]
            return CandidateState.from_dict(state_data)
        except Exception as e:
            print(f"Error loading state: {e}")
            return None
    
    @staticmethod
    def create_state(interview_id: str, candidate_id: str, job_id: str) -> CandidateState:
        """Create new candidate state"""
        state = CandidateState(
            interview_id=interview_id,
            candidate_id=candidate_id,
            job_id=job_id
        )
        StatePersistence.save_state(state)
        return state
    
    @staticmethod
    def get_or_create_state(interview_id: str, candidate_id: str, job_id: str) -> CandidateState:
        """Get existing state or create new one"""
        state = StatePersistence.load_state(interview_id)
        if state is None:
            state = StatePersistence.create_state(interview_id, candidate_id, job_id)
        return state
    
    @staticmethod
    def delete_state(interview_id: str) -> bool:
        """Delete candidate state (cleanup)"""
        try:
            supabase.table(StatePersistence.TABLE_NAME)\
                .delete()\
                .eq("interview_id", interview_id)\
                .execute()
            return True
        except Exception as e:
            print(f"Error deleting state: {e}")
            return False
    
    @staticmethod
    def get_all_states() -> list:
        """Get all candidate states (for debugging/admin)"""
        try:
            response = supabase.table(StatePersistence.TABLE_NAME)\
                .select("*")\
                .execute()
            return [CandidateState.from_dict(row["state_data"]) for row in response.data]
        except Exception as e:
            print(f"Error getting all states: {e}")
            return []
