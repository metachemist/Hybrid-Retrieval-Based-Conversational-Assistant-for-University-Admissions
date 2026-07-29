#!/usr/bin/env python3
"""
Document Ingestion Script

Processes admission PDF and image (jpg/png) documents and ingests them into the database.
Images are transcribed via OpenAI vision (see app/services/retrieval/image_processor.py).

Usage:
    python scripts/ingest_documents.py path/to/prospectus.pdf [--title "Admission Prospectus 2024"]
"""
import sys
import os
import argparse

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.core.database import SessionLocal, engine, Base
from app.models import Document, Chunk
from app.services.retrieval.pdf_processor import PDFProcessor
from app.services.retrieval.image_processor import ImageProcessor
from app.services.retrieval.chunking import DocumentChunker
from app.services.retrieval.embeddings import get_embedding_model

IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png')
SUPPORTED_EXTENSIONS = ('.pdf',) + IMAGE_EXTENSIONS


def ingest_document(file_path: str, title: str = None, year: int = None) -> dict:
    """
    Ingest a single document into the database.

    Args:
        file_path: Path to the PDF or image file
        title: Optional title override
        year: Optional year

    Returns:
        Ingestion result dictionary
    """
    db = SessionLocal()

    try:
        # Validate file
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.lower().endswith(SUPPORTED_EXTENSIONS):
            raise ValueError("Only PDF and image (jpg/png) files are supported")

        print(f"Processing: {file_path}")

        # Extract text and metadata
        processor = ImageProcessor() if file_path.lower().endswith(IMAGE_EXTENSIONS) else PDFProcessor()
        full_text, metadata = processor.extract(file_path)
        
        doc_title = title or metadata.title
        doc_year = year or metadata.year
        
        print(f"  Title: {doc_title}")
        print(f"  Year: {doc_year}")
        print(f"  Pages: {metadata.total_pages}")
        
        # Create document record
        document = Document(
            title=doc_title,
            year=doc_year,
            source_path=os.path.abspath(file_path),
            ingested_at=datetime.utcnow()
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        print(f"  Document ID: {document.id}")
        
        # Extract sections and chunk
        sections = processor.extract_with_sections(file_path)
        chunker = DocumentChunker()
        embedding_model = get_embedding_model()
        
        total_chunks = 0
        
        for section in sections:
            chunks = chunker.chunk_text(
                text=section.content,
                section_header=section.section_header,
                page_start=section.page_start,
                page_end=section.page_end,
                chunk_type=section.chunk_type
            )
            
            # Generate embeddings and store
            for i, chunk in enumerate(chunks):
                embedding = embedding_model.encode_query(chunk.content)
                
                chunk_record = Chunk(
                    doc_id=document.id,
                    content=chunk.content,
                    embedding=embedding.tolist(),
                    section_header=chunk.section_header,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    chunk_type=chunk.chunk_type,
                    chunk_order=total_chunks
                )
                db.add(chunk_record)
                total_chunks += 1
                
                if total_chunks % 10 == 0:
                    print(f"  Processed {total_chunks} chunks...")
        
        db.commit()
        
        print(f"  ✓ Ingestion complete: {total_chunks} chunks created")
        
        return {
            "document_id": str(document.id),
            "title": doc_title,
            "year": doc_year,
            "chunks_created": total_chunks,
            "status": "success"
        }
        
    except Exception as e:
        db.rollback()
        print(f"  ✗ Error: {e}")
        return {
            "file": file_path,
            "status": "error",
            "error": str(e)
        }
    finally:
        db.close()


def ingest_directory(dir_path: str) -> list:
    """
    Ingest all supported documents (PDFs and images) from a directory.

    Args:
        dir_path: Path to directory containing documents

    Returns:
        List of ingestion results
    """
    results = []

    if not os.path.isdir(dir_path):
        raise NotADirectoryError(f"Directory not found: {dir_path}")

    files = sorted(f for f in os.listdir(dir_path) if f.lower().endswith(SUPPORTED_EXTENSIONS))

    if not files:
        print(f"No supported files found in {dir_path}")
        return results

    print(f"Found {len(files)} files")

    for filename in files:
        file_path = os.path.join(dir_path, filename)
        result = ingest_document(file_path)
        results.append(result)

    return results


def main():
    parser = argparse.ArgumentParser(description="Ingest admission documents into the database")
    parser.add_argument("path", help="Path to a PDF/image file or a directory of them")
    parser.add_argument("--title", help="Override document title")
    parser.add_argument("--year", type=int, help="Override document year")
    
    args = parser.parse_args()
    
    # Initialize database
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    
    # Check if path is file or directory
    if os.path.isfile(args.path):
        result = ingest_document(args.path, args.title, args.year)
        print(f"\nResult: {result}")
    elif os.path.isdir(args.path):
        results = ingest_directory(args.path)
        print(f"\nCompleted: {len(results)} documents processed")
        success = sum(1 for r in results if r.get("status") == "success")
        print(f"Successful: {success}, Failed: {len(results) - success}")
    else:
        print(f"Error: Path not found: {args.path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
