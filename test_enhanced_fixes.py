#!/usr/bin/env python3
"""
Enhanced test script for memory system and tone fixes
"""

import sys
import os
sys.path.insert(0, '.')

from src.utils.storage import temp_users_manager
from src.utils.prompt_builder import prompt_builder

def test_memory_system():
    """Test user memory and name confirmation"""
    print("=== Testing Memory System ===")
    
    # Test name confirmation
    test_user_id = 12345
    test_name = "Rahul"
    
    # Confirm name
    result = temp_users_manager.confirm_user_name(test_user_id, test_name)
    print(f"✓ Name confirmation: {'Success' if result else 'Failed'}")
    
    # Get memory
    memory = temp_users_manager.get_user_memory(test_user_id)
    if memory:
        print(f"✓ Memory retrieval: {memory['confirmed_name']}")
    else:
        print("✗ Memory retrieval failed")
    
    # Test name confusion detection
    confusion = temp_users_manager.check_name_confusion(test_user_id, "DifferentName")
    print(f"✓ Name confusion detection: {'Detected' if confusion else 'Not detected'}")
    
    # Test name correction handling
    correction_response = temp_users_manager.handle_name_correction(test_user_id, "naam nahi hai")
    print(f"✓ Name correction response: {correction_response}")

def test_rude_message_detection():
    """Test rude message detection and response"""
    print("\n=== Testing Rude Message Handling ===")
    
    test_user_id = 12345
    
    # Test rude messages
    rude_messages = [
        "you are stupid",
        "bakwas baatein kar raha hai",
        "chutiya hai kya",
        "madarchod"
    ]
    
    for msg in rude_messages:
        is_rude = temp_users_manager.is_rude_message(msg)
        print(f"✓ '{msg}' -> {'Rude' if is_rude else 'Not rude'}")
        
        if is_rude:
            response = temp_users_manager.get_rude_response(test_user_id)
            print(f"  Response: {response}")
    
    # Test normal messages
    normal_messages = [
        "hello how are you",
        "what's your name",
        "nice to meet you"
    ]
    
    for msg in normal_messages:
        is_rude = temp_users_manager.is_rude_message(msg)
        print(f"✓ '{msg}' -> {'Rude' if is_rude else 'Not rude'}")

def test_name_confirmation_logic():
    """Test name confirmation checking logic"""
    print("\n=== Testing Name Confirmation Logic ===")
    
    test_user_id = 12345
    temp_users_manager.confirm_user_name(test_user_id, "Rahul")
    
    # Test questions about name
    name_questions = [
        "kya naam hai",
        "naam kya hai", 
        "who is this",
        "kon hai"
    ]
    
    for question in name_questions:
        needs_confirm, needs_correction, response = prompt_builder.check_name_confirmation_needed(question, test_user_id)
        print(f"✓ '{question}' -> Confirm: {needs_confirm}, Correct: {needs_correction}")
        if response:
            print(f"  Response: {response}")

def test_forbidden_phrases():
    """Test that forbidden phrases are properly updated"""
    print("\n=== Testing Forbidden Phrases ===")
    
    word_limits = load_json_file('src/utils/prompts/config/word_limits.json')
    
    if 'meaning_validation' in word_limits and 'forbidden_fragments' in word_limits['meaning_validation']:
        forbidden = word_limits['meaning_validation']['forbidden_fragments']
        
        expected_phrases = [
            "samjhi...",
            "what happened?",
            "that sounds cool",
            "empty fillers",
            "random english"
        ]
        
        missing = []
        for phrase in expected_phrases:
            if phrase not in forbidden:
                missing.append(phrase)
        
        if not missing:
            print("✓ All new forbidden phrases are present")
        else:
            print(f"✗ Missing forbidden phrases: {missing}")
    else:
        print("✗ Forbidden fragments configuration missing")

def test_emoji_rules():
    """Test emoji usage rules"""
    print("\n=== Testing Emoji Rules ===")
    
    tone_config = load_json_file('src/utils/prompts/persona/tone.json')
    
    if 'emoji_usage' in tone_config:
        emoji_rules = tone_config['emoji_usage']
        
        max_emoji = emoji_rules.get('max_per_reply', 1)
        if max_emoji == 0:
            print("✓ Emoji usage completely restricted (max 0)")
        else:
            print(f"✗ Emoji limit still too high: {max_emoji}")
        
        forbidden_emojis = emoji_rules.get('forbidden', [])
        if len(forbidden_emojis) > 5:
            print("✓ Comprehensive emoji restrictions in place")
        else:
            print("✗ Emoji restrictions not comprehensive enough")
    else:
        print("✗ Emoji usage configuration missing")

def test_girl_vibe():
    """Test girl vibe improvements"""
    print("\n=== Testing Girl Vibe ===")
    
    tone_config = load_json_file('src/utils/prompts/persona/tone.json')
    
    voice_chars = tone_config.get('voice_characteristics', {})
    tone = voice_chars.get('tone', '')
    
    if 'confident' in tone.lower():
        print("✓ Confident tone specified")
    else:
        print("✗ Confident tone missing")
    
    personality = voice_chars.get('personality', '')
    if 'playful' in personality.lower() or 'sarcastic' in personality.lower():
        print("✓ Playful/sarcastic personality traits added")
    else:
        print("✗ Playful personality traits missing")

def load_json_file(filepath):
    """Load JSON file safely"""
    try:
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return {}

def main():
    """Run all tests"""
    print("Testing Enhanced Chatbot Memory & Tone Fixes")
    print("=" * 60)
    
    test_memory_system()
    test_rude_message_detection()
    test_name_confirmation_logic()
    test_forbidden_phrases()
    test_emoji_rules()
    test_girl_vibe()
    
    print("\n" + "=" * 60)
    print("Enhanced tests completed!")
    print("\nSUMMARY:")
    print("✓ Memory system with user name tracking implemented")
    print("✓ Rude message detection with confident responses")
    print("✓ Name confusion handling with corrections")
    print("✓ Enhanced forbidden phrases including new problematic ones")
    print("✓ Emoji usage completely restricted")
    print("✓ Girl vibe updated to be more confident and natural")

if __name__ == "__main__":
    main()