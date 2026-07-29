"""
RAG Prompt Builder

Constructs prompts for the LLM with retrieved context and citation instructions.
"""
from typing import List, Dict, Optional
from dataclasses import dataclass

from app.models import Chunk


@dataclass
class Citation:
    """Represents a citation for a retrieved chunk."""
    document_title: str
    section_header: str
    page_start: int
    page_end: int
    chunk_index: int
    
    def format(self) -> str:
        """Format citation for display."""
        pages = f"p. {self.page_start}"
        if self.page_end and self.page_end != self.page_start:
            pages += f"-{self.page_end}"
        return f"[{self.document_title}: {self.section_header}, {pages}]"
    
    def marker(self) -> str:
        """Get inline citation marker."""
        return f"[{self.chunk_index}]"


class RAGPromptBuilder:
    """
    Builds prompts for RAG-based answer generation.
    
    Features:
    - Context assembly from retrieved chunks
    - Citation tracking
    - Language-aware response instructions
    - Hallucination prevention
    """
    
    SYSTEM_PROMPT = """You are an admission policy assistant for the University of Karachi.
Your role is to help prospective students understand admission requirements, procedures, and policies.

IMPORTANT RULES:
1. Answer ONLY based on the provided context. Do not use outside knowledge.
2. If the context doesn't contain enough information, say "I don't have enough information to answer this question."
3. Always include citations when making factual claims. Use the format [1], [2], etc.
4. Respond in the same language as the user's query (English or Roman Urdu).
5. Keep responses clear, concise, and easy to understand.
6. If asked about something not related to admissions, politely redirect to admission topics.
7. Do not predict admission chances or merit rankings.
8. Always remind users to verify information with official admission office.
9. Quote numbers (fees, dates, percentages, scores) EXACTLY as they appear in the
   source text - character for character, including comma placement. Some figures
   use South Asian lakh-style grouping (e.g. "6,50,000" means 650,000, not 6,500
   or 6.5). Never round, reformat, reinterpret, or recompute a number from the
   source; copy it verbatim.

Remember: Your responses must be grounded in the provided documents."""

    def __init__(self, max_context_tokens: int = 4000):
        """
        Initialize the prompt builder.
        
        Args:
            max_context_tokens: Maximum tokens for context
        """
        self.max_context_tokens = max_context_tokens
    
    def build(
        self,
        query: str,
        chunks: List[Chunk],
        documents: Dict[str, str],  # chunk_id -> document_title
        language: str = "en"
    ) -> tuple[str, List[Citation]]:
        """
        Build a RAG prompt with context and citations.
        
        Args:
            query: User query
            chunks: Retrieved chunks
            documents: Map of chunk IDs to document titles
            language: Language code ('en' or 'ur')
            
        Returns:
            Tuple of (prompt, citations)
        """
        # Build context from chunks
        context_parts = []
        citations = []
        
        for i, chunk in enumerate(chunks):
            doc_title = documents.get(str(chunk.doc_id), "Unknown Document")
            
            citation = Citation(
                document_title=doc_title,
                section_header=chunk.section_header or "N/A",
                page_start=chunk.page_start or 0,
                page_end=chunk.page_end or 0,
                chunk_index=i + 1
            )
            citations.append(citation)
            
            context_parts.append(
                f"[{i + 1}] {chunk.content}\n"
                f"    Source: {doc_title}, Section: {chunk.section_header or 'N/A'}, "
                f"Pages: {chunk.page_start or '?'}-{chunk.page_end or '?'}"
            )
        
        context = "\n\n".join(context_parts)
        
        # Build language-specific instructions
        if language == "ur":
            lang_instruction = "Respond in Roman Urdu (Urdu written in Latin script)."
        else:
            lang_instruction = "Respond in English."
        
        # Build the prompt
        prompt = f"""{context}

---
User Query: {query}

{lang_instruction}
Remember to cite your sources using [1], [2], etc.
"""
        
        return prompt, citations
    
    def build_condensed(
        self,
        query: str,
        chunks: List[Chunk],
        documents: Dict[str, str],
        max_chunks: int = 5
    ) -> tuple[str, List[Citation]]:
        """
        Build a condensed prompt with top chunks.
        
        Args:
            query: User query
            chunks: Retrieved chunks (already ranked)
            documents: Map of chunk IDs to document titles
            max_chunks: Maximum number of chunks to include
            
        Returns:
            Tuple of (prompt, citations)
        """
        # Take top chunks
        selected_chunks = chunks[:max_chunks]
        return self.build(query, selected_chunks, documents)
    
    def format_citations(self, citations: List[Citation]) -> str:
        """Format citations for display."""
        if not citations:
            return ""
        
        formatted = []
        for citation in citations:
            formatted.append(f"{citation.marker()} {citation.format()}")
        
        return "\n".join(formatted)
    
    def extract_citation_markers(self, text: str) -> List[int]:
        """
        Extract citation markers from generated text.
        
        Args:
            text: Generated response text
            
        Returns:
            List of citation indices
        """
        import re
        markers = re.findall(r'\[(\d+)\]', text)
        return [int(m) for m in markers]
    
    def validate_citations(
        self,
        response: str,
        citations: List[Citation]
    ) -> Dict:
        """
        Validate that response includes proper citations.
        
        Args:
            response: Generated response
            citations: Available citations
            
        Returns:
            Validation results
        """
        markers = self.extract_citation_markers(response)
        
        return {
            "has_citations": len(markers) > 0,
            "citation_count": len(markers),
            "valid_citations": [m for m in markers if 1 <= m <= len(citations)],
            "invalid_citations": [m for m in markers if m < 1 or m > len(citations)],
            "all_valid": all(1 <= m <= len(citations) for m in markers)
        }


def create_rag_prompt(
    query: str,
    chunks: List[Chunk],
    documents: Dict[str, str],
    max_chunks: int = 5
) -> tuple[str, str, List[Citation]]:
    """
    Convenience function to create a complete RAG prompt.
    
    Args:
        query: User query
        chunks: Retrieved chunks
        documents: Map of chunk IDs to document titles
        max_chunks: Maximum chunks to include
        
    Returns:
        Tuple of (system_prompt, user_prompt, citations)
    """
    builder = RAGPromptBuilder()
    user_prompt, citations = builder.build_condensed(query, chunks, documents, max_chunks)
    return RAGPromptBuilder.SYSTEM_PROMPT, user_prompt, citations
