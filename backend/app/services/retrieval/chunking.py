"""
Document Chunking Module

Implements hybrid chunking strategy:
- Section-based chunks (respect document structure)
- Fixed-size fallback with overlap
- Special handling for tables and lists
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
import re


@dataclass
class Chunk:
    """Represents a text chunk ready for embedding."""
    content: str
    section_header: str
    page_start: int
    page_end: int
    chunk_type: str  # 'text', 'table', 'list'
    chunk_order: int
    metadata: Dict


class DocumentChunker:
    """
    Chunk documents for embedding and retrieval.
    
    Strategy:
    1. Respect section boundaries when possible
    2. Split long sections into fixed-size chunks with overlap
    3. Keep tables intact when possible
    4. Track metadata for citations
    """
    
    # Default chunk settings
    DEFAULT_CHUNK_SIZE = 512  # tokens (approximate)
    DEFAULT_OVERLAP = 50  # tokens
    MIN_CHUNK_SIZE = 100  # Minimum meaningful chunk
    
    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_OVERLAP,
        min_chunk_size: int = MIN_CHUNK_SIZE
    ):
        """
        Initialize the chunker.
        
        Args:
            chunk_size: Target chunk size in tokens (approximate)
            overlap: Overlap between consecutive chunks
            min_chunk_size: Minimum chunk size to create
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.min_chunk_size = min_chunk_size
    
    def chunk_text(
        self,
        text: str,
        section_header: str = "",
        page_start: int = 0,
        page_end: int = 0,
        chunk_type: str = "text"
    ) -> List[Chunk]:
        """
        Chunk a text into smaller pieces.
        
        Args:
            text: Text to chunk
            section_header: Section header for context
            page_start: Starting page number
            page_end: Ending page number
            chunk_type: Type of content ('text', 'table', 'list')
            
        Returns:
            List of Chunk objects
        """
        if not text or not text.strip():
            return []
        
        # Estimate token count (rough approximation: 1 token ≈ 4 characters)
        estimated_tokens = len(text) // 4
        
        # If text is small enough, return as single chunk
        if estimated_tokens <= self.chunk_size:
            return [Chunk(
                content=text.strip(),
                section_header=section_header,
                page_start=page_start,
                page_end=page_end,
                chunk_type=chunk_type,
                chunk_order=0,
                metadata={}
            )]
        
        # For tables, try to keep intact
        if chunk_type == "table":
            return self._chunk_table(text, section_header, page_start, page_end)
        
        # For regular text, split with overlap
        return self._chunk_with_overlap(
            text, section_header, page_start, page_end, chunk_type
        )
    
    def _chunk_with_overlap(
        self,
        text: str,
        section_header: str,
        page_start: int,
        page_end: int,
        chunk_type: str
    ) -> List[Chunk]:
        """Split text into chunks with overlap."""
        chunks = []
        
        # Split by paragraphs first
        paragraphs = self._split_paragraphs(text)
        
        current_chunk = []
        current_length = 0
        chunk_order = 0
        
        for paragraph in paragraphs:
            paragraph_length = len(paragraph) // 4  # Token estimate
            
            # If single paragraph is too long, split it
            if paragraph_length > self.chunk_size:
                # Save current chunk if any
                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append(Chunk(
                        content=chunk_text.strip(),
                        section_header=section_header,
                        page_start=page_start,
                        page_end=page_end,
                        chunk_type=chunk_type,
                        chunk_order=chunk_order,
                        metadata={}
                    ))
                    chunk_order += 1
                    current_chunk = []
                    current_length = 0
                
                # Split long paragraph
                sub_chunks = self._split_long_paragraph(
                    paragraph, section_header, page_start, page_end, chunk_type, chunk_order
                )
                chunks.extend(sub_chunks)
                chunk_order += len(sub_chunks)
            
            # Check if adding this paragraph exceeds chunk size
            elif current_length + paragraph_length > self.chunk_size:
                # Save current chunk
                if current_chunk:
                    chunk_text = "\n\n".join(current_chunk)
                    chunks.append(Chunk(
                        content=chunk_text.strip(),
                        section_header=section_header,
                        page_start=page_start,
                        page_end=page_end,
                        chunk_type=chunk_type,
                        chunk_order=chunk_order,
                        metadata={}
                    ))
                    chunk_order += 1
                    
                    # Create overlap from end of current chunk
                    current_chunk = self._create_overlap(current_chunk)
                    current_length = sum(len(p) // 4 for p in current_chunk)
                else:
                    current_chunk = []
                    current_length = 0
                
                current_chunk.append(paragraph)
                current_length += paragraph_length
            
            else:
                current_chunk.append(paragraph)
                current_length += paragraph_length
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append(Chunk(
                content=chunk_text.strip(),
                section_header=section_header,
                page_start=page_start,
                page_end=page_end,
                chunk_type=chunk_type,
                chunk_order=chunk_order,
                metadata={}
            ))
        
        return chunks
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        # Split by double newlines
        paragraphs = re.split(r'\n\s*\n', text)
        
        # Filter empty paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def _split_long_paragraph(
        self,
        paragraph: str,
        section_header: str,
        page_start: int,
        page_end: int,
        chunk_type: str,
        start_order: int
    ) -> List[Chunk]:
        """Split a long paragraph into smaller chunks."""
        chunks = []
        
        # Try splitting by sentences first
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)
        
        if len(sentences) > 1:
            # Group sentences into chunks
            current_chunk = []
            current_length = 0
            
            for sentence in sentences:
                sentence_length = len(sentence) // 4
                
                if current_length + sentence_length > self.chunk_size:
                    if current_chunk:
                        chunks.append(Chunk(
                            content=" ".join(current_chunk).strip(),
                            section_header=section_header,
                            page_start=page_start,
                            page_end=page_end,
                            chunk_type=chunk_type,
                            chunk_order=start_order + len(chunks),
                            metadata={}
                        ))
                        # Overlap: keep last sentence
                        current_chunk = [sentences[max(0, len(sentences) - 2)]]
                        current_length = len(current_chunk[0]) // 4
                    else:
                        current_chunk = []
                        current_length = 0
                    
                    current_chunk.append(sentence)
                    current_length += sentence_length
                else:
                    current_chunk.append(sentence)
                    current_length += sentence_length
            
            # Last chunk
            if current_chunk:
                chunks.append(Chunk(
                    content=" ".join(current_chunk).strip(),
                    section_header=section_header,
                    page_start=page_start,
                    page_end=page_end,
                    chunk_type=chunk_type,
                    chunk_order=start_order + len(chunks),
                    metadata={}
                ))
        else:
            # Fallback: split by fixed character count
            chunk_text = paragraph
            start_idx = 0
            chunk_order = start_order
            
            while start_idx < len(chunk_text):
                end_idx = min(start_idx + self.chunk_size * 4, len(chunk_text))
                
                # Try to break at word boundary
                if end_idx < len(chunk_text):
                    last_space = chunk_text.rfind(' ', start_idx, end_idx)
                    if last_space > start_idx:
                        end_idx = last_space
                
                chunk_content = chunk_text[start_idx:end_idx].strip()
                if len(chunk_content) > self.min_chunk_size:
                    chunks.append(Chunk(
                        content=chunk_content,
                        section_header=section_header,
                        page_start=page_start,
                        page_end=page_end,
                        chunk_type=chunk_type,
                        chunk_order=chunk_order,
                        metadata={}
                    ))
                    chunk_order += 1
                
                start_idx = end_idx
        
        return chunks
    
    def _chunk_table(
        self,
        table_text: str,
        section_header: str,
        page_start: int,
        page_end: int
    ) -> List[Chunk]:
        """Try to keep tables intact, split only if necessary."""
        # If table is small enough, keep as single chunk
        if len(table_text) // 4 <= self.chunk_size:
            return [Chunk(
                content=table_text.strip(),
                section_header=section_header,
                page_start=page_start,
                page_end=page_end,
                chunk_type="table",
                chunk_order=0,
                metadata={"is_table": True}
            )]
        
        # For large tables, split by rows if possible
        rows = table_text.split('\n')
        chunks = []
        current_rows = []
        current_length = 0
        chunk_order = 0
        
        for row in rows:
            row_length = len(row) // 4
            
            if current_length + row_length > self.chunk_size:
                if current_rows:
                    chunks.append(Chunk(
                        content="\n".join(current_rows).strip(),
                        section_header=section_header,
                        page_start=page_start,
                        page_end=page_end,
                        chunk_type="table",
                        chunk_order=chunk_order,
                        metadata={"is_table": True, "is_partial": True}
                    ))
                    chunk_order += 1
                    current_rows = [rows[max(0, len(rows) - 2)]]  # Keep header row as overlap
                else:
                    current_rows = []
                
                current_rows.append(row)
                current_length = sum(len(r) // 4 for r in current_rows)
            else:
                current_rows.append(row)
                current_length += row_length
        
        if current_rows:
            chunks.append(Chunk(
                content="\n".join(current_rows).strip(),
                section_header=section_header,
                page_start=page_start,
                page_end=page_end,
                chunk_type="table",
                chunk_order=chunk_order,
                metadata={"is_table": True}
            ))
        
        return chunks
    
    def _create_overlap(self, paragraphs: List[str]) -> List[str]:
        """Create overlap from end of paragraphs."""
        if not paragraphs:
            return []
        
        # Keep last few paragraphs that fit in overlap size
        overlap_paragraphs = []
        current_length = 0
        
        for paragraph in reversed(paragraphs):
            paragraph_length = len(paragraph) // 4
            if current_length + paragraph_length <= self.overlap:
                overlap_paragraphs.insert(0, paragraph)
                current_length += paragraph_length
            else:
                break
        
        return overlap_paragraphs if overlap_paragraphs else [paragraphs[-1]]
    
    def add_context_to_chunks(
        self,
        chunks: List[Chunk],
        context: str,
        max_length: int = 100
    ) -> List[Chunk]:
        """
        Add contextual information to each chunk.
        
        Args:
            chunks: List of chunks to modify
            context: Context string to prepend
            max_length: Maximum length of context to add
            
        Returns:
            Modified list of chunks
        """
        context = context[:max_length].strip()
        
        for chunk in chunks:
            if context:
                chunk.content = f"{context}\n\n{chunk.content}"
        
        return chunks


def chunk_document(
    text: str,
    section_header: str = "",
    page_start: int = 0,
    page_end: int = 0,
    chunk_size: int = 512,
    overlap: int = 50
) -> List[Chunk]:
    """
    Convenience function to chunk a document.
    
    Args:
        text: Text to chunk
        section_header: Section header
        page_start: Starting page
        page_end: Ending page
        chunk_size: Target chunk size
        overlap: Overlap size
        
    Returns:
        List of Chunk objects
    """
    chunker = DocumentChunker(chunk_size=chunk_size, overlap=overlap)
    return chunker.chunk_text(text, section_header, page_start, page_end)
