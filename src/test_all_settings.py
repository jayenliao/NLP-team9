#!/usr/bin/env python3
"""Test all experiment settings with one question to catch issues"""

import json
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent))

from single_question import run_single_experiment
import os
from dotenv import load_dotenv

def test_all_settings():
    """Test one question across all settings"""
    
    # Load API keys
    load_dotenv()
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
    
    # Test configuration
    test_configs = {
        'models': [
            ('gemini-2.0-flash', GOOGLE_API_KEY),
            ('mistral-small-latest', MISTRAL_API_KEY)
        ],
        'languages': ['en', 'fr'],
        'formats': [
            ('base', 'base'),
            ('base', 'json'),
            ('base', 'xml'),
            ('json', 'base'),
            ('xml', 'base')
        ],
        'test_subtask': 'abstract_algebra',
        'test_question': 0
    }
    
    results = []
    
    print("Running comprehensive test...")
    print("=" * 60)
    
    for model_name, api_key in test_configs['models']:
        for language in test_configs['languages']:
            for input_fmt, output_fmt in test_configs['formats']:
                
                print(f"\nTesting: {model_name} - {language} - {input_fmt}/{output_fmt}")
                print("-" * 40)
                
                try:
                    result = run_single_experiment(
                        model_name=model_name,
                        api_key=api_key,
                        subtask=test_configs['test_subtask'],
                        question_idx=test_configs['test_question'],
                        permutation=[0, 1, 2, 3],  # Normal order
                        input_format=input_fmt,
                        output_format=output_fmt,
                        language=language
                    )
                    
                    # Check for issues
                    issues = []
                    
                    # 1. Check if question language matches setting
                    prompt = result.prompt_used
                    if language == 'fr':
                        # Check if question is in French
                        if not any(french_word in prompt for french_word in 
                                 ['le', 'la', 'de', 'un', 'une', 'est', 'sont']):
                            # More sophisticated check
                            if 'the' in prompt.lower() or 'is' in prompt.lower():
                                issues.append("Question appears to be in English!")
                    
                    # 2. Check format compliance
                    if output_fmt == 'json' and 'json' not in prompt.lower():
                        issues.append("JSON output format not in prompt!")
                    
                    if output_fmt == 'xml' and 'xml' not in prompt.lower():
                        issues.append("XML output format not in prompt!")
                    
                    # 3. Check parsing
                    if not result.error and not result.parsed_answer:
                        issues.append("Failed to parse answer!")
                    
                    # 4. Display critical info
                    print(f"✓ API call successful: {result.error is None}")
                    print(f"✓ Response length: {len(result.raw_response)} chars")
                    print(f"✓ Parsed answer: {result.parsed_answer}")
                    print(f"✓ Correct: {result.is_correct}")
                    
                    # Show prompt snippet
                    print(f"\nPrompt preview (first 200 chars):")
                    print(f"{result.prompt_used[:200]}...")
                    
                    # Show response snippet
                    print(f"\nResponse preview (first 200 chars):")
                    print(f"{result.raw_response[:200]}...")
                    
                    if issues:
                        print(f"\n⚠️  ISSUES DETECTED:")
                        for issue in issues:
                            print(f"   - {issue}")
                    
                    results.append({
                        'config': f"{model_name}_{language}_{input_fmt}_{output_fmt}",
                        'success': result.error is None,
                        'parsed': result.parsed_answer,
                        'issues': issues
                    })
                    
                except Exception as e:
                    print(f"❌ ERROR: {str(e)}")
                    results.append({
                        'config': f"{model_name}_{language}_{input_fmt}_{output_fmt}",
                        'success': False,
                        'error': str(e)
                    })
                
                # Small delay between tests
                import time
                time.sleep(2)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    total = len(results)
    successful = sum(1 for r in results if r.get('success', False))
    with_issues = sum(1 for r in results if r.get('issues', []))
    
    print(f"Total tests: {total}")
    print(f"Successful: {successful}")
    print(f"With issues: {with_issues}")
    
    if with_issues > 0:
        print("\nConfigurations with issues:")
        for r in results:
            if r.get('issues'):
                print(f"  - {r['config']}: {', '.join(r['issues'])}")
    
    # Save detailed results
    with open('test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nDetailed results saved to test_results.json")

if __name__ == "__main__":
    test_all_settings()