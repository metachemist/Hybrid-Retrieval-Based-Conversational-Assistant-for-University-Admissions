"""pgvector embedding column on chunks

Fixes chunks.embedding_data (a plain JSON-text column) which the retriever
was incorrectly querying with pgvector's cosine_distance() — that only
works on a real pgvector-typed column. Replaces it with one.

Revision ID: 2b4f6a9c1d3e
Revises: 1a70cd8d8d31
Create Date: 2026-07-29 17:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = '2b4f6a9c1d3e'
down_revision: Union[str, Sequence[str], None] = '1a70cd8d8d31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIMENSION = 768  # gemini-embedding-001


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.drop_column('chunks', 'embedding_data')
    op.add_column('chunks', sa.Column('embedding', Vector(EMBEDDING_DIMENSION), nullable=True))
    op.execute(
        "CREATE INDEX chunks_embedding_idx ON chunks "
        "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS chunks_embedding_idx")
    op.drop_column('chunks', 'embedding')
    op.add_column('chunks', sa.Column('embedding_data', sa.Text(), nullable=True))
