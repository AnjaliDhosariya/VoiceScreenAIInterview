-- Database schema for candidate state persistence
-- This table stores the evolving state of each candidate during their interview

CREATE TABLE IF NOT EXISTS candidate_states (
    interview_id VARCHAR PRIMARY KEY REFERENCES interview_sessions(id) ON DELETE CASCADE,
    state_data JSONB NOT NULL,
    last_updated TIMESTAMP DEFAULT NOW(),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_candidate_states_interview ON candidate_states(interview_id);
CREATE INDEX IF NOT EXISTS idx_candidate_states_updated ON candidate_states(last_updated);

-- Add comment
COMMENT ON TABLE candidate_states IS 'Stores evolving candidate state for agentic interview decision-making';
COMMENT ON COLUMN candidate_states.state_data IS 'JSON blob containing CandidateState data including performance, decisions, and signals';
