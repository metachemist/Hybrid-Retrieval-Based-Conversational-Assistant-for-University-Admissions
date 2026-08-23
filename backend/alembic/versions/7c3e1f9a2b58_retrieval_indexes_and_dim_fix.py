"""retrieval indexes + embedding dimension correction

Two problems this fixes, both found by inspecting the live Neon database:

1. Revision 2b4f6a9c1d3e declared the embedding column as vector(768) for
   gemini-embedding-001, but the project moved to OpenAI
   text-embedding-3-small (1536-dim) and app.models was updated without a
   matching migration. The deployed database is vector(1536) because it was
   built by Base.metadata.create_all() and then `alembic stamp`ed - the
   migration never actually executed. So a *fresh* build from migrations
   would have produced a 768 column that no longer matches the model.

2. Because that migration never ran, chunks_embedding_idx does not exist on
   the deployed database, and there has never been a full-text index at all.
   Both retrieval arms were sequential scans; _keyword_search additionally
   recomputed to_tsvector() over every chunk on every query.

Everything here is written to be idempotent so it converges to the same
schema whether it runs against the stamped-but-unmigrated production
database or a fresh one built from scratch.

Revision ID: 7c3e1f9a2b58
Revises: 2b4f6a9c1d3e
Create Date: 2026-08-23 19:05:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = '7c3e1f9a2b58'
down_revision: Union[str, Sequence[str], None] = '2b4f6a9c1d3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIMENSION = 1536  # openai text-embedding-3-small; keep in sync with app.models


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
    """Upgrade schema."""
    bind = op.get_bind()

    # --- 1. Embedding column at the dimension the application actually uses ---
    current_dim = _current_embedding_dim(bind)

    if current_dim != EMBEDDING_DIMENSION:
        # A dimension mismatch means any stored vectors came from a different
        # embedding model, so they are not merely the wrong shape - they are
        # semantically meaningless against text-embedding-3-small queries.
        # There is no cast worth attempting; drop and re-ingest.
        op.execute("DROP INDEX IF EXISTS chunks_embedding_idx")
        op.execute("ALTER TABLE chunks DROP COLUMN IF EXISTS embedding")
        op.execute(f"ALTER TABLE chunks ADD COLUMN embedding vector({EMBEDDING_DIMENSION})")

    # --- 2. Vector index ---
    # HNSW rather than the ivfflat in 2b4f6a9c1d3e: ivfflat needs its `lists`
    # tuned to the row count (that migration hardcoded lists=100 for a table
    # that holds 781 chunks, which would have degenerated toward a scan
    # anyway) and it must be rebuilt as the corpus grows. HNSW needs no such
    # tuning and gives better recall at this size.
    op.execute(
        "CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw_idx ON chunks "
        "USING hnsw (embedding vector_cosine_ops)"
    )
    op.execute("DROP INDEX IF EXISTS chunks_embedding_idx")

    # --- 3. Full-text search column + index ---
    # Stored generated column so to_tsvector() is computed once at write time
    # instead of over every row on every query, and so a GIN index can back
    # the match. to_tsvector(regconfig, text) is immutable when the config is
    # passed explicitly, which is what makes it legal in a generated column.
    op.execute("""
        ALTER TABLE chunks ADD COLUMN IF NOT EXISTS content_tsv tsvector
        GENERATED ALWAYS AS (to_tsvector('english', content)) STORED
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS chunks_content_tsv_idx ON chunks USING GIN (content_tsv)"
    )

    # --- 4. Foreign-key index for chunk -> document joins ---
    op.execute("CREATE INDEX IF NOT EXISTS chunks_doc_id_idx ON chunks (doc_id)")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS chunks_doc_id_idx")
    op.execute("DROP INDEX IF EXISTS chunks_content_tsv_idx")
    op.execute("ALTER TABLE chunks DROP COLUMN IF EXISTS content_tsv")
    op.execute("DROP INDEX IF EXISTS chunks_embedding_hnsw_idx")
    op.execute(
        "CREATE INDEX IF NOT EXISTS chunks_embedding_idx ON chunks "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )
