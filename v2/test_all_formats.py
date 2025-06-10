#!/usr/bin/env python3
"""
Test all format combinations to ensure they work correctly
"""

from pathlib import Path
import sys
import os
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from single_question import run_single_experiment, load_question
from format_handlers import PromptFormatter, ResponseParser


def test_all_format_combinations():
    """Test all 5 format combinations on one question"""
    
    # Load API key
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    API_KEY = os.getenv("GOOGLE_API_KEY", "")
    if not API_KEY:
        print("Please set GOOGLE_API_KEY in .env file")
        return
    
    # Format combinations to test
    format_combinations = [
        ("base", "base", "Plain text input → Plain text output"),
        ("base", "json", "Plain text input → JSON output"),
        ("base", "xml", "Plain text input → XML output"), 
        ("json", "base", "JSON input → Plain text output"),
        ("xml", "base", "XML input → Plain text output")
    ]
    
    # Test parameters
    subtask = "abstract_algebra"
    question_idx = 0
    model_name = "gemini-2.0-flash"
    language = "en"
    
    # Load the question once to display it
    question = load_question(subtask, question_idx)
    
    print(f"\n{'='*80}")
    print(f"Testing All Format Combinations")
    print(f"{'='*80}")
    print(f"Question: {question.question}")
    print(f"Correct Answer: {question.correct_answer}")
    print(f"{'='*80}\n")
    
    results = []
    
    for in_fmt, out_fmt, description in format_combinations:
        print(f"\n{'-'*60}")
        print(f"Testing: {description}")
        print(f"Format: {in_fmt} → {out_fmt}")
        print(f"{'-'*60}")
        
        # Show the prompt that will be sent
        formatter = PromptFormatter()
        prompt = formatter.format_prompt(
            question,
            [0, 1, 2, 3],  # Normal order for testing
            in_fmt,
            out_fmt,
            language
        )
        
        print(f"\nPrompt Preview:")
        print("---")
        if len(prompt) > 300:
            print(f"{prompt[:300]}...")
        else:
            print(prompt)
        print("---")
        
        # Run the experiment
        result = run_single_experiment(
            model_name=model_name,
            api_key=API_KEY,
            subtask=subtask,
            question_idx=question_idx,
            permutation=[0, 1, 2, 3],
            input_format=in_fmt,
            output_format=out_fmt,
            language=language
        )
        
        # Display results
        if result.error:
            print(f"\n❌ API Error: {result.error}")
        else:
            print(f"\nResponse Preview:")
            if len(result.raw_response) > 300:
                print(f"{result.raw_response[:300]}...")
            else:
                print(result.raw_response)
            
            print(f"\n✅ Parsed Answer: {result.parsed_answer}")
            print(f"Correct: {result.is_correct}")
        
        results.append({
            'format': f"{in_fmt} → {out_fmt}",
            'success': not result.error,
            'parsed': result.parsed_answer is not None,
            'correct': result.is_correct
        })
        
        # Wait between calls
        time.sleep(3)
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    
    print(f"\n{'Format':<20} {'API Call':<10} {'Parsed':<10} {'Correct':<10}")
    print(f"{'-'*50}")
    
    for r in results:
        api_status = "✅" if r['success'] else "❌"
        parse_status = "✅" if r['parsed'] else "❌"
        correct_status = "✅" if r['correct'] else "❌" if r['correct'] is False else "—"
        
        print(f"{r['format']:<20} {api_status:<10} {parse_status:<10} {correct_status:<10}")


def test_specific_format(input_format: str, output_format: str):
    """Test a specific format combination in detail"""
    
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    API_KEY = os.getenv("GOOGLE_API_KEY", "")
    
    print(f"\nTesting {input_format} → {output_format} in detail...")
    
    # Test on different subtasks to see if format affects different domains
    test_cases = [
        ("abstract_algebra", 0),  # Math
        ("anatomy", 0),           # Medical
        ("formal_logic", 2),      # Logic (the tricky one)
    ]
    
    for subtask, q_idx in test_cases:
        print(f"\n\nTesting on {subtask}...")
        
        question = load_question(subtask, q_idx)
        print(f"Q: {question.question[:80]}...")
        
        result = run_single_experiment(
            model_name="gemini-2.0-flash",
            api_key=API_KEY,
            subtask=subtask,
            question_idx=q_idx,
            permutation=[0, 1, 2, 3],
            input_format=input_format,
            output_format=output_format,
            language="en"
        )
        
        print(f"Parsed: {result.parsed_answer}, Correct: {result.is_correct}")
        
        time.sleep(2)


def test_parser_robustness():
    """Test the parser with various response formats"""
    
    parser = ResponseParser()
    
    test_responses = {
        "base": [
            "The answer is B.",
            "Answer: C",
            "After analysis, I choose D",
            "A",
            "My final answer is A.",
            "réponse: B",  # French
        ],
        "json": [
            '{"reasoning": "...", "answer": "B"}',
            '```json\n{"answer": "C", "reasoning": "..."}\n```',
            '{"answer":"D"}',
            'The answer in JSON format: {"answer": "A"}',
        ],
        "xml": [
            '<answer>B</answer>',
            '```xml\n<response><answer>C</answer></response>\n```',
            '<response>\n  <reasoning>...</reasoning>\n  <answer>D</answer>\n</response>',
        ]
    }
    
    print("\nTesting parser robustness...")
    print(f"{'-'*50}")
    
    for format_type, responses in test_responses.items():
        print(f"\n{format_type.upper()} format parsing:")
        for response in responses:
            parsed = parser.parse(response, format_type, "en")
            status = "✅" if parsed else "❌"
            print(f"  {status} '{response[:50]}...' → {parsed}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test format combinations")
    parser.add_argument("--all", action="store_true", help="Test all format combinations")
    parser.add_argument("--specific", nargs=2, metavar=("IN", "OUT"), 
                       help="Test specific format (e.g., --specific json base)")
    parser.add_argument("--parser", action="store_true", help="Test parser robustness")
    
    args = parser.parse_args()
    
    if args.all:
        test_all_format_combinations()
    elif args.specific:
        test_specific_format(args.specific[0], args.specific[1])
    elif args.parser:
        test_parser_robustness()
    else:
        # Default: run all tests
        print("Running all format tests...")
        test_all_format_combinations()