"""
Job Service
Handles loading and managing job descriptions for dynamic interview generation
"""

import json
import os
from typing import Dict, Any, List, Optional

class JobService:
    """Service for managing job descriptions"""
    
    def __init__(self):
        self.jobs_cache = None
        self.jobs_file_path = os.path.join(os.path.dirname(__file__), '..', '..', 'job_descriptions.json')
    
    def load_jobs(self) -> Dict[str, Any]:
        """Load job descriptions from JSON file"""
        if self.jobs_cache is not None:
            return self.jobs_cache
        
        try:
            with open(self.jobs_file_path, 'r') as f:
                data = json.load(f)
                self.jobs_cache = data.get('jobs', {})
                return self.jobs_cache
        except FileNotFoundError:
            print(f"Warning: job_descriptions.json not found at {self.jobs_file_path}")
            return self._get_fallback_jobs()
        except json.JSONDecodeError as e:
            print(f"Error parsing job_descriptions.json: {e}")
            return self._get_fallback_jobs()
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job description by ID
        
        Args:
            job_id: Job ID (e.g., "JOB-DA-FRESHER")
            
        Returns:
            Job description dict or None
        """
        jobs = self.load_jobs()
        return jobs.get(job_id)
    
    def get_jobs_by_title(self, title: str) -> List[Dict[str, Any]]:
        """
        Get all jobs matching a title
        
        Args:
            title: Job title to search for (e.g., "Data Analyst")
            
        Returns:
            List of matching job descriptions
        """
        jobs = self.load_jobs()
        return [job for job in jobs.values() if job.get('title', '').lower() == title.lower()]
    
    def get_jobs_by_level(self, level: str) -> List[Dict[str, Any]]:
        """
        Get all jobs matching an experience level
        
        Args:
            level: Experience level (e.g., "Fresher", "Senior")
            
        Returns:
            List of matching job descriptions
        """
        jobs = self.load_jobs()
        return [job for job in jobs.values() if level.lower() in job.get('level', '').lower()]
    
    def list_all_jobs(self) -> Dict[str, str]:
        """
        Get a simplified list of all jobs
        
        Returns:
            Dict mapping job_id to "Title - Level"
        """
        jobs = self.load_jobs()
        return {
            job_id: f"{job['title']} - {job['level']}"
            for job_id, job in jobs.items()
        }
    
    def get_skills_for_job(self, job_id: str) -> Dict[str, List[str]]:
        """
        Get skills breakdown for a job
        
        Args:
            job_id: Job ID
            
        Returns:
            Dict with must_have_skills and nice_to_have_skills lists
        """
        job = self.get_job(job_id)
        if not job:
            return {"must_have_skills": [], "nice_to_have_skills": []}
        
        return {
            "must_have_skills": job.get("must_have_skills", []),
            "nice_to_have_skills": job.get("nice_to_have_skills", [])
        }
    
    def get_focus_areas(self, job_id: str) -> Dict[str, List[str]]:
        """
        Get technical and behavioral focus areas for a job
        
        Args:
            job_id: Job ID
            
        Returns:
            Dict with technical_focus_areas and behavioral_focus_areas
        """
        job = self.get_job(job_id)
        if not job:
            return {"technical_focus_areas": [], "behavioral_focus_areas": []}
        
        return {
            "technical_focus_areas": job.get("technical_focus_areas", []),
            "behavioral_focus_areas": job.get("behavioral_focus_areas", [])
        }
    
    def _get_fallback_jobs(self) -> Dict[str, Any]:
        """Fallback job data if JSON file is not available"""
        return {
            "JOB-DA-FRESHER": {
                "id": "JOB-DA-FRESHER",
                "title": "Data Analyst",
                "level": "Fresher",
                "experience_years": "0-1",
                "description": "Entry-level data analyst position",
                "must_have_skills": ["SQL", "Excel", "Data Visualization"],
                "nice_to_have_skills": ["Python", "Tableau"],
                "technical_focus_areas": ["SQL queries", "Data cleaning", "Basic analytics"],
                "behavioral_focus_areas": ["Learning agility", "Teamwork"]
            }
        }

# Global instance
job_service = JobService()


# Convenience functions
def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Get job by ID"""
    return job_service.get_job(job_id)


def list_jobs() -> Dict[str, str]:
    """List all available jobs"""
    return job_service.list_all_jobs()


def get_job_skills(job_id: str) -> Dict[str, List[str]]:
    """Get skills for a job"""
    return job_service.get_skills_for_job(job_id)
