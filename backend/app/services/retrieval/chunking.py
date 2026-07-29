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
    
    # Markdown-style table row, e.g. "| Department | Fee |" or "|---|---|"
    TABLE_ROW_RE = re.compile(r'^\s*\|.*\|\s*$')
    TABLE_SEPARATOR_RE = re.compile(r'^\s*\|[\s:\-|]+\|\s*$')
    # Tab-delimited row (>=3 columns) - vision OCR doesn't always use markdown
    # pipes for tables even when asked to, so this is a format-agnostic fallback.
    TAB_ROW_RE = re.compile(r'^[^\t\n]+(\t[^\t\n]+){2,}$')
    MIN_TABLE_RUN = 3  # lines (header + separator + >=1 data row)

    def _is_table_row(self, line: str) -> bool:
        return bool(self.TABLE_ROW_RE.match(line) or self.TAB_ROW_RE.match(line))

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

        Detects markdown-style pipe tables and chunks each data row on its
        own (with the header row repeated for column context), instead of
        letting the generic prose chunker glom dozens of unrelated table
        rows (e.g. every department's eligibility) into one chunk - that
        dilutes the embedding for any single row and hurts retrieval
        precision for entity-specific queries ("Computer Science fee").

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

        lines = text.split('\n')
        table_runs = self._detect_table_runs(lines)

        if not table_runs:
            return self._chunk_prose(text, section_header, page_start, page_end, chunk_type)

        chunks = []
        cursor = 0
        for start, end in table_runs:
            if start > cursor:
                pre_text = "\n".join(lines[cursor:start]).strip()
                if pre_text:
                    chunks.extend(self._chunk_prose(
                        pre_text, section_header, page_start, page_end, chunk_type, len(chunks)
                    ))
            chunks.extend(self._chunk_table_rows(
                lines[start:end], section_header, page_start, page_end, len(chunks)
            ))
            cursor = end

        if cursor < len(lines):
            tail_text = "\n".join(lines[cursor:]).strip()
            if tail_text:
                chunks.extend(self._chunk_prose(
                    tail_text, section_header, page_start, page_end, chunk_type, len(chunks)
                ))

        return chunks

    def _detect_table_runs(self, lines: List[str]):
        """Find (start, end) index ranges of consecutive markdown table rows."""
        runs = []
        i, n = 0, len(lines)
        while i < n:
            if self._is_table_row(lines[i]):
                j = i
                while j < n and (self._is_table_row(lines[j]) or lines[j].strip() == ''):
                    j += 1
                k = j
                while k > i and lines[k - 1].strip() == '':
                    k -= 1
                if k - i >= self.MIN_TABLE_RUN:
                    runs.append((i, k))
                i = j
            else:
                i += 1
        return runs

    def _chunk_table_rows(
        self,
        table_lines: List[str],
        section_header: str,
        page_start: int,
        page_end: int,
        start_order: int
    ) -> List[Chunk]:
        """One chunk per data row, with the header row repeated for context."""
        header_lines = []
        data_lines = []
        seen_separator = False

        for line in table_lines:
            if self.TABLE_SEPARATOR_RE.match(line):
                seen_separator = True
                continue
            if not seen_separator:
                header_lines.append(line)
            else:
                data_lines.append(line)

        if not seen_separator:
            # No "|---|---|" separator found; assume the first row is the header.
            header_lines, data_lines = table_lines[:1], table_lines[1:]

        header_text = "\n".join(l for l in header_lines if l.strip()).strip()

        chunks = []
        for row in data_lines:
            if not row.strip():
                continue
            content = f"{header_text}\n{row.strip()}" if header_text else row.strip()
            chunks.append(Chunk(
                content=content,
                section_header=section_header,
                page_start=page_start,
                page_end=page_end,
                chunk_type="table",
                chunk_order=start_order + len(chunks),
                metadata={"is_table_row": True}
            ))
        return chunks

    def _chunk_prose(
        self,
        text: str,
        section_header: str = "",
        page_start: int = 0,
        page_end: int = 0,
        chunk_type: str = "text",
        start_order: int = 0
    ) -> List[Chunk]:
        """Chunk non-tabular text: single chunk if short, else split with overlap."""
        if not text or not text.strip():
            return []

        estimated_tokens = len(text) // 4

        if estimated_tokens <= self.chunk_size:
            return [Chunk(
                content=text.strip(),
                section_header=section_header,
                page_start=page_start,
                page_end=page_end,
                chunk_type=chunk_type,
                chunk_order=start_order,
                metadata={}
            )]

        return self._chunk_with_overlap(
            text, section_header, page_start, page_end, chunk_type, start_order
        )
    
    def _chunk_with_overlap(
        self,
        text: str,
        section_header: str,
        page_start: int,
        page_end: int,
        chunk_type: str,
        start_order: int = 0
    ) -> List[Chunk]:
        """Split text into chunks with overlap."""
        chunks = []

        # Split by paragraphs first
        paragraphs = self._split_paragraphs(text)

        current_chunk = []
        current_length = 0
        chunk_order = start_order
        
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

            def flush(pieces: List[str]):
                """Append a sentence-grouped chunk, hard-splitting it first if
                a single sentence (e.g. an unpunctuated block of text) made it
                exceed the target size on its own."""
                text = " ".join(pieces).strip()
                if not text:
                    return
                if len(text) // 4 > self.chunk_size:
                    chunks.extend(self._split_by_char_count(
                        text, section_header, page_start, page_end, chunk_type,
                        start_order + len(chunks)
                    ))
                else:
                    chunks.append(Chunk(
                        content=text,
                        section_header=section_header,
                        page_start=page_start,
                        page_end=page_end,
                        chunk_type=chunk_type,
                        chunk_order=start_order + len(chunks),
                        metadata={}
                    ))

            for sentence in sentences:
                sentence_length = len(sentence) // 4

                if current_length + sentence_length > self.chunk_size:
                    if current_chunk:
                        flush(current_chunk)
                        # Overlap: keep last sentence of the current chunk
                        current_chunk = [current_chunk[-1]]
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
                flush(current_chunk)
        else:
            # Fallback: split by fixed character count
            chunks.extend(self._split_by_char_count(
                paragraph, section_header, page_start, page_end, chunk_type, start_order
            ))

        return chunks

    def _split_by_char_count(
        self,
        text: str,
        section_header: str,
        page_start: int,
        page_end: int,
        chunk_type: str,
        start_order: int
    ) -> List['Chunk']:
        """Split text into fixed-size chunks, breaking at word boundaries where possible."""
        chunks = []
        start_idx = 0
        chunk_order = start_order

        while start_idx < len(text):
            end_idx = min(start_idx + self.chunk_size * 4, len(text))

            # Try to break at word boundary
            if end_idx < len(text):
                last_space = text.rfind(' ', start_idx, end_idx)
                if last_space > start_idx:
                    end_idx = last_space

            chunk_content = text[start_idx:end_idx].strip()
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
