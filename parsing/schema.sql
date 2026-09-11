-- ==============================================================================
-- Supabase Schema & pgvector Setup for Government Services & Forms
-- Model: Hugging Face sentence-transformers (384 dimensions)
-- ==============================================================================

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create the table for government services, form blueprints, and submission workflows
CREATE TABLE IF NOT EXISTS government_schemas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_title TEXT NOT NULL,
    intent TEXT NOT NULL,
    department_name TEXT NOT NULL,
    portal_url TEXT NOT NULL,
    form_url TEXT NOT NULL UNIQUE,
    navigation_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    form_fields JSONB NOT NULL DEFAULT '[]'::jsonb,
    submit_button_selector TEXT NOT NULL,
    submission_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    search_content TEXT NOT NULL,
    raw_blueprint JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(384), -- 384 dimensions for all-MiniLM-L6-v2
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Create HNSW index for fast cosine distance semantic vector search
CREATE INDEX IF NOT EXISTS government_schemas_embedding_hnsw_idx 
ON government_schemas 
USING hnsw (embedding vector_cosine_ops);

-- 4. Create semantic similarity search function
CREATE OR REPLACE FUNCTION match_government_schemas (
  query_embedding vector(384),
  match_threshold float DEFAULT 0.3,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  service_title TEXT,
  intent TEXT,
  department_name TEXT,
  portal_url TEXT,
  form_url TEXT,
  navigation_steps JSONB,
  form_fields JSONB,
  submit_button_selector TEXT,
  submission_steps JSONB,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    g.id,
    g.service_title,
    g.intent,
    g.department_name,
    g.portal_url,
    g.form_url,
    g.navigation_steps,
    g.form_fields,
    g.submit_button_selector,
    g.submission_steps,
    (1 - (g.embedding <=> query_embedding))::float AS similarity
  FROM government_schemas g
  WHERE (1 - (g.embedding <=> query_embedding)) > match_threshold
  ORDER BY similarity DESC
  LIMIT match_count;
END;
$$;
