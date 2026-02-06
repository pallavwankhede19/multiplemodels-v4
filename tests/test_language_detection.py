"""
Perfect Language Detection Test Suite
======================================

Tests the language detector's ability to differentiate between
Hindi and Marathi correctly.
"""

from app.services.language_detector import AdvancedLanguageDetector as LanguageDetector, detect_language


def test_explicit_tags():
    """Test explicit language tag detection"""
    print("\n" + "="*60)
    print("TEST 1: Explicit Language Tags")
    print("="*60)
    
    test_cases = [
        ("[en] Hello, how are you?", "en"),
        ("[hi] नमस्ते, कैसे हो?", "hi"),
        ("[mr] नमस्कार, कसा आहेस?", "mr"),
        ("Some text [EN] with tag in middle", "en"),
    ]
    
    for text, expected in test_cases:
        result, confidence = LanguageDetector.detect_language(text)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} | Expected: {expected}, Got: {result} (conf: {confidence:.2f})")
        print(f"   Text: {text[:50]}")
    

def test_unique_characters():
    """Test Marathi-specific character detection"""
    print("\n" + "="*60)
    print("TEST 2: Marathi Unique Characters (ळ, ऱ)")
    print("="*60)
    
    test_cases = [
        ("मुंबईळा जाणार आहे", "mr"),  # Contains ळ
        ("पुण्याऱ्या लोकांना", "mr"),  # Contains ऱ
        ("माझं नाव काळे आहे", "mr"),  # Contains ळ
    ]
    
    for text, expected in test_cases:
        result, confidence = LanguageDetector.detect_language(text)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} | Expected: {expected}, Got: {result} (conf: {confidence:.2f})")
        print(f"   Text: {text}")


def test_vocabulary_matching():
    """Test vocabulary-based detection"""
    print("\n" + "="*60)
    print("TEST 3: Vocabulary-Based Detection")
    print("="*60)
    
    test_cases = [
        # Marathi examples
        ("नमस्कार, तू कसा आहेस?", "mr"),
        ("मला समजलं नाही", "mr"),
        ("तुझं नाव काय आहे?", "mr"),
        ("मी छान आहे, धन्यवाद", "mr"),
        ("आम्ही पुण्याला जातोय", "mr"),
        
        # Hindi examples
        ("नमस्ते, तुम कैसे हो?", "hi"),
        ("मुझे समझ नहीं आया", "hi"),
        ("तुम्हारा नाम क्या है?", "hi"),
        ("मैं अच्छा हूं, शुक्रिया", "hi"),
        ("हम दिल्ली जा रहे हैं", "hi"),
    ]
    
    for text, expected in test_cases:
        result, confidence = LanguageDetector.detect_language(text)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} | Expected: {expected}, Got: {result} (conf: {confidence:.2f})")
        print(f"   Text: {text}")


def test_mixed_scenarios():
    """Test edge cases and mixed scenarios"""
    print("\n" + "="*60)
    print("TEST 4: Edge Cases & Mixed Scenarios")
    print("="*60)
    
    test_cases = [
        ("Hello!", "en"),
        ("How are you doing?", "en"),
        ("", "en"),  # Empty string
        ("123456", "en"),  # Numbers only
        ("!@#$%", "en"),  # Symbols only
    ]
    
    for text, expected in test_cases:
        result, confidence = LanguageDetector.detect_language(text)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} | Expected: {expected}, Got: {result} (conf: {confidence:.2f})")
        print(f"   Text: '{text}'")


def test_context_detection():
    """Test context-aware detection"""
    print("\n" + "="*60)
    print("TEST 5: Context-Aware Detection")
    print("="*60)
    
    # Simulate conversation flow
    detector = LanguageDetector()
    
    # User asks in Marathi
    user_input = "नमस्कार, तुझं नाव काय?"
    user_lang, _ = detector.detect_language(user_input)
    print(f"User input detected as: {user_lang}")
    
    # AI responds (without tag, ambiguous)
    ai_response = "माझं नाव AI आहे"
    
    # Detect with context
    result, confidence = detector.detect_with_context(
        text=ai_response,
        user_input=user_input,
        previous_lang=None
    )
    
    status = "✅ PASS" if result == "mr" else "❌ FAIL"
    print(f"{status} | AI response detected as: {result} (conf: {confidence:.2f})")
    print(f"   Using user context: {user_input}")


def test_real_world_scenarios():
    """Test with actual problematic inputs from the logs"""
    print("\n" + "="*60)
    print("TEST 6: Real-World Scenarios from Logs")
    print("="*60)
    
    test_cases = [
        # The problematic case from your logs
        ("Mi Tula Hindi picture Hindi picture", "en"),  # Mixed English/transliterated
        ("मला समजले नाही", "mr"),  # Pure Marathi
        ("कृपया स्पष्टपणे सांगा", "mr"),  # Marathi (स्पष्टपणे is Marathi-specific)
        ("कृपया फिर से बोलें", "hi"),  # Hindi (फिर से is Hindi-specific)
    ]
    
    for text, expected in test_cases:
        result, confidence = LanguageDetector.detect_language(text)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        print(f"{status} | Expected: {expected}, Got: {result} (conf: {confidence:.2f})")
        print(f"   Text: {text}")


def run_all_tests():
    """Run all test suites"""
    print("\n" + "🧪 "*30)
    print("PERFECT LANGUAGE DETECTOR - COMPREHENSIVE TEST SUITE")
    print("🧪 "*30)
    
    test_explicit_tags()
    test_unique_characters()
    test_vocabulary_matching()
    test_mixed_scenarios()
    test_context_detection()
    test_real_world_scenarios()
    
    print("\n" + "="*60)
    print("✨ ALL TESTS COMPLETED")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()
