class ComplianceService:
    """Handles compliance-related operations (disclosure, consent)"""
    
    @staticmethod
    def get_disclosure_text() -> str:
        """Get standard disclosure text"""
        return (
            "Hi! I'm an AI interviewer powered by advanced language models. "
            "This conversation will be recorded and analyzed to assess your qualifications "
            "for the position. Your responses will be evaluated based on technical skills, "
            "communication, and cultural fit. The entire interview typically takes 15-20 minutes. "
            "Do I have your consent to proceed and record this conversation?"
        )
    
    @staticmethod
    def validate_consent(consent: str) -> bool:
        """Validate consent response"""
        positive_responses = ["yes", "y", "sure", "okay", "proceed", "agree"]
        return consent.lower().strip() in positive_responses
