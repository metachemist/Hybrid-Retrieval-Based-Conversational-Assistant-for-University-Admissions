"""
Document Processing Module

Handles PDF parsing, text extraction, and chunking for admission documents.
"""
from .pdf_processor import PDFProcessor
from .chunking import DocumentChunker

__all__ = ["PDFProcessor", "DocumentChunker"]
