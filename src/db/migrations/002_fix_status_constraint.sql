-- FIX: Add DISCLOSURE_DONE to valid_status constraint
-- Run this to fix the 500 error

ALTER TABLE interview_sessions
DROP CONSTRAINT IF EXISTS valid_status;

ALTER TABLE interview_sessions
ADD CONSTRAINT valid_status 
    CHECK (status IN (
        'CREATED', 
        'DISCLOSURE_DONE',
        'CONSENT_GRANTED', 
        'INTERVIEW_IN_PROGRESS', 
        'COMPLETED', 
        'CANCELLED'
    ));
