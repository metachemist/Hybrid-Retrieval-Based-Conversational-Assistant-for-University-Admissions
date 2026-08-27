#!/usr/bin/env python3
"""
Re-embed every stored chunk with the currently configured embedding model.

Use after switching EMBEDDING_MODEL / EMBEDDING_DIMENSION and running
`alembic upgrade head`. Reads chunks.content straight from the database and
writes chunks.embedding back — no PDF/image re-processing, so this never
touches the OpenAI vision path.

By default it only fills chunks whose embedding IS NULL, so it is safe to
re-run after an interruption or a partial failure. Pass --all to re-embed
every chunk regardless.

Usage:
    python scripts/reembed_chunks.py [--all] [--batch-size 10] [--sleep 3.0]
"""
import argparse
import os
import sys
import time

_BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, _BACKEND)
# Settings loads backend/.env relative to the working directory.
os.chdir(_BACKEND)

from app.core.config import settings          # noqa: E402
from app.core.database import SessionLocal    # noqa: E402
from app.models import Chunk                  # noqa: E402
from app.services.retrieval.embeddings import get_embedding_model  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Re-embed all chunks")
    parser.add_argument("--all", action="store_true",
                        help="re-embed every chunk, not just those missing an embedding")
    parser.add_argument("--batch-size", type=int, default=10,
                        help="chunks per embedding API call (default 10; free tier is rate-limited)")
    parser.add_argument("--sleep", type=float, default=3.0,
                        help="seconds to wait between batches, for free-tier rate limits")
    args = parser.parse_args()

    print(f"Embedding model : {settings.EMBEDDING_MODEL}")
    print(f"Dimension       : {settings.EMBEDDING_DIMENSION}")

    db = SessionLocal()
    model = get_embedding_model()

    try:
        q = db.query(Chunk.id, Chunk.content).order_by(Chunk.id)
        if not args.all:
            q = q.filter(Chunk.embedding.is_(None))
        rows = q.all()

        total = len(rows)
        if total == 0:
            print("Nothing to do — every chunk already has an embedding.")
            return 0

        print(f"Re-embedding {total} chunk(s)...\n")
        done = 0
        for i in range(0, total, args.batch_size):
            batch = rows[i:i + args.batch_size]
            texts = [content for _, content in batch]

            # Free-tier embedding quota returns 429 in bursts; back off and retry
            # this batch rather than losing the whole run.
            for attempt in range(6):
                try:
                    vectors = model.encode(texts)
                    break
                except Exception as e:  # noqa: BLE001
                    if "429" not in str(e) and "RESOURCE_EXHAUSTED" not in str(e):
                        raise
                    wait = 20 * (attempt + 1)
                    print(f"  rate-limited, waiting {wait}s (attempt {attempt + 1}/6)...")
                    time.sleep(wait)
            else:
                raise RuntimeError("still rate-limited after 6 retries; re-run to resume")

            for (chunk_id, _), vec in zip(batch, vectors):
                db.query(Chunk).filter(Chunk.id == chunk_id).update(
                    {"embedding": vec.tolist()}, synchronize_session=False
                )
            db.commit()

            done += len(batch)
            print(f"  {done}/{total} committed")
            if done < total and args.sleep:
                time.sleep(args.sleep)

        print("\n✓ Re-embedding complete.")
        return 0

    except Exception as e:  # noqa: BLE001
        db.rollback()
        print(f"\n✗ Failed: {e}")
        print("  Re-run the script to resume from where it stopped.")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
