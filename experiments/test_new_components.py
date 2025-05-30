#!/usr/bin/env python
"""Test script to verify new components work correctly."""

import sys
import os

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_formatters():
    print("Testing formatters...")
    from experiments.formatters import PromptFormatter
    
    formatter = PromptFormatter()
    test_data = {
        'question': 'What is 2+2?',
        'choices': ['3', '4', '5', '6'],
        'answer_label': 'B'
    }
    
    result = formatter.format_prompt(
        test_data, ['A', 'B', 'C', 'D'], 'en', 'base', 'base'
    )
    
    if result and 'What is 2+2?' in result and 'A) 3' in result:
        print("✓ Formatters working correctly")
        return True
    else:
        print("✗ Formatters test failed")
        return False

def test_parsers():
    print("\nTesting parsers...")
    from experiments.parsers import ResponseParser
    
    parser = ResponseParser()
    
    # Test base format
    response1 = "Let me think...\nAnswer: B"
    result1 = parser.parse(response1, 'base')
    
    # Test JSON format
    response2 = '```json\n{"answer": "C"}\n```'
    result2 = parser.parse(response2, 'json')
    
    # Test XML format
    response3 = '<answer>D</answer>'
    result3 = parser.parse(response3, 'xml')
    
    if result1 == 'B' and result2 == 'C' and result3 == 'D':
        print("✓ Parsers working correctly")
        return True
    else:
        print("✗ Parsers test failed")
        print(f"  Base: {result1}, JSON: {result2}, XML: {result3}")
        return False

def test_permutations():
    print("\nTesting permutations...")
    from experiments.permutations import PermutationGenerator
    
    gen = PermutationGenerator()
    
    # Test circular
    circular = gen.generate('circular')
    
    # Test factorial
    factorial = gen.generate('factorial', num_factorial=4)
    
    if len(circular) == 4 and len(factorial) == 4:
        print("✓ Permutations working correctly")
        print(f"  Circular example: {circular[0]}")
        return True
    else:
        print("✗ Permutations test failed")
        return False

def test_api_clients():
    print("\nTesting API client structure...")
    from experiments.api_clients import APIClientFactory
    
    # Just test that classes exist and can be imported
    try:
        # Don't actually create clients (requires API keys)
        print("✓ API clients structure is correct")
        return True
    except Exception as e:
        print(f"✗ API clients test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing new components...\n")
    
    all_passed = True
    all_passed &= test_formatters()
    all_passed &= test_parsers()
    all_passed &= test_permutations()
    all_passed &= test_api_clients()
    
    if all_passed:
        print("\n✅ All component tests passed!")
    else:
        print("\n❌ Some tests failed. Please check the output above.")