# test_permutations.py
#!/usr/bin/env python3
"""
Phase 1.5: Test Permutations
Verify that our permutation logic works correctly
"""

from pathlib import Path
import sys
import json

# Add parent directory to path to import single_question
sys.path.append(str(Path(__file__).parent))

from single_question import (
    run_single_experiment, 
    load_question,
    ResponseParser
)


def get_circular_permutations():
    """
    Generate 4 circular shift permutations
    Returns list of permutations where each is a list of indices
    """
    return [
        [0, 1, 2, 3],  # ABCD - Original
        [3, 0, 1, 2],  # DABC - Shifted right once
        [2, 3, 0, 1],  # CDAB - Shifted right twice
        [1, 2, 3, 0],  # BCDA - Shifted right thrice
    ]


def test_permutations_on_question(
    subtask: str = "abstract_algebra",
    question_idx: int = 0,
    model_name: str = "gemini-2.0-flash"
):
    """Test all 4 circular permutations on a single question"""
    
    # Load API key
    import os
    from dotenv import load_dotenv
    
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    API_KEY = os.getenv("GOOGLE_API_KEY", "")
    if not API_KEY:
        print("Please set GOOGLE_API_KEY in .env file")
        return
    
    # Load the question to display it
    question = load_question(subtask, question_idx)
    
    print(f"\n{'='*60}")
    print(f"Testing Order Sensitivity")
    print(f"{'='*60}")
    print(f"Subtask: {subtask}")
    print(f"Question: {question.question}")
    print(f"Original choices:")
    for i, choice in enumerate(question.choices):
        marker = "✓" if chr(65+i) == question.correct_answer else " "
        print(f"  {chr(65+i)}) {choice} {marker}")
    print(f"Correct answer: {question.correct_answer}")
    print(f"{'='*60}\n")
    
    # Test each permutation
    permutations = get_circular_permutations()
    results = []
    
    for perm_idx, permutation in enumerate(permutations):
        print(f"\nPermutation {perm_idx + 1}/4: {permutation}")
        
        # Show how choices are reordered
        print("Reordered choices:")
        for display_pos in range(4):
            original_pos = permutation[display_pos]
            choice = question.choices[original_pos]
            print(f"  {chr(65+display_pos)}) {choice} (originally {chr(65+original_pos)})")
        
        # Run experiment
        result = run_single_experiment(
            model_name=model_name,
            api_key=API_KEY,
            subtask=subtask,
            question_idx=question_idx,
            permutation=permutation,
            input_format="base",
            output_format="base",
            language="en"
        )
        
        # Analyze result
        if result.error:
            print(f"  ❌ API Error: {result.error}")
        else:
            print(f"  Model picked: {result.parsed_answer}")
            
            if result.parsed_answer:
                # Show what the model actually chose
                answer_idx = ord(result.parsed_answer) - ord('A')
                if 0 <= answer_idx < 4:
                    original_idx = permutation[answer_idx]
                    original_label = chr(65 + original_idx)
                    print(f"  Which maps to original: {original_label}")
                    print(f"  Correct: {'✅' if result.is_correct else '❌'}")
        
        results.append(result)
        
        # Small delay to avoid rate limits
        import time
        time.sleep(2)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    correct_count = sum(1 for r in results if r.is_correct)
    total_valid = sum(1 for r in results if r.parsed_answer is not None)
    
    print(f"Total permutations tested: {len(permutations)}")
    print(f"Successfully parsed: {total_valid}/{len(permutations)}")
    print(f"Correct answers: {correct_count}/{total_valid}")
    
    # Check consistency
    unique_answers = set(r.parsed_answer for r in results if r.parsed_answer)
    if len(unique_answers) == 1:
        print(f"\n🎯 Model is CONSISTENT - always picked position {unique_answers.pop()}")
    else:
        print(f"\n⚠️  Model is INCONSISTENT - picked different positions: {unique_answers}")
    
    # Check position bias
    position_counts = {chr(65+i): 0 for i in range(4)}
    for r in results:
        if r.parsed_answer:
            position_counts[r.parsed_answer] += 1
    
    print(f"\nPosition preference:")
    for pos, count in position_counts.items():
        print(f"  {pos}: {count} times")
    
    # Save detailed results
    output_file = project_root / "v2_results" / f"{subtask}_permutation_test.jsonl"
    with open(output_file, 'w', encoding='utf-8') as f:
        for r in results:
            result_dict = {
                "question_id": r.question_id,
                "permutation": r.permutation,
                "parsed_answer": r.parsed_answer,
                "is_correct": r.is_correct,
                "model": r.model,
                "timestamp": r.timestamp
            }
            f.write(json.dumps(result_dict) + '\n')
    
    print(f"\nDetailed results saved to: {output_file}")


def test_specific_permutation():
    """Test a specific tricky case"""
    print("\nTesting specific permutation that might reveal bias...")
    
    # Test where correct answer is in different positions
    # You can modify this to test specific scenarios
    import os
    from dotenv import load_dotenv
    
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    API_KEY = os.getenv("GOOGLE_API_KEY", "")
    
    # Find a question where correct answer is C or D (often missed)
    subtasks = ["abstract_algebra", "anatomy", "astronomy"]
    
    for subtask in subtasks[:1]:  # Just test one for now
        print(f"\nChecking {subtask}...")
        
        # Look for questions with different correct answers
        for q_idx in range(5):  # Check first 5 questions
            question = load_question(subtask, q_idx)
            
            if question.correct_answer in ['C', 'D']:
                print(f"\nFound question with answer {question.correct_answer}:")
                print(f"Q: {question.question[:100]}...")
                
                # Test with original order
                result = run_single_experiment(
                    model_name="gemini-2.0-flash",
                    api_key=API_KEY,
                    subtask=subtask,
                    question_idx=q_idx,
                    permutation=[0, 1, 2, 3],
                    input_format="base",
                    output_format="base",
                    language="en"
                )
                
                print(f"Model picked: {result.parsed_answer} (Correct: {result.is_correct})")
                break


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test permutation logic")
    parser.add_argument("--subtask", default="abstract_algebra", help="Subtask to test")
    parser.add_argument("--question", type=int, default=0, help="Question index")
    parser.add_argument("--specific", action="store_true", help="Run specific bias tests")
    
    args = parser.parse_args()
    
    if args.specific:
        test_specific_permutation()
    else:
        test_permutations_on_question(
            subtask=args.subtask,
            question_idx=args.question
        )