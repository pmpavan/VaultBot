-- Enable pgvector extension for vector similarity search
-- Required for link_metadata.embedding column (Epic 3: Semantic Search)

create extension if not exists vector;

-- Verify extension is enabled
comment on extension vector is 'Vector similarity search for semantic search (Epic 3)';
