"""
PDF Processor Module

Extracts text and metadata from PDF documents using PyMuPDF.
Handles admission prospectus and policy documents.
"""
import fitz  # PyMuPDF
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import re


@dataclass
class ExtractedSection:
    """Represents a section extracted from a PDF."""
    content: str
    section_header: str
    page_start: int
    page_end: int
    chunk_type: str  # 'text', 'table', 'list'
    metadata: Dict


@dataclass
class PDFMetadata:
    """Metadata extracted from a PDF document."""
    title: str
    year: Optional[int]
    total_pages: int
    source_path: str


class PDFProcessor:
    """
    Process PDF documents for the admission chatbot.
    
    Features:
    - Text extraction with page preservation
    - Section detection based on headings
    - Table extraction
    - Noise removal (headers, footers, page numbers)
    """
    
    # Patterns for detecting section headers
    HEADER_PATTERNS = [
        r'^CHAPTER\s+\d+',
        r'^SECTION\s+\d+',
        r'^\d+\.\s+[A-Z]',  # "1. Introduction"
        r'^\d+\.\d+\s+[A-Z]',  # "1.1 Subsection"
        r'^[A-Z][A-Z\s]+$',  # All caps headers
        r'^ELIGIBILITY',
        r'^ADMISSION',
        r'^REQUIREMENTS',
        r'^DEADLINE',
        r'^FEE',
        r'^PROGRAM',
        r'^COURSE',
    ]
    
    # Patterns for noise to remove
    NOISE_PATTERNS = [
        r'^Page\s+\d+\s*$',
        r'^\d+\s*$',  # Standalone page numbers
        r'^University\s+of\s+Karachi\s*$',  # Repeated headers
        r'^Admission\s+Prospectus\s*$',
        r'^www\.uok\.edu\.pk\s*$',  # Website URLs in footer
        r'^\d{4}\s*$',  # Year in footer
    ]
    
    def __init__(self):
        self.header_regex = [
            re.compile(pattern, re.MULTILINE | re.IGNORECASE)
            for pattern in self.HEADER_PATTERNS
        ]
        self.noise_regex = [
            re.compile(pattern, re.MULTILINE | re.IGNORECASE)
            for pattern in self.NOISE_PATTERNS
        ]
    
    def extract(self, file_path: str) -> Tuple[str, PDFMetadata]:
        """
        Extract text and metadata from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Tuple of (full_text, metadata)
        """
        doc = fitz.open(file_path)
        
        # Extract metadata
        metadata = self._extract_metadata(doc, file_path)
        
        # Extract text page by page
        pages_text = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            cleaned_text = self._clean_page(text, page_num)
            pages_text.append(cleaned_text)
        
        doc.close()
        
        full_text = "\n\n".join(pages_text)
        return full_text, metadata
    
    def extract_with_sections(self, file_path: str) -> List[ExtractedSection]:
        """
        Extract text organized by sections.

        Pages before the first detected header are grouped under a "General"
        section so no content is silently dropped.

        Args:
            file_path: Path to the PDF file

        Returns:
            List of ExtractedSection objects
        """
        doc = fitz.open(file_path)
        sections = []

        current_section = "General"
        current_content = []
        current_page_start = 0

        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text("text")
            cleaned_text = self._clean_page(text, page_num)

            section_header = self._detect_section_header(cleaned_text)

            if section_header and section_header != current_section:
                # Save previous section (skip empty ones)
                combined = "\n".join(current_content).strip()
                if combined:
                    sections.append(ExtractedSection(
                        content=combined,
                        section_header=current_section,
                        page_start=current_page_start,
                        page_end=page_num - 1 if page_num > 0 else page_num,
                        chunk_type="text",
                        metadata={"doc_path": file_path}
                    ))

                current_section = section_header
                current_content = [cleaned_text]
                current_page_start = page_num
            else:
                current_content.append(cleaned_text)

        # Save last section
        combined = "\n".join(current_content).strip()
        if combined:
            sections.append(ExtractedSection(
                content=combined,
                section_header=current_section,
                page_start=current_page_start,
                page_end=len(doc) - 1,
                chunk_type="text",
                metadata={"doc_path": file_path}
            ))

        doc.close()
        return sections
    
    def _extract_metadata(self, doc: fitz.Document, file_path: str) -> PDFMetadata:
        """Extract metadata from PDF."""
        # Try to get title from PDF metadata
        meta = doc.metadata
        title = meta.get("title", "")
        
        # If no title, infer from filename
        if not title:
            import os
            title = os.path.splitext(os.path.basename(file_path))[0]
        
        # Try to extract year from title or content
        year = self._extract_year(title)
        if not year and len(doc) > 0:
            first_page_text = doc[0].get_text("text")
            year = self._extract_year(first_page_text)
        
        return PDFMetadata(
            title=title,
            year=year,
            total_pages=len(doc),
            source_path=file_path
        )
    
    def _extract_year(self, text: str) -> Optional[int]:
        """Extract year from text."""
        # Each tuple: (pattern, group_index_with_the_year)
        patterns = [
            (r'Academic\s+Session\s+((19|20)\d{2})', 1),
            (r'Session\s+((19|20)\d{2})', 1),
            (r'((19|20)\d{2})', 1),  # fallback: any 4-digit year
        ]

        for pattern, group in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(group))

        return None
    
    def _clean_page(self, text: str, page_num: int) -> str:
        """Clean extracted text by removing noise."""
        lines = text.split("\n")
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip noise patterns
            is_noise = False
            for pattern in self.noise_regex:
                if pattern.search(line):
                    is_noise = True
                    break
            
            if not is_noise and line:
                cleaned_lines.append(line)
        
        return "\n".join(cleaned_lines)
    
    def _detect_section_header(self, text: str) -> Optional[str]:
        """Detect if text contains a section header."""
        lines = text.split("\n")
        
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            for pattern in self.header_regex:
                if pattern.match(line):
                    return line
        
        return None
    
    def extract_tables(self, file_path: str) -> List[Dict]:
        """
        Extract tables from PDF.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of table data with metadata
        """
        doc = fitz.open(file_path)
        tables = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            # PyMuPDF can extract tables as blocks
            blocks = page.get_text("dict")["blocks"]
            
            for block in blocks:
                if block.get("type") == 1:  # Image block, skip
                    continue
                
                # Simple table detection based on structure
                # For better table extraction, use 'unstructured' library
                pass
        
        doc.close()
        return tables


def process_pdf(file_path: str) -> Tuple[str, PDFMetadata, List[ExtractedSection]]:
    """
    Convenience function to process a PDF file.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Tuple of (full_text, metadata, sections)
    """
    processor = PDFProcessor()
    full_text, metadata = processor.extract(file_path)
    sections = processor.extract_with_sections(file_path)
    return full_text, metadata, sections
