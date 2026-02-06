import re

# Simple Phonetic Map for Roman to Devanagari (Basic Conversational)
# This is a heuristic mapping for transliteration when libraries are unavailable.
PHONETIC_MAP = {
    'ai': 'ऐ', 'au': 'औ', 'ee': 'ई', 'oo': 'ऊ',
    'a': 'ा', 'e': 'े', 'i': 'ि', 'o': 'ो', 'u': 'ु',
    'k': 'क', 'kh': 'ख', 'g': 'ग', 'gh': 'घ',
    'ch': 'च', 'chh': 'छ', 'j': 'ज', 'jh': 'झ',
    't': 'त', 'th': 'थ', 'd': 'द', 'dh': 'ध',
    'n': 'न', 'p': 'प', 'ph': 'फ', 'f': 'फ', 'b': 'ब', 'bh': 'भ', 'm': 'म',
    'y': 'य', 'r': 'र', 'l': 'ल', 'v': 'व', 'w': 'व', 'sh': 'श', 's': 'स', 'h': 'ह',
    'z': 'झ', 'x': 'क्ष',
}

# Vowels at start of words
START_VOWELS = {
    'a': 'अ', 'e': 'ए', 'i': 'इ', 'o': 'ओ', 'u': 'उ',
    'aa': 'आ', 'ee': 'ई', 'oo': 'ऊ', 'ai': 'ऐ', 'au': 'औ'
}

# Common English terms and their phonetic Devanagari equivalents
ENGLISH_TO_DEVANAGARI = {
    'otp': 'ओटीपी', 'form': 'फॉर्म', 'fee': 'फीस', 'fees': 'फीस',
    'bank': 'बैंक', 'mobile': 'मोबाइल', 'number': 'नंबर',
    'payment': 'पेमेंट', 'online': 'ऑनलाइन', 'status': 'स्टेटस',
    'hello': 'हेलो', 'hi': 'हाय', 'ok': 'ओके', 'yes': 'यस', 'no': 'नो',
    'please': 'प्लीज', 'cancel': 'कैंसिल', 'submit': 'सबमिट',
    'namaste': 'नमस्ते', 'dhanyavad': 'धन्यवाद', 'swagat': 'स्वागत',
    'tuza': 'तुझा', 'tujha': 'तुझा', 'majha': 'माझा', 'mazha': 'माझा',
    'mazhi': 'माझी', 'tujhi': 'तुझी', 'nav': 'नाव', 'naav': 'नाव',
    'tabiyat': 'तब्येत', 'tabiyet': 'तब्येत', 'aahe': 'आहे', 'aahes': 'आहेस',
    'kashi': 'कशी', 'kasa': 'कसा', 'kase': 'कसे', 'tuzi': 'तुझी', 'tuji': 'तुझी',
}

# Marathi-specific input corrections (fixing common STT misrecognitions)
MARATHI_INPUT_CORRECTIONS = {
    'puja': 'tuza',
    'pujha': 'tujha',
    'aisi': 'kashi',  # kashi often sounds like kaisi/aisi to Hindi-biased STT
    'kaisi': 'kashi',
    'tujhe': 'tuzi',  # For phrases like 'tuzi tabiyat'
    'hai': 'aahe',    # If Marathi markers are present, hai is likely aahe
    'song': '',       # STT often adds 'song' at the end on noise
    'aaja re': 'aajari', # 'aajari' (sick) misrecognized
    'aajare': 'aajari',
}

def transliterate_roman_to_devanagari(text: str) -> str:
    """
    A heuristic Roman to Devanagari transliterator for conversational Hindi/Marathi.
    Handles basic phonetics and preserves common English terms.
    """
    words = text.split()
    converted_words = []
    
    for word in words:
        clean_word = re.sub(r'[^\w]', '', word).lower()
        
        # 1. Check if it's a known English term
        if clean_word in ENGLISH_TO_DEVANAGARI:
            converted_words.append(ENGLISH_TO_DEVANAGARI[clean_word])
            continue
            
        # 2. If it's pure numbers, keep as is
        if clean_word.isdigit():
            converted_words.append(word)
            continue
            
        # 3. If it's already Devanagari, keep as is
        if any('\u0900' <= c <= '\u097F' for c in word):
            converted_words.append(word)
            continue
            
        # 4. Phonetic approximation
        # (This is a simplified version of ITRANS/HK mapping)
        res = ""
        i = 0
        w = word.lower()
        while i < len(w):
            char_found = False
            # Try 2 chars
            if i + 1 < len(w):
                pair = w[i:i+2]
                if i == 0 and pair in START_VOWELS:
                    res += START_VOWELS[pair]
                    i += 2
                    continue
                if pair in PHONETIC_MAP:
                    res += PHONETIC_MAP[pair]
                    i += 2
                    continue
            
            # Try 1 char
            single = w[i]
            if i == 0 and single in START_VOWELS:
                res += START_VOWELS[single]
                i += 1
                continue
            
            if single in PHONETIC_MAP:
                res += PHONETIC_MAP[single]
                i += 1
                continue
            
            res += single
            i += 1
            
        converted_words.append(res)
        
    return " ".join(converted_words)

