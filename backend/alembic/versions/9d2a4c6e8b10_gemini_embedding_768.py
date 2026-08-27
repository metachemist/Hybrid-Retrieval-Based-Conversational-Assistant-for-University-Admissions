"""switch embedding column to gemini-embedding-001 (768-dim)

The project is moving retrieval fully off OpenAI: query and chunk embeddings
now come from Google gemini-embedding-001 at output_dimensionality=768
(app.services.retrieval.embeddings), replacing OpenAI text-embedding-3-small
(1536-dim).

A dimension change makes every stored vector unusable — they live in a
different embedding space, not merely the wrong shape — so this drops the
column and its index and recreates them empty at 768. Chunk *text*
(chunks.content) is untouched; scripts/reembed_chunks.py repopulates the
vectors afterwards. Written idempotently so it converges whether it runs
against the live 1536-dim database or a fresh build.

Revision ID: 9d2a4c6e8b10
Revises: 7c3e1f9a2b58
Create Date: 2026-08-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = '9d2a4c6e8b10'
down_revision: Union[str, Sequence[str], None] = '7c3e1f9a2b58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIMENSION = 768  # gemini-embedding-001; keep in sync with app.models


def _current_embedding_dim(bind) -> int | None:
    """Return the declared dimension of chunks.embedding, or None if absent."""
    from sqlalchemy import text

    typ = bind.execute(text("""
        SELECT format_type(a.atttypid, a.atttypmod)
        FROM pg_attribute a
        JOIN pg_class t ON a.attrelid = t.oid
        JOIN pg_namespace n ON t.relnamespace = n.oid
        WHERE t.relname = 'chunks'
          AND n.nspname = current_schema()
          AND a.attname = 'embedding'
          AND a.attnum > 0
          AND NOT a.attisdropped
    """)).scalar()

    if not typ or not typ.startswith('vector'):
        return None
    if '(' not in typ:
        return None
    return int(typ.split('(')[1].rstrip(')'))


def upgrade() -> None:
    bind = op.get_bind()

    if _current_embedding_dim(bind) != EMBEDDING_DIMENSION:
        op.execute("DROP INDEX IF EXISTS chunks_embedding_hnsw_idx")
        op.execute("DROP INDEX IF EXISTS chunks_embedding_idx")
        op.execute("ALTER TABLE chunks DROP COLUMN IF EXISTS embedding")
        op.execute(f"ALTER TABLE chunks ADD COLUMN embedding vector({EMBEDDING_DIMENSION})")

    op.execute(
        "CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw_idx ON chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )


def downgrade() -> None:
    bind = op.get_bind()

    if _current_embedding_dim(bind) != 1536:
        op.execute("DROP INDEX IF EXISTS chunks_embedding_hnsw_idx")
        op.execute("ALTER TABLE chunks DROP COLUMN IF EXISTS embedding")
        op.execute("ALTER TABLE chunks ADD COLUMN embedding vector(1536)")

    op.execute(
        "CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw_idx ON chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )
