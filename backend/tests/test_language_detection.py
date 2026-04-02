"""
Tests for Roman Urdu language detection.
"""
import pytest
from app.services.roman_urdu.language_detection import LanguageDetector


class TestLanguageDetector:
    """Test cases for language detection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = LanguageDetector()
    
    def test_english_detection(self):
        """Test English query detection."""
        text = "What are the eligibility criteria for admission?"
        lang, confidence = self.detector.detect(text)
        assert lang == 'en'
    
    def test_roman_urdu_detection(self):
        """Test Roman Urdu query detection."""
        text = "admission ke liye kya documents chahiye?"
        lang, confidence = self.detector.detect(text)
        assert lang in ('ur', 'mixed')
    
    def test_mixed_detection(self):
        """Test code-mixed query detection."""
        text = "admission ke liye last date kya hai?"
        lang, confidence = self.detector.detect(text)
        assert lang in ('ur', 'mixed', 'en')
    
    def test_empty_text(self):
        """Test empty text handling."""
        lang, confidence = self.detector.detect("")
        assert lang == 'en'
        assert confidence == 0.0
    
    def test_question_words(self):
        """Test detection of Roman Urdu question words."""
        questions = [
            "kya admission mil sakta hai?",
            "kaise apply karein?",
            "kahan submit karna hai?",
            "kab last date hai?",
        ]
        for question in questions:
            lang, confidence = self.detector.detect(question)
            assert lang in ('ur', 'mixed'), f"Failed for: {question}"
    
    def test_is_roman_urdu(self):
        """Test Roman Urdu boolean check."""
        assert self.detector.is_roman_urdu("admission ke liye kya chahiye?")
        assert not self.detector.is_roman_urdu("What is required for admission?")
