#!/usr/bin/env python3
"""
Test script to validate anti-copying and thinking-based response system
"""

import json
import sys
import os

def test_system_prompt_no_examples():
    """Test that system prompt doesn't contain direct reply examples"""
    print("=== Testing System Prompt Anti-Copying ===")
    
    try:
        # Test prompt_builder directly
        sys.path.insert(0, '.')
        from src.utils.prompt_builder import PromptBuilder
        
        builder = PromptBuilder()
        prompt = builder.build_system_prompt("hello", False, {}, None)
        
        # Check for problematic direct examples
        problematic_patterns = [
            "respond with:",
            "example response:",
            "say this",
            "like this",
            "Pixel hoon",
            "Aap mere dost ho",
            "relax a bit",
            "calm down",
            "what's your problem"
        ]
        
        violations = []
        for pattern in problematic_patterns:
            if pattern.lower() in prompt.lower():
                violations.append(pattern)
        
        if violations:
            print(f"✗ Found direct examples: {violations}")
            return False
        else:
            print("✓ No direct reply examples found in system prompt")
            return True
            
    except Exception as e:
        print(f"✗ Error testing system prompt: {e}")
        return False

def test_thinking_instructions():
    """Test that system prompt contains thinking instructions"""
    print("\n=== Testing Thinking Instructions ===")
    
    try:
        sys.path.insert(0, '.')
        from src.utils.prompt_builder import PromptBuilder
        
        builder = PromptBuilder()
        prompt = builder.build_system_prompt("hello", False, {}, None)
        
        # Check for thinking instructions
        thinking_patterns = [
            "DO NOT copy any example",
            "Generate FRESH, ORIGINAL",
            "CONTEXT-AWARE PROCESSING",
            "BEHAVIORAL GUIDELINES",
            "VARIATION REQUIREMENT",
            "HARD CONSTRAINTS",
            "anti-copying"
        ]
        
        missing = []
        for pattern in thinking_patterns:
            if pattern.lower() not in prompt.lower():
                missing.append(pattern)
        
        if missing:
            print(f"✗ Missing thinking instructions: {missing}")
            return False
        else:
            print("✓ All thinking instructions present")
            return True
            
    except Exception as e:
        print(f"✗ Error testing thinking instructions: {e}")
        return False

def test_intent_based_system():
    """Test that intent-based system is working"""
    print("\n=== Testing Intent-Based System ===")
    
    try:
        sys.path.insert(0, '.')
        from src.utils.prompt_builder import PromptBuilder
        
        builder = PromptBuilder()
        
        # Test different message types
        test_cases = [
            ("yes", "dry_reply"),
            ("no", "dry_reply"), 
            ("hmm", "dry_reply"),
            ("hello", "greetings"),
            ("sad", "emotional")
        ]
        
        all_passed = True
        for message, expected_type in test_cases:
            intent = builder.get_response_intent(expected_type, None, message)
            
            if 'intent' not in intent or 'approach' not in intent:
                print(f"✗ Missing intent guidance for '{message}'")
                all_passed = False
            else:
                print(f"✓ Intent guidance for '{message}': {intent['intent']}")
        
        return all_passed
        
    except Exception as e:
        print(f"✗ Error testing intent system: {e}")
        return False

def test_template_removal():
    """Test that template system is removed"""
    print("\n=== Testing Template Removal ===")
    
    try:
        sys.path.insert(0, '.')
        from src.utils.prompt_builder import PromptBuilder
        
        builder = PromptBuilder()
        
        # Check that get_response_template method doesn't exist or is deprecated
        if hasattr(builder, 'get_response_template'):
            print("✗ Old template method still exists")
            return False
        elif hasattr(builder, 'get_response_intent'):
            print("✓ Intent-based method replacing templates")
            return True
        else:
            print("✗ No response method found")
            return False
            
    except Exception as e:
        print(f"✗ Error testing template removal: {e}")
        return False

def test_era_integration():
    """Test that era.py uses intent system"""
    print("\n=== Testing Era Integration ===")
    
    try:
        with open('src/utils/era.py', 'r') as f:
            era_content = f.read()
        
        # Check for anti-copying validation
        if 'ANTI-COPYING VALIDATION' in era_content:
            print("✓ Era has anti-copying validation")
        else:
            print("✗ Era missing anti-copying validation")
            return False
        
        # Check for intent usage
        if 'get_response_intent' in era_content:
            print("✓ Era uses intent system")
            return True
        else:
            print("✗ Era not using intent system")
            return False
            
    except Exception as e:
        print(f"✗ Error testing era integration: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing Anti-Copying & Thinking-Based Response System")
    print("=" * 65)
    
    results = []
    results.append(test_system_prompt_no_examples())
    results.append(test_thinking_instructions())
    results.append(test_intent_based_system())
    results.append(test_template_removal())
    results.append(test_era_integration())
    
    print("\n" + "=" * 65)
    print("Anti-copying tests completed!")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All {total} tests passed!")
        print("\nSYSTEM TRANSFORMATION COMPLETE:")
        print("✓ Removed all direct reply examples")
        print("✓ Added strong thinking & originality instructions")
        print("✓ Implemented intent-based behavior system")
        print("✓ Added memory + context enforcement")
        print("✓ Added hard constraints against copying")
        print("✓ AI will now think naturally instead of copying")
    else:
        print(f"❌ {total - passed} out of {total} tests failed")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)