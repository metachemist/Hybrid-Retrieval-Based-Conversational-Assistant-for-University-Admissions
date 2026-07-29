"""
Image Processor Module

Extracts text from image-based admission notices (JPG/PNG scans with no
embedded text layer) using OpenAI's vision model. Mirrors PDFProcessor's
interface so the ingestion pipeline can treat both uniformly.
"""
import base64
import logging
import os
import re
from typing import List, Optional, Tuple

from openai import OpenAI

from app.core.config import settings
from .pdf_processor import ExtractedSection, PDFMetadata

logger = logging.getLogger(__name__)

TRANSCRIPTION_PROMPT = (
    "This is a public admissions notice published on a university website (not "
    "an identity document or personal record). Transcribe all text visible in "
    "the image exactly as written, preserving structure (headings, lists). "
    "Any tabular content MUST be transcribed as a GitHub-flavored markdown "
    "table (`| col | col |` rows with a `|---|---|` header separator) - never "
    "use tabs or aligned spacing for tables. Do not summarize, translate, or "
    "add commentary - output only the transcribed text."
)

_CODE_FENCE_RE = re.compile(r'^```[a-zA-Z]*\n|\n```$|^```$', re.MULTILINE)


class ImageProcessor:
    """Extracts text from image notices via OpenAI vision."""

    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self._client = None
        self._transcription_cache = {}

    def _get_client(self) -> OpenAI:
        if self._client is None:
            self._client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=30.0)
        return self._client

    def extract(self, file_path: str) -> Tuple[str, PDFMetadata]:
        """Extract text and metadata from an image file."""
        text = self._transcribe(file_path)

        title = os.path.splitext(os.path.basename(file_path))[0]
        year = self._extract_year(text) or self._extract_year(title)

        metadata = PDFMetadata(
            title=title,
            year=year,
            total_pages=1,
            source_path=file_path
        )
        return text, metadata

    def extract_with_sections(self, file_path: str) -> List[ExtractedSection]:
        """Extract text as a single section (images have no page/section structure)."""
        text = self._transcribe(file_path)
        if not text.strip():
            return []

        return [ExtractedSection(
            content=text,
            section_header="General",
            page_start=0,
            page_end=0,
            chunk_type="text",
            metadata={"doc_path": file_path}
        )]

    def _transcribe(self, file_path: str) -> str:
        """Send the image to OpenAI vision and return the transcribed text.

        Cached per file_path so extract() and extract_with_sections() - both
        called during ingestion - reuse one transcription instead of paying
        for (and risking a differently-formatted) second vision call.
        """
        if file_path in self._transcription_cache:
            return self._transcription_cache[file_path]

        client = self._get_client()

        with open(file_path, "rb") as f:
            image_bytes = f.read()
        b64 = base64.b64encode(image_bytes).decode("utf-8")

        ext = os.path.splitext(file_path)[1].lstrip(".").lower()
        mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

        response = client.chat.completions.create(
            model=self.model,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": TRANSCRIPTION_PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ],
            }],
            temperature=0,
            max_tokens=4096,
        )
        if response.choices[0].finish_reason == "length":
            logger.warning("Vision transcription hit max_tokens and was truncated: %s", file_path)
        text = response.choices[0].message.content or ""
        text = _CODE_FENCE_RE.sub("", text).strip()
        self._transcription_cache[file_path] = text
        return text

    def _extract_year(self, text: str) -> Optional[int]:
        match = re.search(r'((19|20)\d{2})', text)
        return int(match.group(1)) if match else None
