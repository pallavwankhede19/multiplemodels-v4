import re

"""
Transliteration Detection for Hinglish/Manglish
"""

# Common Hindi transliteration patterns
HINDI_TRANSLITERATION_WORDS = {
    'namaste', 'kaise', 'kaisa', 'kaisi', 'hai', 'ho', 'hain',
    'hu', 'hoon', 'main', 'mein', 'hum', 'woh', 'wo', 've',
    'kya', 'kahan', 'kab', 'kaun', 'kyun', 'mujhe', 'tujhe', 
    'humara', 'hamara', 'mera', 'tera', 'liye', 'sath', 'acha', 'theek',
    'chahiye', 'karta', 'raha', 'rahi', 'rahe', 'tha', 'thi', 'the',
    'samajh', 'baat', 'bol', 'kal', 'aaj', 'parson', 'kyu', 'kyoon'
}

# Common Marathi transliteration patterns
# High-weight words that are almost exclusively Marathi
MARATHI_UNIQUE_WORDS = {
    'aahe', 'aahes', 'aahat', 'aahet', 'kasa', 'kashi', 'kase', 
    'kay', 'kuthe', 'kadhi', 'kontyhi', 'kashala', 'mala', 'tula', 
    'tyala', 'tila', 'majha', 'tujha', 'mazha', 'tuza', 'majhi', 'tujhi', 
    'mazhi', 'tuzi', 'ani', 'pan', 'mag', 'tar', 'khup', 'motha', 
    'lay', 'pahije', 'hawa', 'havi', 'havay', 'zalay', 'zala', 'bhau',
    'dada', 'tai', 'aaho', 'jevlas', 'aiklas', 'baghitlas', 'kelay', 'kela',
    'madhe', 'madhye', 'cha', 'chi', 'che', 'la', 'ne', 'shi', 'kon',
    'adhi', 'nantar', 'bara', 'bari', 'amhala', 'tumhala', 'aamhi', 'tumhi',
    'tabiyat', 'aajari', 'tabiyet', 'mi', 'mee', 'nav', 'naav', 'mahit',
    'shakal', 'shakto', 'shakte', 'bhun', 'mhanje', 'mhanun', 'pan', 'pun'
}

# Add 'aaja re' as a bigram marker for Marathi
MARATHI_BIGRAMS = {
    'aaja re', 'kaisi hai', 'aisi hai', 'basi hai', 'kashi aahe', 'kasa aahes',
    'kasa aahe', 'tujhe tabiyat', 'tuzi tabiyat', 'tuza tabiyat'
}

# Words that appear in both but are common in Marathi context
MARATHI_TRANSLITERATION_WORDS = MARATHI_UNIQUE_WORDS | {
    'namaskar', 'tu', 'to', 'ti', 'te', 'ji', 'ho', 'nahi', 'dhanyavad',
    'sang', 'sanga', 'bol', 'bola', 'de', 'dya', 'kar', 'kara', 'baki'
}

# English-only words
ENGLISH_ONLY_WORDS = {
    'hello', 'hi', 'hey', 'bye', 'goodbye', 'thanks', 'thank', 'you',
    'yes', 'no', 'ok', 'okay', 'please', 'sorry', 'welcome',
    'good', 'morning', 'evening', 'night', 'afternoon',
    'how', 'what', 'when', 'where', 'why', 'who',
    'the', 'is', 'are', 'am', 'was', 'were', 'be', 'been',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'can', 'could', 'should', 'may', 'might', 'must',
}

# Devanagari Script Support
HINDI_DEVANAGARI_WORDS = {
    'है', 'हैं', 'था', 'थी', 'थे', 'हुआ', 'हुए', 'हुई', 'कहा', 'कह', 'कर', 'दिया',
    'अपना', 'अपनी', 'अपने', 'मुझे', 'तुलसी', 'क्या', 'कहाँ', 'कब', 'कौन', 'क्यूँ',
    'कैसे', 'बारे', 'बात', 'बोल', 'सुन', 'रहा', 'रही', 'रहे', 'गया', 'गई', 'गए'
}

MARATHI_DEVANAGARI_WORDS = {
    'आहे', 'आहेत', 'होता', 'होती', 'होते', 'झाला', 'झाली', 'झाले', 'म्हटलं', 'सांगितलं',
    'माझा', 'माझी', 'माझे', 'तुझा', 'तुझी', 'तुझे', 'मला', 'तुला', 'त्याला', 'तिला',
    'काय', 'कुठे', 'कधी', 'कसं', 'कशी', 'असं', 'तसं', 'आणि', 'पण', 'तर', 'खूप', 'लय'
}

def detect_transliteration(text: str) -> str:
    """
    Enhanced Transliteration & Script Detection (Supports Devanagari).
    """
    text_lower = text.lower()
    
    # Check for Devanagari script presence
    has_devanagari = any('\u0900' <= c <= '\u097F' for c in text)
    
    # Replace punctuation with spaces
    text_clean = re.sub(r'[^\w\s]', ' ', text_lower)
    words = text_clean.split()
    
    if not words:
        return 'en'
    
    english_count = sum(1 for w in words if w in ENGLISH_ONLY_WORDS)
    if english_count > len(words) / 2: return 'en'
    
    hindi_score = 0
    marathi_score = 0
    
    # 1. Scoring based on Devanagari words if script is present
    if has_devanagari:
        for word in words:
            if word in HINDI_DEVANAGARI_WORDS: hindi_score += 2
            if word in MARATHI_DEVANAGARI_WORDS: marathi_score += 2
        
        # Marathi-only character 'ळ' check
        if '\u0933' in text: marathi_score += 5
    
    # 2. Scoring based on Roman transliteration
    for word in words:
        if word in ENGLISH_ONLY_WORDS: continue
            
        if word in MARATHI_UNIQUE_WORDS: marathi_score += 3
        elif word in MARATHI_TRANSLITERATION_WORDS: marathi_score += 1
            
        if word in HINDI_TRANSLITERATION_WORDS: hindi_score += 1

    # 3. Specific Bigram markers
    for bg in MARATHI_BIGRAMS:
        if bg in text_clean:
            marathi_score += 4

    print(f"📊 VAD DETECT: HI={hindi_score}, MR={marathi_score} | Script: {'DEV' if has_devanagari else 'ROMAN'}")
    
    if marathi_score == 0 and hindi_score == 0:
        return 'en'
    
    # Return based on highest score, tilt towards Hindi on draw
    if marathi_score > hindi_score:
        return 'mr'
    else:
        return 'hi'
