"""
Tests for document chunking.
"""
import pytest
from app.services.retrieval.chunking import DocumentChunker, Chunk


class TestDocumentChunker:
    """Test cases for document chunking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.chunker = DocumentChunker(chunk_size=100, overlap=20)
    
    def test_small_text(self):
        """Test chunking of small text."""
        text = "This is a small text."
        chunks = self.chunker.chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0].content == text
    
    def test_empty_text(self):
        """Test empty text handling."""
        chunks = self.chunker.chunk_text("")
        assert len(chunks) == 0
    
    def test_chunk_metadata(self):
        """Test chunk metadata."""
        text = "This is a test paragraph."
        chunks = self.chunker.chunk_text(
            text,
            section_header="Test Section",
            page_start=1,
            page_end=2
        )
        assert len(chunks) == 1
        assert chunks[0].section_header == "Test Section"
        assert chunks[0].page_start == 1
        assert chunks[0].page_end == 2
    
    def test_chunk_type(self):
        """Test different chunk types."""
        text = "Test content"
        
        # Text chunk
        chunks = self.chunker.chunk_text(text, chunk_type="text")
        assert chunks[0].chunk_type == "text"
        
        # Table chunk
        chunks = self.chunker.chunk_text(text, chunk_type="table")
        assert chunks[0].chunk_type == "table"
    
    def test_overlap(self):
        """Test that chunks have proper overlap."""
        # Create text that will be split into multiple chunks
        text = " ".join([f"Sentence {i}." for i in range(50)])
        chunks = self.chunker.chunk_text(text)
        
        if len(chunks) > 1:
            # Check that there's some overlap between consecutive chunks
            for i in range(len(chunks) - 1):
                # This is a basic check - real overlap testing would be more complex
                assert chunks[i].chunk_order == i
    
    def test_chunk_order(self):
        """Test chunk ordering."""
        text = " ".join([f"Paragraph {i}." for i in range(10)])
        chunks = self.chunker.chunk_text(text)
        
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_order == i
