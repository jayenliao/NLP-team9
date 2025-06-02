#!/usr/bin/env python3
"""
Test Script: Run ONE question through ALL required settings
Tests all combinations before running full experiment
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import importlib
from dataclasses import asdict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

# Force reload to get latest changes
if 'single_question' in sys.modules:
    importlib.reload(sys.modules['single_question'])

from single_question import (
    run_single_experiment,
    load_question,
    Question,
    ExperimentResult
)
from dotenv import load_dotenv


def test_all_settings(subtask: str = "abstract_algebra", question_idx: int = 0):
    """
    Test one question across all required settings:
    - 2 models (Gemini, Mistral)
    - 2 languages (en, fr)
    - 5 format combinations
    - 4 circular permutations
    Total: 2 × 2 × 5 × 4 = 80 API calls
    """
    
    # Load API keys
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
    
    if not GOOGLE_API_KEY or not MISTRAL_API_KEY:
        print("❌ ERROR: Please set both GOOGLE_API_KEY and MISTRAL_API_KEY in .env file")
        return
    
    # Test configuration
    models = [
        ("gemini-2.0-flash-lite", GOOGLE_API_KEY),
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
    
    # Circular permutations
    circular_permutations = [
        [0, 1, 2, 3],  # ABCD
        [3, 0, 1, 2],  # DABC
        [2, 3, 0, 1],  # CDAB
        [1, 2, 3, 0],  # BCDA
    ]
    
    # Test results storage
    test_results = {
        "test_config": {
            "subtask": subtask,
            "question_idx": question_idx,
            "timestamp": datetime.now().isoformat()
        },
        "results": [],
        "summary": {
            "total_tests": 0,
            "successful": 0,
            "failed": 0,
            "parse_failures": 0
        }
    }
    
    # Also save raw JSONL for inspection
    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)
    test_jsonl = output_dir / f"test_all_settings_{subtask}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    
    print(f"🧪 SINGLE QUESTION TEST")
    print(f"{'='*60}")
    print(f"Subtask: {subtask}")
    print(f"Question Index: {question_idx}")
    print(f"Total API calls to make: {len(models) * len(languages) * len(format_combinations) * len(circular_permutations)}")
    print(f"Output: {test_jsonl}")
    print(f"{'='*60}\n")
    
    test_number = 0
    
    # Run through all combinations
    for model_name, api_key in models:
        for language in languages:
            for in_fmt, out_fmt in format_combinations:
                for perm_idx, permutation in enumerate(circular_permutations):
                    test_number += 1
                    
                    # Test identifier
                    test_id = f"{model_name}_{language}_i{in_fmt}_o{out_fmt}_p{perm_idx}"
                    
                    print(f"\n[Test {test_number}/80] {test_id}")
                    print(f"  Model: {model_name}")
                    print(f"  Language: {language}")
                    print(f"  Format: {in_fmt} → {out_fmt}")
                    print(f"  Permutation: {permutation} ({''.join(['ABCD'[p] for p in permutation])})")
                    
                    try:
                        # Run experiment
                        result = run_single_experiment(
                            model_name=model_name,
                            api_key=api_key,
                            subtask=subtask,
                            question_idx=question_idx,
                            permutation=permutation,
                            input_format=in_fmt,
                            output_format=out_fmt,
                            language=language
                        )
                        
                        # Convert to dict for storage
                        result_dict = asdict(result)
                        result_dict["test_id"] = test_id
                        
                        # Save to JSONL
                        with open(test_jsonl, 'a', encoding='utf-8') as f:
                            f.write(json.dumps(result_dict, ensure_ascii=False) + '\n')
                        
                        # Record test result
                        test_result = {
                            "test_id": test_id,
                            "model": model_name,
                            "language": language,
                            "input_format": in_fmt,
                            "output_format": out_fmt,
                            "permutation": permutation,
                            "success": not bool(result.error),
                            "parsed_answer": result.parsed_answer,
                            "model_choice_original_label": result.model_choice_original_label,
                            "is_correct": result.is_correct,
                            "error": result.error,
                            "response_length": len(result.api_response_text) if result.api_response_text else 0,
                            "response_time_ms": result.response_time_ms
                        }
                        
                        test_results["results"].append(test_result)
                        test_results["summary"]["total_tests"] += 1
                        
                        if result.error:
                            print(f"  ❌ API Error: {result.error}")
                            test_results["summary"]["failed"] += 1
                        else:
                            test_results["summary"]["successful"] += 1
                            if result.parsed_answer:
                                print(f"  ✅ Success! Answer: {result.parsed_answer} → {result.model_choice_original_label}, Correct: {result.is_correct}")
                            else:
                                print(f"  ⚠️  Success but couldn't parse answer from response")
                                test_results["summary"]["parse_failures"] += 1
                        
                        # Rate limiting
                        time.sleep(1)
                        
                    except Exception as e:
                        print(f"  ❌ Unexpected error: {e}")
                        test_results["results"].append({
                            "test_id": test_id,
                            "error": str(e),
                            "success": False
                        })
                        test_results["summary"]["failed"] += 1
                        test_results["summary"]["total_tests"] += 1
    
    # Save test summary
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_file = output_dir / f"test_single_question_summary_{timestamp}.json"
    
    with open(summary_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total tests: {test_results['summary']['total_tests']}")
    print(f"Successful: {test_results['summary']['successful']}")
    print(f"Failed: {test_results['summary']['failed']}")
    print(f"Parse failures: {test_results['summary']['parse_failures']}")
    print(f"\nResults saved to:")
    print(f"  Full data: {test_jsonl}")
    print(f"  Summary: {summary_file}")
    
    # Detailed breakdown by format
    print(f"\n{'='*60}")
    print(f"BREAKDOWN BY FORMAT")
    print(f"{'='*60}")
    
    format_stats = {}
    for result in test_results["results"]:
        if result.get("success"):
            key = f"{result['input_format']} → {result['output_format']}"
            if key not in format_stats:
                format_stats[key] = {"total": 0, "parsed": 0, "correct": 0}
            format_stats[key]["total"] += 1
            if result.get("parsed_answer"):
                format_stats[key]["parsed"] += 1
                if result.get("is_correct"):
                    format_stats[key]["correct"] += 1
    
    for fmt, stats in format_stats.items():
        parse_rate = (stats["parsed"] / stats["total"] * 100) if stats["total"] > 0 else 0
        correct_rate = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"{fmt}: {stats['parsed']}/{stats['total']} parsed ({parse_rate:.1f}%), "
              f"{stats['correct']}/{stats['total']} correct ({correct_rate:.1f}%)")
    
    return test_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test single question across all settings")
    parser.add_argument("--subtask", default="abstract_algebra", 
                       help="Subtask to test")
    parser.add_argument("--question", type=int, default=0,
                       help="Question index to test")
    
    args = parser.parse_args()
    
    print(f"Starting test with subtask: {args.subtask}, question: {args.question}")
    test_all_settings(args.subtask, args.question)