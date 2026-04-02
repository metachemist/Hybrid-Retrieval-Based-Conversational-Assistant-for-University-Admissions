"""
Roman Urdu Normalization Module

Normalizes Roman Urdu text by:
- Mapping character variations (aa→a, ee→e, oo→o)
- Correcting common spelling variations
- Standardizing common words
"""
import re
from typing import Dict, List, Optional
from difflib import SequenceMatcher


class RomanUrduNormalizer:
    """
    Normalizes Roman Urdu text to standard spelling.
    """
    
    # Character mapping for common variations
    CHARACTER_MAPPINGS = {
        'aa': 'a',
        'aaa': 'a',
        'ee': 'e',
        'eee': 'e',
        'oo': 'o',
        'ooo': 'o',
        'ii': 'i',
        'iii': 'i',
        'uu': 'u',
        'uuu': 'u',
        'ae': 'a',
        'ai': 'a',
        'ao': 'a',
        'ei': 'e',
        'ea': 'e',
        'ie': 'e',
        'oa': 'o',
        'oe': 'o',
        'io': 'o',
        'ui': 'u',
        'iu': 'u',
    }
    
    # Common word normalizations (admission context)
    WORD_MAPPINGS = {
        # University related
        'kal': 'university',
        'kull': 'university',
        'kul': 'university',
        'uni': 'university',
        'varsity': 'university',
        
        # Admission related
        'admisn': 'admission',
        'admn': 'admission',
        'addmission': 'admission',
        'admisison': 'admission',
        
        # Document related
        'doc': 'document',
        'docs': 'documents',
        'documentz': 'documents',
        'documnet': 'document',
        'documnets': 'documents',
        
        # Fee related
        'fii': 'fee',
        'fees': 'fee',
        'fe': 'fee',
        
        # Form related
        'forme': 'form',
        'from': 'form',
        'formm': 'form',
        
        # Date/Time related
        'dat': 'date',
        'deed': 'date',
        'last': 'last',
        'laast': 'last',
        'final': 'final',
        
        # Question words
        'kya': 'what',
        'kyaa': 'what',
        'ky': 'what',
        'kaise': 'how',
        'kese': 'how',
        'kesay': 'how',
        'kahan': 'where',
        'kahan': 'where',
        'kab': 'when',
        'kyun': 'why',
        'q': 'why',
        'kaun': 'who',
        'kon': 'who',
        
        # Verbs
        'hai': 'is',
        'he': 'is',
        'hy': 'is',
        'hai': 'is',
        'tha': 'was',
        'tha': 'was',
        'hoga': 'will be',
        'honge': 'will be',
        'hain': 'are',
        'hein': 'are',
        
        # Possessives
        'mera': 'my',
        'meri': 'my',
        'mera': 'my',
        'tera': 'your',
        'teri': 'your',
        'uska': 'his/her',
        'uski': 'his/her',
        'hamara': 'our',
        'hamari': 'our',
        'unka': 'their',
        'unki': 'their',
        
        # Conjunctions
        'aur': 'and',
        'or': 'and',
        'lekin': 'but',
        'lekun': 'but',
        'par': 'but',
        'ya': 'or',
        'toh': 'then',
        'to': 'then',
        'phir': 'then',
        'fir': 'then',
        
        # Prepositions
        'mein': 'in',
        'men': 'in',
        'main': 'in',
        'se': 'from',
        'say': 'from',
        'ko': 'to',
        'ke': 'of',
        'ki': 'of',
        'ka': 'of',
        
        # Requirements
        'chahiye': 'needed',
        'chaiye': 'needed',
        'chiye': 'needed',
        'lagta': 'required',
        'lagte': 'required',
        'lagti': 'required',
        
        # Programs
        'degree': 'degree',
        'digree': 'degree',
        'program': 'program',
        'programme': 'program',
        'course': 'course',
        'cours': 'course',
        
        # Eligibility
        'eligible': 'eligible',
        'eligible': 'eligible',
        'apply': 'apply',
        'apply': 'apply',
        'qualification': 'qualification',
        'qualifiction': 'qualification',
        
        # Merit
        'merit': 'merit',
        'marit': 'merit',
        'percentage': 'percentage',
        'percent': 'percent',
        'marks': 'marks',
        'mark': 'mark',
        
        # Process
        'process': 'process',
        'proces': 'process',
        'procedure': 'procedure',
        'apply': 'apply',
        'submission': 'submission',
        'submit': 'submit',
    }
    
    # Suffix patterns
    SUFFIX_MAPPINGS = {
        'iyat': 'ity',
        'iyth': 'ity',
        'tion': 'tion',
        'sion': 'sion',
    }
    
    def __init__(self, use_translation: bool = False):
        """
        Initialize the normalizer.
        
        Args:
            use_translation: If True, translate Roman Urdu to English.
                           If False, just normalize spelling.
        """
        self.use_translation = use_translation
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for character mappings."""
        self.char_pattern = re.compile(
            r'(' + '|'.join(re.escape(k) for k in sorted(self.CHARACTER_MAPPINGS.keys(), key=len, reverse=True)) + r')',
            re.IGNORECASE
        )
    
    def normalize(self, text: str) -> str:
        """
        Normalize Roman Urdu text.
        
        Args:
            text: Input Roman Urdu text
            
        Returns:
            Normalized text
        """
        if not text:
            return text
        
        # Convert to lowercase for processing
        text = text.lower()
        
        # Apply character mappings
        text = self._apply_character_mappings(text)
        
        # Apply word-level normalization
        text = self._apply_word_mappings(text)
        
        return text
    
    def normalize_preserve(self, text: str) -> str:
        """
        Normalize while preserving original case where possible.
        
        Args:
            text: Input text
            
        Returns:
            Normalized text with original case preserved
        """
        if not text:
            return text
        
        words = text.split()
        normalized_words = []
        
        for word in words:
            # Preserve punctuation
            punctuation = ''
            while word and not word[-1].isalnum():
                punctuation = word[-1] + punctuation
                word = word[:-1]
            
            if word:
                # Check if original was capitalized
                was_capitalized = word[0].isupper()
                
                # Normalize
                normalized = self.normalize(word)
                
                # Restore capitalization
                if was_capitalized and normalized:
                    normalized = normalized.capitalize()
                
                normalized_words.append(normalized + punctuation)
            else:
                normalized_words.append(punctuation)
        
        return ' '.join(normalized_words)
    
    def _apply_character_mappings(self, text: str) -> str:
        """Apply character-level mappings."""
        return self.char_pattern.sub(
            lambda m: self.CHARACTER_MAPPINGS.get(m.group(0).lower(), m.group(0)),
            text
        )
    
    def _apply_word_mappings(self, text: str) -> str:
        """Apply word-level mappings."""
        words = re.findall(r'\b\w+\b|\W+', text)
        normalized_words = []
        
        for word in words:
            if re.match(r'\w+', word):
                # Check for exact match
                normalized = self.WORD_MAPPINGS.get(word.lower(), word)
                
                # If not translating, keep original word after character normalization
                if not self.use_translation and normalized != word:
                    # Only apply character mappings, not translation
                    normalized = self._apply_character_mappings(word)
                
                normalized_words.append(normalized)
            else:
                normalized_words.append(word)
        
        return ''.join(normalized_words)
    
    def get_suggestions(self, word: str, top_n: int = 3) -> List[str]:
        """
        Get normalization suggestions for a word.
        
        Args:
            word: Input word
            top_n: Number of suggestions to return
            
        Returns:
            List of suggested normalizations
        """
        word = word.lower()
        suggestions = []
        
        # Check direct mapping
        if word in self.WORD_MAPPINGS:
            suggestions.append(self.WORD_MAPPINGS[word])
        
        # Find similar words using fuzzy matching
        for original, normalized in self.WORD_MAPPINGS.items():
            similarity = SequenceMatcher(None, word, original).ratio()
            if similarity > 0.7:
                suggestions.append((normalized, similarity))
        
        # Sort by similarity and return top N
        if suggestions and isinstance(suggestions[0], tuple):
            suggestions.sort(key=lambda x: x[1], reverse=True)
            return [s[0] for s in suggestions[:top_n]]
        
        return suggestions[:top_n]


# Singleton instance
_normalizer = None


def get_normalizer(use_translation: bool = False) -> RomanUrduNormalizer:
    """Get or create the normalizer singleton."""
    global _normalizer
    if _normalizer is None or _normalizer.use_translation != use_translation:
        _normalizer = RomanUrduNormalizer(use_translation=use_translation)
    return _normalizer