class ScriptNormalizer:
    @staticmethod
    def normalize_input(text: str, locked_lang: str) -> str:
        """
        STAGE 3: SCRIPT NORMALIZATION (PRE-LLM)
        """
        if locked_lang == 'en':
            # Ensure English is Latin only (strip Devanagari if any leaked in)
            return re.sub(r'[\u0900-\u097F]', '', text).strip()
            
        if locked_lang == 'mr':
            # Heuristic correction for common Marathi misrecognitions in STT
            for wrong, right in MARATHI_INPUT_CORRECTIONS.items():
                # Use regex for word boundary to avoid partial matches
                text = re.sub(rf'\b{wrong}\b', right, text, flags=re.IGNORECASE)

        if locked_lang in ['hi', 'mr']:
            # If text is Roman, transliterate to Devanagari
            has_latin = any('a' <= c.lower() <= 'z' for c in text)
            if has_latin:
                return transliterate_roman_to_devanagari(text)
                
        return text

    @staticmethod
    def validate_output(text: str, locked_lang: str) -> str:
        """
        STAGE 6: OUTPUT SCRIPT VALIDATION (PRE-TTS)
        Enhanced for clear pronunciation in all languages
        """
        if not text.strip():
            return ""
        
        # Remove emojis from all languages (backup filter)
        # Comprehensive emoji Unicode ranges
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags
            u"\U00002702-\U000027B0"  # dingbats
            u"\U000024C2-\U0001F251"  # enclosed characters
            u"\U0001F900-\U0001F9FF"  # supplemental symbols
            u"\U0001FA00-\U0001FA6F"  # chess symbols
            u"\U00002600-\U000026FF"  # misc symbols
            "]+", flags=re.UNICODE
        )
        text = emoji_pattern.sub('', text)
            
        if locked_lang == 'en':
            # 1. Phonetic replacements for common Indian words in English TTS
            replacements = {
                r'\bnamaste\b': 'Nah-mas-tay',
                r'\bdhanyavad\b': 'Dhahn-yah-vahd',
                r'\baadhar\b': 'Ah-dhar',
                r'\bnamaskar\b': 'Nah-mas-kar',
                r'\brupees\b': 'rupees',
                r'\brupee\b': 'rupee',
                # Common tech terms for clarity
                r'\bapi\b': 'A P I',
                r'\bui\b': 'U I',
                r'\burl\b': 'U R L',
                r'\bai\b': 'artificial intelligence',
                r'\bml\b': 'machine learning',
            }
            
            processed_text = text
            for pattern, sub in replacements.items():
                processed_text = re.sub(pattern, sub, processed_text, flags=re.IGNORECASE)
            
            # 2. Fix spacing around punctuation for natural pauses
            processed_text = re.sub(r'\s*([.,!?])\s*', r'\1 ', processed_text)
            
            # 3. Remove emojis and special characters that confuse TTS
            processed_text = re.sub(r'[^\x00-\x7F\s.,!?]', '', processed_text)
            
            # 4. Normalize whitespace
            processed_text = re.sub(r'\s+', ' ', processed_text).strip()
            
            return processed_text
            
        if locked_lang in ['hi', 'mr']:
            # 1. Handle English Loanwords Phonetically
            words = text.split()
            processed_words = []
            for w in words:
                clean_w = re.sub(r'[^\w]', '', w).lower()
                if clean_w in ENGLISH_TO_DEVANAGARI:
                    processed_words.append(ENGLISH_TO_DEVANAGARI[clean_w])
                else:
                    processed_words.append(w)
            text = " ".join(processed_words)

            # 2. Transliterate any remaining Latin 
            has_latin = any('a' <= c.lower() <= 'z' for c in text)
            if has_latin:
                text = transliterate_roman_to_devanagari(text)
            
            # 3. Numeric Normalization
            if any(c.isdigit() for c in text):
                digit_map = {
                    '0': 'शून्य', '1': 'एक', '2': 'दो', '3': 'तीन', '4': 'चार',
                    '5': 'पांच', '6': 'छह', '7': 'सात', '8': 'आठ', '9': 'नौ'
                }
                for digit, word in digit_map.items():
                    text = text.replace(digit, word)
            
            # 4. Punctuation & Cleaning
            text = text.replace('.', '।')
            text = re.sub(r'[^\u0900-\u097F\s.,!?।]', '', text)
            return re.sub(r'\s+', ' ', text).strip()
            
        return text
