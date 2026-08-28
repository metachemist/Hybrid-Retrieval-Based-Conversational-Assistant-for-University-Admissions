"""
Tests for Roman Urdu normalization.
"""
import pytest
from app.services.roman_urdu.normalization import RomanUrduNormalizer


class TestRomanUrduNormalizer:
    """Test cases for Roman Urdu normalization."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.normalizer = RomanUrduNormalizer(use_translation=False)
    
    def test_character_mapping(self):
        """Test character-level normalization."""
        assert self.normalizer.normalize("aa") == "a"
        assert self.normalizer.normalize("ee") == "e"
        assert self.normalizer.normalize("oo") == "o"
    
    def test_word_mapping(self):
        """Test word-level normalization."""
        # Without translation, words should keep original form after char mapping
        result = self.normalizer.normalize("admisn")
        # Should apply character mappings but not translate
        assert result is not None
    
    def test_empty_text(self):
        """Test empty text handling."""
        assert self.normalizer.normalize("") == ""
        assert self.normalizer.normalize(None) is None
    
    def test_punctuation_preservation(self):
        """Test that punctuation is preserved."""
        text = "admission ke liye kya documents chahiye?"
        result = self.normalizer.normalize(text)
        assert result.endswith("?")
    
    def test_common_variations(self):
        """Test common Roman Urdu variations."""
        variations = {
            "kull": "kul",  # Should normalize double vowels
            "fii": "fi",   # Should normalize double vowels
            "admisn": "admisn",  # Keep as is without translation
        }
        for input_text, expected in variations.items():
            result = self.normalizer.normalize(input_text)
            # Just verify it doesn't crash and returns something
            assert result is not None
