#!/usr/bin/env python3
"""
Comprehensive test of all experimental settings
Tests one econometrics question through all combinations
"""

import json
import os
from pathlib import Path
from datetime import datetime
import sys

# Add v2 directory to path
sys.path.append(str(Path(__file__).parent))

from single_question import run_single_experiment
from format_handlers import Question

def test_all_settings():
    """Test every combination and log everything"""
    
    # Load API keys
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
    
    if not GOOGLE_API_KEY or not MISTRAL_API_KEY:
        print("❌ Please set both GOOGLE_API_KEY and MISTRAL_API_KEY in .env file")
        return
    
    # Test parameters
    SUBTASK = "econometrics"
    QUESTION_IDX = 5  # Use question 5 for variety
    
    # All settings to test
    models = [
        ("gemini-2.0-flash", GOOGLE_API_KEY),
        ("mistral-small-latest", MISTRAL_API_KEY)
    ]
    
    languages = ["en", "fr"]
    
    format_combinations = [
        ("base", "base"),
        ("base", "json"),
        ("base", "xml"),
        ("json", "base"),
        ("xml", "base")
    ]
    
    # Test with normal ABCD order
    permutation = [0, 1, 2, 3]
    
    # Create test results directory
    test_dir = Path("test_results") / datetime.now().strftime("%Y%m%d_%H%M%S")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Summary file
    summary_file = test_dir / "test_summary.txt"
    
    print(f"\n{'='*80}")
    print(f"COMPREHENSIVE SETTINGS TEST - {SUBTASK}")
    print(f"{'='*80}")
    print(f"Output directory: {test_dir}")
    print(f"Testing {len(models)} models × {len(languages)} languages × {len(format_combinations)} formats = {len(models)*len(languages)*len(format_combinations)} combinations\n")
    
    all_results = []
    test_count = 0
    
    # First, let's check the actual question content
    print("📚 CHECKING QUESTION CONTENT IN DATASET:")
    print("-" * 60)
    
    try:
        import pickle
        data_path = project_root / "data" / "ds_selected.pkl"
        with open(data_path, 'rb') as f:
            dataset = pickle.load(f)
        
        for lang in languages:
            if SUBTASK in dataset and lang in dataset[SUBTASK]:
                q_data = dataset[SUBTASK][lang][QUESTION_IDX]
                print(f"\n{lang.upper()} Question #{QUESTION_IDX}:")
                print(f"Question: {q_data['question'][:100]}...")
                print(f"Choices: {[c[:30]+'...' if len(c)>30 else c for c in q_data['choices']]}")
                print(f"Answer: {q_data['answer_label']}")
            else:
                print(f"\n❌ No {lang} data found for {SUBTASK}!")
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
    
    print("\n" + "="*80)
    print("RUNNING EXPERIMENTS:")
    print("="*80)
    
    # Run all combinations
    for model_name, api_key in models:
        for language in languages:
            for input_format, output_format in format_combinations:
                test_count += 1
                
                config_str = f"{model_name}_{language}_i{input_format}_o{output_format}"
                print(f"\n[{test_count}/20] Testing: {config_str}")
                print("-" * 60)
                
                try:
                    # Run the experiment
                    result = run_single_experiment(
                        model_name=model_name,
                        api_key=api_key,
                        subtask=SUBTASK,
                        question_idx=QUESTION_IDX,
                        permutation=permutation,
                        input_format=input_format,
                        output_format=output_format,
                        language=language
                    )
                    
                    # Create detailed log
                    log_data = {
                        "config": config_str,
                        "model": model_name,
                        "language": language,
                        "input_format": input_format,
                        "output_format": output_format,
                        "success": not bool(result.error),
                        "parsed_answer": result.parsed_answer,
                        "is_correct": result.is_correct,
                        "error": result.error
                    }
                    
                    # Print key info
                    print(f"✓ API Call: {'Success' if not result.error else 'Failed'}")
                    print(f"✓ Response Length: {len(result.raw_response)} chars")
                    print(f"✓ Parsed Answer: {result.parsed_answer}")
                    print(f"✓ Correct: {result.is_correct}")
                    
                    # Save complete result
                    result_file = test_dir / f"{config_str}.json"
                    result_dict = result.__dict__ if hasattr(result, '__dict__') else {}
                    with open(result_file, 'w', encoding='utf-8') as f:
                        json.dump(result_dict, f, indent=2, ensure_ascii=False)
                    
                    # Check for specific issues
                    issues = []
                    
                    # Issue 1: Language mismatch
                    if language == "fr":
                        # Check if question is actually in French
                        if any(eng_word in result.prompt_used[:200].lower() for eng_word in 
                               ['what', 'which', 'the', 'is', 'are', 'many', 'following']):
                            issues.append("⚠️  LANGUAGE MISMATCH: French prompt contains English question!")
                    
                    # Issue 2: Format mismatch
                    if output_format == "json" and result.parsed_answer:
                        if '"reasoning"' not in result.raw_response and '"answer"' not in result.raw_response:
                            issues.append("⚠️  FORMAT ISSUE: JSON output format but no JSON in response!")
                    
                    if output_format == "xml" and result.parsed_answer:
                        if '<reasoning>' not in result.raw_response and '<answer>' not in result.raw_response:
                            issues.append("⚠️  FORMAT ISSUE: XML output format but no XML in response!")
                    
                    # Issue 3: Suspicious parsing
                    if result.parsed_answer and not result.error:
                        answer_patterns = [
                            f"answer.*{result.parsed_answer}",
                            f"réponse.*{result.parsed_answer}",
                            f"{result.parsed_answer}\\)",
                            f"<answer>{result.parsed_answer}</answer>"
                        ]
                        
                        if not any(re.search(pattern, result.raw_response, re.IGNORECASE) 
                                  for pattern in answer_patterns):
                            issues.append(f"⚠️  PARSING SUSPICION: Extracted '{result.parsed_answer}' but no clear answer pattern found!")
                    
                    # Issue 4: No answer but something parsed
                    no_answer_indicators = [
                        "cannot determine", "aucune.*réponse", "none.*options",
                        "no correct answer", "pas de réponse"
                    ]
                    if any(indicator in result.raw_response.lower() for indicator in no_answer_indicators):
                        if result.parsed_answer:
                            issues.append(f"⚠️  PARSING ERROR: Model said no answer but parsed '{result.parsed_answer}'!")
                    
                    # Print issues
                    if issues:
                        print("\n🚨 ISSUES DETECTED:")
                        for issue in issues:
                            print(f"   {issue}")
                    
                    # Save snippets for review
                    with open(summary_file, 'a', encoding='utf-8') as f:
                        f.write(f"\n{'='*80}\n")
                        f.write(f"Config: {config_str}\n")
                        f.write(f"Success: {not bool(result.error)}\n")
                        f.write(f"Parsed: {result.parsed_answer}, Correct: {result.is_correct}\n")
                        
                        if issues:
                            f.write("\nISSUES:\n")
                            for issue in issues:
                                f.write(f"  - {issue}\n")
                        
                        f.write(f"\nPROMPT (first 500 chars):\n{result.prompt_used[:500]}\n")
                        f.write(f"\nRESPONSE (first 1000 chars):\n{result.raw_response[:1000]}\n")
                    
                    all_results.append(log_data)
                    
                except Exception as e:
                    print(f"❌ EXCEPTION: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    
                    all_results.append({
                        "config": config_str,
                        "success": False,
                        "error": str(e)
                    })
    
    # Final summary
    print(f"\n{'='*80}")
    print("TEST COMPLETE - SUMMARY")
    print(f"{'='*80}")
    
    successful = sum(1 for r in all_results if r.get('success', False))
    parsed = sum(1 for r in all_results if r.get('parsed_answer'))
    correct = sum(1 for r in all_results if r.get('is_correct'))
    
    print(f"Total tests: {len(all_results)}")
    print(f"Successful API calls: {successful}")
    print(f"Successfully parsed: {parsed}")
    print(f"Correct answers: {correct}")
    
    # Check for systematic issues
    print("\n🔍 SYSTEMATIC ISSUES CHECK:")
    
    # Group results by characteristic
    fr_results = [r for r in all_results if r.get('language') == 'fr']
    json_out_results = [r for r in all_results if r.get('output_format') == 'json']
    xml_out_results = [r for r in all_results if r.get('output_format') == 'xml']
    
    if fr_results:
        fr_success = sum(1 for r in fr_results if r.get('success', False))
        print(f"\nFrench experiments: {fr_success}/{len(fr_results)} successful")
    
    if json_out_results:
        json_parsed = sum(1 for r in json_out_results if r.get('parsed_answer'))
        print(f"JSON output parsing: {json_parsed}/{len(json_out_results)} parsed")
    
    if xml_out_results:
        xml_parsed = sum(1 for r in xml_out_results if r.get('parsed_answer'))
        print(f"XML output parsing: {xml_parsed}/{len(xml_out_results)} parsed")
    
    print(f"\n📁 Full results saved to: {test_dir}")
    print("Review the individual JSON files and test_summary.txt for details")
    
    # Final instructions
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("1. Check test_summary.txt for any ⚠️  warnings")
    print("2. Look at the JSON files for suspicious parsing")
    print("3. Share any issues found back for analysis")
    print("="*80)

if __name__ == "__main__":
    import re  # Add this import at the top
    test_all_settings()