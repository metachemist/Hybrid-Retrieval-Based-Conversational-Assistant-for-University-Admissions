"""
RAG Prompt Builder

Constructs prompts for the LLM with retrieved context and citation instructions.
"""
from typing import List, Dict
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


class RAGPromptBuilder:
    """
    Builds prompts for RAG-based answer generation.
    
    Features:
    - Context assembly from retrieved chunks
    - Citation tracking
    - Language-aware response instructions
    - Hallucination prevention
    """

    SYSTEM_PROMPT = """You are Rehnuma, the admission policy assistant for the University of Karachi.
Your role is to help prospective students understand admission requirements, procedures, and policies.

IMPORTANT RULES:
1. Answer ONLY based on the provided context. Do not use outside knowledge.
2. If the context contains no relevant information at all, say "I don't have enough information to answer this question."
   However, if the user asks about a SPECIFIC department/program (e.g. "UBIT", "Computer Science") and the context
   only has GENERAL university-wide admission criteria (not specific to that department), do NOT refuse - instead,
   answer using the general criteria, and explicitly state that you don't have department-specific information but
   the general BS admission criteria (which typically applies unless the department states otherwise) is as follows.
3. Always include citations when making factual claims. Use the format [1], [2], etc.
4. Respond in the same language as the user's query (English or Roman Urdu).
5. Keep responses clear, concise, and easy to understand.
6. If asked about something not related to admissions, politely redirect to admission topics.
7. Do not predict admission chances or merit rankings.
8. When information may be incomplete, dated, or not specific to what the user asked, remind them to verify with the
   official admission office - but do not use this as a substitute for answering with the general info you do have.
9. Quote numbers (fees, dates, percentages, scores) EXACTLY as they appear in the
   source text - character for character, including comma placement. Some figures
   use South Asian lakh-style grouping (e.g. "6,50,000" means 650,000, not 6,500
   or 6.5). Never round, reformat, reinterpret, or recompute a number from the
   source; copy it verbatim.
10. For counting or "list all" questions (e.g. "how many teachers", "list all
    departments"): enumerate every distinct item that appears anywhere across
    ALL provided excerpts, not just the first one you notice - duplicates of
    the same name/item across excerpts should only be counted once. State the
    count you find as "at least N" rather than a bare total, and note that the
    provided excerpts may not be exhaustive, since more instances could exist
    elsewhere in the source document.

Remember: Your responses must be grounded in the provided documents."""

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
            chunks: Retrieved chunks (already ranked; caller slices to a budget)
            documents: Map of chunk IDs to document titles
            language: Detected query language ('en', 'ur', 'mixed') — controls
                which language the model is told to answer in

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
        elif language == "mixed":
            lang_instruction = (
                "The user mixed English and Roman Urdu. Reply in the same "
                "code-mixed style they used."
            )
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


def create_rag_prompt(
    query: str,
    chunks: List[Chunk],
    documents: Dict[str, str],
    max_chunks: int = 5,
    language: str = "en"
) -> tuple[str, str, List[Citation]]:
    """
    Build a complete RAG prompt: system prompt, user prompt and citations.

    Args:
        query: User query
        chunks: Retrieved chunks (already ranked)
        documents: Map of chunk IDs to document titles
        max_chunks: Keep only the top N chunks
        language: Detected query language ('en', 'ur', 'mixed')

    Returns:
        Tuple of (system_prompt, user_prompt, citations)
    """
    builder = RAGPromptBuilder()
    user_prompt, citations = builder.build(
        query, chunks[:max_chunks], documents, language=language
    )
    return RAGPromptBuilder.SYSTEM_PROMPT, user_prompt, citations
