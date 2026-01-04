-- Migration: Add memory_type column to long_term_memories table
-- Date: 2026-01-02
-- Purpose: Support both session_summary (auto) and explicit_fact (user requested)

-- Add memory_type column
ALTER TABLE long_term_memories 
ADD COLUMN IF NOT EXISTS memory_type VARCHAR(20) DEFAULT 'session_summary';

-- Add index for faster filtering by user + type
CREATE INDEX IF NOT EXISTS idx_ltm_user_type 
ON long_term_memories(user_id, memory_type);

-- Add comment
COMMENT ON COLUMN long_term_memories.memory_type IS 
'Memory type: session_summary (automatic session close) | explicit_fact (user requested "jegyezd meg")';

-- Verify column
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'long_term_memories' 
        AND column_name = 'memory_type'
    ) THEN
        RAISE NOTICE 'Migration successful: memory_type column added';
    ELSE
        RAISE EXCEPTION 'Migration failed: memory_type column not found';
    END IF;
END $$;
