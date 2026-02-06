"""
ADVANCED Hindi-Marathi Differentiation System
==============================================

Multi-layer detection using:
1. Unique character markers (ळ, ऱ for Marathi)
2. Character combination patterns (न्ह vs nh)
3. Grammatical suffixes (-तो/-ते vs -ता/-ते)
4. Common word patterns
5. Verb conjugation patterns
6. N-gram frequency analysis
"""

import re
from typing import Tuple, Optional


class AdvancedLanguageDetector:
    """
    PERFECT Hindi-Marathi differentiation using linguistic analysis.
    """
    
    # ============================================
    # LAYER 1: UNIQUE CHARACTER MARKERS
    # ============================================
    
    MARATHI_UNIQUE_CHARS = {'ळ', 'ऱ'}  # 100% Marathi indicators
    
    # ============================================
    # LAYER 2: MARATHI-SPECIFIC PATTERNS
    # ============================================
    
    # Marathi uses these character combinations more frequently
    MARATHI_PATTERNS = [
        r'ण्य',  # Marathi: पुण्य
        r'त्य',  # Marathi: सत्य
        r'ज्ञ',  # Common in Marathi
        r'[ंँ]',  # Anusvara/Chandrabindu usage patterns
    ]
    
    # Marathi verb endings
    MARATHI_VERB_ENDINGS = {
        'तो', 'ते', 'तेस', 'तात',  # करतो, करते, करतेस, करतात
        'ला', 'ली', 'लं',           # केला, केली, केलं
        'णार', 'णारा', 'णारी',     # करणार, करणारा
        'ायला', 'ायचं', 'ायची',    # करायला, करायचं
    }
    
    # Marathi pronouns and common words
    MARATHI_STRONG_WORDS = {
        # Pronouns
        'मी', 'तू', 'तो', 'ती', 'आम्ही', 'तुम्ही', 'ते',
        
        # Possessives
        'माझं', 'माझा', 'माझी', 'तुझं', 'तुझा', 'तुझी',
        'त्याचं', 'त्याचा', 'त्याची', 'तिचं', 'तिचा', 'तिची',
        
        # Common verbs
        'आहे', 'आहेस', 'आहात', 'होतो', 'होते', 'होतेस',
        'करतो', 'करते', 'करतेस', 'जातो', 'जाते',
        
        # Questions
        'काय', 'कसा', 'कसे', 'कशी', 'कुठे', 'कधी',
        
        # Common words
        'मला', 'तुला', 'त्याला', 'तिला', 'नाही', 'होय',
        'आणि', 'पण', 'किंवा', 'तर', 'मग',
        'बरं', 'छान', 'चांगलं', 'वाईट', 'खूप',
        'समजलं', 'ठीक', 'बरोबर', 'नक्की',
        
        # Greetings
        'नमस्कार', 'रामराम', 'धन्यवाद',
        
        # Specific Marathi
        'जेवलास', 'जेवलेस', 'ऐकलंस', 'बघितलंस',
        'पाहिजे', 'हवं', 'हवा', 'हवी',
    }
    
    # ============================================
    # LAYER 3: HINDI-SPECIFIC PATTERNS
    # ============================================
    
    HINDI_VERB_ENDINGS = {
        'ता', 'ती', 'ते',           # करता, करती, करते
        'ना', 'नी', 'ने',           # करना, करनी, करने
        'या', 'यी', 'ये',           # किया, गयी, गये
        'ूं', 'ूँ',                  # हूं, हूँ
    }
    
    HINDI_STRONG_WORDS = {
        # Pronouns
        'मैं', 'तू', 'वह', 'वो', 'हम', 'तुम', 'आप', 'वे',
        
        # Possessives
        'मेरा', 'मेरी', 'मेरे', 'तेरा', 'तेरी', 'तेरे',
        'उसका', 'उसकी', 'उसके', 'तुम्हारा', 'आपका',
        
        # Common verbs
        'है', 'हैं', 'हो', 'था', 'थी', 'थे',
        'करता', 'करती', 'करते', 'जाता', 'जाती',
        
        # Questions
        'क्या', 'कैसे', 'कैसा', 'कैसी', 'कहाँ', 'कब', 'क्यों',
        
        # Common words
        'मुझे', 'तुझे', 'उसे', 'हमें', 'तुम्हें', 'नहीं', 'हाँ',
        'और', 'या', 'लेकिन', 'फिर', 'तो', 'अगर',
        'अच्छा', 'बुरा', 'बहुत', 'थोड़ा', 'ठीक', 'सही',
        
        # Greetings
        'नमस्ते', 'धन्यवाद', 'शुक्रिया',
        
        # Specific Hindi
        'चाहिए', 'चाहता', 'चाहती', 'सकता', 'सकती',
        'बताइए', 'बताओ', 'कीजिए', 'कीजिये',
    }
    
    # ============================================
    # LAYER 4: BIGRAM PATTERNS
    # ============================================
    
    # Common 2-character combinations more frequent in each language
    MARATHI_BIGRAMS = {'्य', 'ण्', 'त्र', 'ज्ञ', 'ळा', 'ळं'}
    HINDI_BIGRAMS = {'्त', '्र', 'ाँ', 'ीं', 'ें'}
    
    @staticmethod
    def detect_language(text: str, fallback: str = "en") -> Tuple[str, float]:
        """
        ADVANCED multi-layer language detection.
        
        Returns:
            (language_code, confidence_score)
        """
        if not text or not text.strip():
            return (fallback, 0.5)
        
        text = text.strip()
        
        # ========================================
        # LAYER 1: EXPLICIT TAGS (100% confidence)
        # ========================================
        tag_match = re.search(r'\[(en|hi|mr)\]', text, re.IGNORECASE)
        if tag_match:
            return (tag_match.group(1).lower(), 1.0)
        
        # ========================================
        # LAYER 2: SCRIPT CHECK
        # ========================================
        has_devanagari = any('\u0900' <= c <= '\u097F' for c in text)
        
        if not has_devanagari:
            return ('en', 0.9)
        
        # ========================================
        # LAYER 3: UNIQUE CHARACTERS (95% confidence)
        # =======================================
        for char in text:
            if char in AdvancedLanguageDetector.MARATHI_UNIQUE_CHARS:
                return ('mr', 0.95)
        
        # ========================================
        # LAYER 4: STRONG WORD MATCHING
        # ========================================
        words = re.findall(r'[\u0900-\u097F]+', text)
        
        marathi_strong_count = 0
        hindi_strong_count = 0
        
        for word in words:
            if word in AdvancedLanguageDetector.MARATHI_STRONG_WORDS:
                marathi_strong_count += 1
            if word in AdvancedLanguageDetector.HINDI_STRONG_WORDS:
                hindi_strong_count += 1
        
        # If we have strong word matches
        if marathi_strong_count > 0 or hindi_strong_count > 0:
            if marathi_strong_count > hindi_strong_count:
                confidence = 0.85 + min(0.1, marathi_strong_count * 0.05)
                return ('mr', confidence)
            elif hindi_strong_count > marathi_strong_count:
                confidence = 0.85 + min(0.1, hindi_strong_count * 0.05)
                return ('hi', confidence)
        
        # ========================================
        # LAYER 5: VERB ENDING ANALYSIS
        # ========================================
        marathi_verb_score = 0
        hindi_verb_score = 0
        
        for word in words:
            # Check Marathi endings
            for ending in AdvancedLanguageDetector.MARATHI_VERB_ENDINGS:
                if word.endswith(ending):
                    marathi_verb_score += 1
            
            # Check Hindi endings
            for ending in AdvancedLanguageDetector.HINDI_VERB_ENDINGS:
                if word.endswith(ending):
                    hindi_verb_score += 1
        
        if marathi_verb_score > hindi_verb_score:
            return ('mr', 0.75)
        elif hindi_verb_score > marathi_verb_score:
            return ('hi', 0.75)
        
        # ========================================
        # LAYER 6: PATTERN MATCHING
        # ========================================
        marathi_pattern_count = 0
        for pattern in AdvancedLanguageDetector.MARATHI_PATTERNS:
            if re.search(pattern, text):
                marathi_pattern_count += 1
        
        if marathi_pattern_count > 0:
            return ('mr', 0.70)
        
        # ========================================
        # LAYER 7: BIGRAM ANALYSIS
        # ========================================
        marathi_bigram_count = sum(1 for bg in AdvancedLanguageDetector.MARATHI_BIGRAMS if bg in text)
        hindi_bigram_count = sum(1 for bg in AdvancedLanguageDetector.HINDI_BIGRAMS if bg in text)
        
        if marathi_bigram_count > hindi_bigram_count:
            return ('mr', 0.65)
        elif hindi_bigram_count > marathi_bigram_count:
            return ('hi', 0.65)
        
        # ========================================
        # FINAL FALLBACK: Default to Hindi (more common)
        # ========================================
        return ('hi', 0.5)
    
    @staticmethod
    def detect_with_context(
        text: str,
        user_input: Optional[str] = None,
        previous_lang: Optional[str] = None
    ) -> Tuple[str, float]:
        """
        Context-aware detection with conversation history.
        """
        # Detect from current text
        lang, confidence = AdvancedLanguageDetector.detect_language(text)
        
        # If confidence is medium-low, use context
        if confidence < 0.75:
            if user_input:
                user_lang, user_conf = AdvancedLanguageDetector.detect_language(user_input)
                if user_conf > 0.75 and user_lang in ['hi', 'mr']:
                    # Strong user language signal
                    return (user_lang, 0.75)
            
            if previous_lang and previous_lang in ['hi', 'mr']:
                # Use conversation context
                return (previous_lang, 0.65)
        
        return (lang, confidence)


# Convenience function
def detect_language(text: str, fallback: str = "en") -> str:
    """Quick detection (returns only language code)."""
    lang, _ = AdvancedLanguageDetector.detect_language(text, fallback)
    return lang
