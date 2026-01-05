-- Migration: Add metadata column to chat_messages table
-- Date: 2026-01-02
-- Purpose: Store RAG sources, parameters, and workflow information

-- Add metadata JSONB column
ALTER TABLE chat_messages 
ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT NULL;

-- Add documentation comment
COMMENT ON COLUMN chat_messages.metadata IS 
'Stores message metadata in JSON format: sources (document references), rag_params (TOP_K, threshold), workflow_path, actions_taken';

-- Verification query (optional, for manual check)
-- SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'chat_messages';
