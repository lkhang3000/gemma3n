#!/usr/bin/env python3
"""
Quick test for emergency detection
"""

import sys
import os

# Add back_end to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'back_end'))

# Test emergency detection directly
from prompt import CRITICAL_SYMPTOMS

def test_emergency_detection():
    test_text = "chest pain"
    text_lower = test_text.lower()
    
    print(f"Testing text: '{test_text}'")
    print(f"Lowercased: '{text_lower}'")
    print(f"Critical symptoms: {CRITICAL_SYMPTOMS}")
    
    for symptom in CRITICAL_SYMPTOMS:
        if symptom in text_lower:
            print(f"✅ MATCH FOUND: '{symptom}' in '{text_lower}'")
            return True, symptom
    
    print("❌ No match found")
    return False, None

if __name__ == "__main__":
    result = test_emergency_detection()
    print(f"Result: {result}")
