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
    
    # Tokens that are unambiguously Roman Urdu — function words, pronouns,
    # postpositions and common verb forms. Words that collide with ordinary
    # English ("the", "he", "or", "to", "par", "is", "us", "main", "so", "in")
    # are deliberately left out so English and code-mixed queries are not
    # dragged across the line by a single coincidental token.
    ROMAN_URDU_MARKERS = {
        # question / quantity words
        'kya', 'kyaa', 'kaise', 'kaisay', 'kese', 'kaisa', 'kaisi',
        'kahan', 'kahaan', 'kab', 'kyun', 'kyon', 'kaun', 'kaunsa', 'konsa',
        'kitna', 'kitni', 'kitne',
        # verbs / auxiliaries
        'hai', 'hain', 'tha', 'thi', 'hoga', 'hogi', 'honge', 'hota', 'hoti',
        'karna', 'karni', 'karne', 'karein', 'karo', 'karun', 'karoon',
        'kiya', 'kiye', 'kar', 'krna', 'krein',
        'mil', 'milega', 'milegi', 'milta', 'milti',
        'sakta', 'sakti', 'sakte', 'chahiye', 'chaiye', 'chahye', 'chahiyay',
        'raha', 'rahi', 'rahe', 'gaya', 'gayi',
        # postpositions / pronouns / determiners
        'ke', 'ki', 'ka', 'ko', 'se', 'mein', 'pe', 'liye', 'lye',
        'wala', 'waala', 'wali', 'waali', 'wale', 'walay',
        'mera', 'meri', 'mere', 'apna', 'apni', 'yeh', 'ye', 'woh', 'wo',
        'iska', 'uska', 'hamara', 'humara', 'unka', 'aap',
        # common adverbs / particles
        'nahi', 'nahin', 'haan', 'kuch', 'sab', 'zyada', 'thoda',
        'bhi', 'sirf', 'phir', 'magar', 'lekin', 'warna', 'abhi',
        # frequent misspellings of admission-domain terms
        'admisn', 'admn', 'addmission', 'admisison',
        'fii', 'forme', 'laast', 'digree', 'kul', 'kull',
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

        # Fraction of the query that reads as Roman Urdu, 0..1
        roman_urdu_score = self._calculate_roman_urdu_score(text)

        # Try langdetect for baseline
        try:
            detected_lang = detect(text)
        except LangDetectException:
            detected_lang = 'en'

        # Decision logic. The threshold is a fraction of tokens, not an absolute
        # count, so a two-word Roman Urdu question is not out-voted by the fixed
        # ceiling the old additive score divided against.
        if roman_urdu_score >= 0.30:
            if detected_lang == 'en':
                # langdetect still reads it as English -> genuinely code-mixed
                return ('mixed', roman_urdu_score)
            return ('ur', roman_urdu_score)
        return ('en', 1.0 - roman_urdu_score)

    def _calculate_roman_urdu_score(self, text: str) -> float:
        """
        Fraction of the query that looks like Roman Urdu (0..1).

        Counts tokens that are unambiguous Roman Urdu markers plus any
        multi-word Roman Urdu phrase patterns, then divides by the token
        count. A query made entirely of Roman Urdu function words scores ~1.0;
        one English loanword ("apply", "documents") in an otherwise Roman Urdu
        question no longer drags it under the line.

        Args:
            text: Input text (lowercase)

        Returns:
            Score between 0 and 1
        """
        tokens = re.findall(r'[a-z]+', text)
        if not tokens:
            return 0.0

        hits = sum(1 for t in tokens if t in self.ROMAN_URDU_MARKERS)

        # Multi-word Roman Urdu phrasing ("... chahiye", "kya ... hai") each
        # count once more, so short but clearly Urdu questions clear the bar.
        for pattern in self.roman_urdu_regex:
            if pattern.search(text):
                hits += 1

        return min(hits / len(tokens), 1.0)
    
    def is_roman_urdu(self, text: str, threshold: float = 0.30) -> bool:
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
