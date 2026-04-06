"""
Documents API Endpoints

Handles document upload, ingestion, and management.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import uuid

from ..core.database import get_db
from ..core.security import require_admin
from ..models import Document, Chunk
from ..services.retrieval.pdf_processor import PDFProcessor
from ..services.retrieval.chunking import DocumentChunker
from ..services.retrieval.embeddings import get_embedding_model

router = APIRouter()


class DocumentInfo(BaseModel):
    """Document information response."""
    id: str
    title: str
    year: Optional[int]
    total_pages: int
    chunk_count: int
    ingested_at: datetime
    
    class Config:
        from_attributes = True


class IngestResponse(BaseModel):
    """Response for document ingestion."""
    document_id: str
    title: str
    chunks_created: int
    status: str


class IngestionStatus(BaseModel):
    """Status of document ingestion."""
    document_id: str
    status: str  # processing, completed, failed
    progress: int  # 0-100
    chunks_processed: int
    error: Optional[str] = None


@router.post("/documents/upload", response_model=IngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    year: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Upload and ingest a PDF document.
    
    Process:
    1. Save uploaded file
    2. Extract text using PyMuPDF
    3. Chunk the text
    4. Generate embeddings
    5. Store in database
    """
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Create data directory if not exists
    data_dir = "data/raw"
    os.makedirs(data_dir, exist_ok=True)
    
    # Save file
    file_id = str(uuid.uuid4())
    file_path = os.path.join(data_dir, f"{file_id}_{file.filename}")
    
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Process document
    try:
        # Extract text and metadata
        processor = PDFProcessor()
        full_text, metadata = processor.extract(file_path)
        
        # Use provided title or extract from document
        doc_title = title or metadata.title
        
        # Create document record
        document = Document(
            title=doc_title,
            year=year or metadata.year,
            source_path=file_path,
            ingested_at=datetime.utcnow()
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Chunk the document
        sections = processor.extract_with_sections(file_path)
        chunker = DocumentChunker()
        all_chunks = []
        
        for section in sections:
            chunks = chunker.chunk_text(
                text=section.content,
                section_header=section.section_header,
                page_start=section.page_start,
                page_end=section.page_end,
                chunk_type=section.chunk_type
            )
            all_chunks.extend(chunks)
        
        # Generate embeddings and store chunks
        embedding_model = get_embedding_model()
        
        chunks_to_store = []
        for i, chunk in enumerate(all_chunks):
            # Generate embedding
            embedding = embedding_model.encode_query(chunk.content)
            
            # Create chunk record
            chunk_record = Chunk(
                doc_id=document.id,
                content=chunk.content,
                embedding=embedding.tolist(),
                section_header=chunk.section_header,
                page_start=chunk.page_start,
                page_end=chunk.page_end,
                chunk_type=chunk.chunk_type,
                chunk_order=i
            )
            chunks_to_store.append(chunk_record)
        
        # Bulk insert chunks
        db.bulk_save_objects(chunks_to_store)
        db.commit()
        
        return IngestResponse(
            document_id=str(document.id),
            title=document.title,
            chunks_created=len(chunks_to_store),
            status="completed"
        )
        
    except Exception as e:
        db.rollback()
        # Clean up file
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@router.get("/documents", response_model=List[DocumentInfo])
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """List all indexed documents."""
    documents = db.query(Document).offset(skip).limit(limit).all()
    
    # Get chunk counts
    result = []
    for doc in documents:
        chunk_count = db.query(Chunk).filter(Chunk.doc_id == doc.id).count()
        result.append(DocumentInfo(
            id=str(doc.id),
            title=doc.title,
            year=doc.year,
            total_pages=0,  # Would need to extract from metadata
            chunk_count=chunk_count,
            ingested_at=doc.ingested_at
        ))
    
    return result


@router.get("/documents/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get document and chunk statistics."""
    doc_count = db.query(Document).count()
    chunk_count = db.query(Chunk).count()

    first_chunk = db.query(Chunk).first()
    embedding_dim = len(first_chunk.embedding) if first_chunk and first_chunk.embedding else 0

    return {
        "total_documents": doc_count,
        "total_chunks": chunk_count,
        "embedding_dimension": embedding_dim
    }


@router.get("/documents/{document_id}", response_model=DocumentInfo)
async def get_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Get details of a specific document."""
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    chunk_count = db.query(Chunk).filter(Chunk.doc_id == document.id).count()

    return DocumentInfo(
        id=str(document.id),
        title=document.title,
        year=document.year,
        total_pages=0,
        chunk_count=chunk_count,
        ingested_at=document.ingested_at
    )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Delete a document and all its chunks.
    
    Note: This doesn't delete the original PDF file.
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete chunks (cascade should handle this, but being explicit)
    db.query(Chunk).filter(Chunk.doc_id == document_id).delete()
    
    # Delete document
    db.delete(document)
    db.commit()
    
    return {"status": "deleted", "document_id": document_id}


@router.post("/documents/{document_id}/reindex")
async def reindex_document(
    document_id: str,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Re-index a document (re-process chunks and embeddings).
    
    Useful when:
    - Embedding model is updated
    - Chunking strategy changes
    - Document needs refresh
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    if not document.source_path or not os.path.exists(document.source_path):
        raise HTTPException(status_code=400, detail="Source file not found")
    
    try:
        # Delete existing chunks
        db.query(Chunk).filter(Chunk.doc_id == document_id).delete()
        
        # Re-process document
        processor = PDFProcessor()
        sections = processor.extract_with_sections(document.source_path)
        chunker = DocumentChunker()
        embedding_model = get_embedding_model()
        
        chunks_to_store = []
        for i, section in enumerate(sections):
            chunks = chunker.chunk_text(
                text=section.content,
                section_header=section.section_header,
                page_start=section.page_start,
                page_end=section.page_end,
                chunk_type=section.chunk_type
            )
            
            for chunk in chunks:
                embedding = embedding_model.encode_query(chunk.content)
                chunk_record = Chunk(
                    doc_id=document.id,
                    content=chunk.content,
                    embedding=embedding.tolist(),
                    section_header=chunk.section_header,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    chunk_type=chunk.chunk_type,
                    chunk_order=len(chunks_to_store)
                )
                chunks_to_store.append(chunk_record)
        
        db.bulk_save_objects(chunks_to_store)
        db.commit()
        
        return {"status": "completed", "chunks_reindexed": len(chunks_to_store)}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Re-indexing failed: {str(e)}")
