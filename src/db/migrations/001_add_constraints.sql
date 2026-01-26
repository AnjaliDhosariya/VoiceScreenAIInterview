-- Database Migration: P0 Improvements
-- Add constraints, indexes, and validation for robustness
-- Version: 001
-- Date: 2026-01-26

-- ============================================================================
-- PHASE 1: Add Indexes (CONCURRENT - No table locking)
-- ============================================================================

-- Index for faster candidate lookups
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_interviews_candidate_id 
    ON interview_sessions(candidate_id);

-- Index for status-based queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_interviews_status 
    ON interview_sessions(status);

-- Index for time-based queries and sorting
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_interviews_created_at 
    ON interview_sessions(created_at);

-- Composite index for candidate + status queries (most common pattern)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_interviews_candidate_status 
    ON interview_sessions(candidate_id, status);

-- ============================================================================
-- PHASE 2: Add Validation Constraints
-- ============================================================================

-- Ensure status values are valid
-- Prevents typos and invalid states
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

-- ============================================================================
-- PHASE 3: Unique Constraint for Active Interviews
-- ============================================================================

-- Prevent duplicate active interviews for same candidate
-- Uses partial unique index (PostgreSQL 15+)
-- Only enforces uniqueness when status is CREATED or INTERVIEW_IN_PROGRESS

DROP INDEX IF EXISTS unique_active_interview;

CREATE UNIQUE INDEX unique_active_interview 
    ON interview_sessions(candidate_id) 
    WHERE status IN ('CREATED', 'INTERVIEW_IN_PROGRESS');

-- ============================================================================
-- PHASE 4: Add Comments for Documentation
-- ============================================================================

COMMENT ON INDEX idx_interviews_candidate_id IS 'Fast lookups for all interviews by candidate';
COMMENT ON INDEX idx_interviews_status IS 'Fast filtering by interview status';
COMMENT ON INDEX idx_interviews_created_at IS 'Time-based sorting and range queries';
COMMENT ON INDEX unique_active_interview IS 'Prevents duplicate active interviews per candidate';
COMMENT ON CONSTRAINT valid_status ON interview_sessions IS 'Ensures only valid status values';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify indexes were created
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'interview_sessions'
ORDER BY indexname;

-- Verify constraints were added
SELECT
    constraint_name,
    constraint_type,
    table_name
FROM information_schema.table_constraints
WHERE table_name = 'interview_sessions'
ORDER BY constraint_name;

-- ============================================================================
-- NOTES FOR ROLLBACK
-- ============================================================================

/*
To rollback this migration:

-- Remove indexes
DROP INDEX IF EXISTS idx_interviews_candidate_id;
DROP INDEX IF EXISTS idx_interviews_status;
DROP INDEX IF EXISTS idx_interviews_created_at;
DROP INDEX IF EXISTS idx_interviews_candidate_status;
DROP INDEX IF EXISTS unique_active_interview;

-- Remove constraints
ALTER TABLE interview_sessions DROP CONSTRAINT IF EXISTS valid_status;
*/
