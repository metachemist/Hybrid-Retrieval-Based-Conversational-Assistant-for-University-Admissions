"""
Language Detection Module

Detects whether a query is in English, Roman Urdu, or code-mixed.
Uses fasttext for initial detection with custom rules for Roman Urdu.
"""
import re
from typing import Tuple
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

# Set seed for reproducibility
DetectorFactory.seed = 0


class LanguageDetector:
    """
    Detects language of input text with support for:
    - English (en)
    - Roman Urdu (ur)
    - Code-mixed (mixed)
    """
    
    # Roman Urdu specific patterns
    ROMAN_URDU_PATTERNS = [
        r'\b(kya|kaise|kahan|kab|kyun|kaun)\b',  # Question words
        r'\b(hai|tha|tha|hoga|hain)\b',  # Verb forms
        r'\b(mera|teri|uska|hamara|unka)\b',  # Possessives
        r'\b(aur|lekin|par|ya|toh|phir)\b',  # Conjunctions
        r'\b(admission|fee|document|form|date|last)\b.*\b(chahiye|hoga|hai|tha)\b',  # Common patterns
    ]
    
    # Common Roman Urdu words for admission context
    ADMISSION_ROMAN_URDU_WORDS = {
        'kal', 'kull', 'kul',  # university
        'admisn', 'admission', 'admn',
        'fee', 'fii', 'fees',
        'form', 'forme', 'from',
        'date', 'dat', 'deed',
        'last', 'laast',
        'chahiye', 'chaiye', 'chiye',
        'kaise', 'kese', 'kesay',
        'kya', 'kyaa', 'ky',
        'hai', 'he', 'hy',
        'hoga', 'hoga', 'hoga',
        'mein', 'men', 'main',
        'liye', 'liye', 'lye',
        'waali', 'wali', 'vaali',
        'degree', 'digree',
        'program', 'programme',
        'course', 'cours',
    }
    
    def __init__(self):
        self.roman_urdu_regex = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.ROMAN_URDU_PATTERNS
        ]
    
    def detect(self, text: str) -> Tuple[str, float]:
        """
        Detect the language of the input text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Tuple of (language_code, confidence)
            - 'ur': Roman Urdu
            - 'en': English
            - 'mixed': Code-mixed
        """
        text = text.strip().lower()
        
        if not text:
            return ('en', 0.0)
        
        # Count Roman Urdu indicators
        roman_urdu_score = self._calculate_roman_urdu_score(text)
        
        # Try langdetect for baseline
        try:
            detected_lang = detect(text)
        except LangDetectException:
            detected_lang = 'en'
        
        # Decision logic
        if roman_urdu_score >= 0.5:
            if detected_lang == 'en':
                # Mixed English and Roman Urdu
                return ('mixed', roman_urdu_score)
            else:
                return ('ur', roman_urdu_score)
        else:
            return ('en', 1.0 - roman_urdu_score)
    
    def _calculate_roman_urdu_score(self, text: str) -> float:
        """
        Calculate a score indicating how likely the text is Roman Urdu.
        
        Args:
            text: Input text (should be lowercase)
            
        Returns:
            Score between 0 and 1
        """
        score = 0.0
        max_score = 0.0
        
        # Check for Roman Urdu patterns
        for pattern in self.roman_urdu_regex:
            if pattern.search(text):
                score += 0.2
            max_score += 0.2
        
        # Check for Roman Urdu words
        words = set(re.findall(r'\b\w+\b', text))
        roman_urdu_matches = sum(
            1 for word in words 
            if word in self.ADMISSION_ROMAN_URDU_WORDS
        )
        score += min(roman_urdu_matches * 0.1, 0.4)
        max_score += 0.4
        
        # Check for characteristic Roman Urdu spellings
        # Double vowels (aa, ee, oo)
        double_vowel_count = len(re.findall(r'(aa|ee|oo|ii|uu)', text))
        score += min(double_vowel_count * 0.05, 0.2)
        max_score += 0.2
        
        # Normalize score
        if max_score > 0:
            return min(score / max_score, 1.0)
        return 0.0
    
    def is_roman_urdu(self, text: str, threshold: float = 0.5) -> bool:
        """
        Check if text is Roman Urdu.
        
        Args:
            text: Input text
            threshold: Confidence threshold
            
        Returns:
            True if Roman Urdu
        """
        lang, confidence = self.detect(text)
        return lang in ('ur', 'mixed') and confidence >= threshold


# Singleton instance
_language_detector = None


def get_language_detector() -> LanguageDetector:
    """Get or create the language detector singleton."""
    global _language_detector
    if _language_detector is None:
        _language_detector = LanguageDetector()
    return _language_detector
