-- Migration: create agent state table
-- Assumption: application uses PostgreSQL
CREATE TABLE IF NOT EXISTS agent_states (
    id UUID PRIMARY KEY,
    data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
