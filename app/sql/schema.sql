-- Embeddings from nomic-embed-text are 768-dimensional.
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS documents (
    id bigserial PRIMARY KEY,
    content text NOT NULL,
    embedding vector(768) NOT NULL
);
-- HNSW works well for both the tiny demo seed and larger local collections;
-- an IVFFlat index with many empty lists can return no candidates on small corpora.
DROP INDEX IF EXISTS documents_embedding_idx;
CREATE INDEX IF NOT EXISTS documents_embedding_hnsw_idx
    ON documents USING hnsw (embedding vector_cosine_ops);
