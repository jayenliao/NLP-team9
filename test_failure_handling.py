#!/usr/bin/env python3
"""
Test script to verify failure handling in the smart runner
Simulates: successful run, parse error, API fail, unknown fail
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import time
import importlib
from unittest.mock import patch, MagicMock
from dataclasses import asdict

# Add project directory to path
sys.path.append(str(Path(__file__).parent))

# Force reload modules
if 'smart_runner' in sys.modules:
    importlib.reload(sys.modules['smart_runner'])
if 'single_question' in sys.modules:
    importlib.reload(sys.modules['single_question'])

from smart_runner import SmartExperimentRunner
from single_question import ExperimentResult


def create_mock_responses():
    """Create different types of responses for testing"""
    
    # Base data for all responses - matching new field order
    base_data = {
        "trial_id": "test-uuid",
        "question_id": "test_q0",
        "question_index": 0,
        "subtask": "test_subtask",
        "model": "test_model",
        "language": "en",
        "input_format": "base",
        "output_format": "base",
        "permutation": [0, 1, 2, 3],
        "permutation_string": "ABCD",
        "prompt_used": "Test prompt",
        "api_call_successful": True,
        "api_raw_response": "Raw response object",
        "api_response_text": "",
        "ground_truth_answer": "B",
        "question_text": "Test question?",
        "original_choices": ["A", "B", "C", "D"],
        "permuted_choices": ["A", "B", "C", "D"],
        "timestamp": datetime.now().isoformat(),
        # Optional fields
        "response_time_ms": 100,
        "parsed_answer": None,
        "model_choice_original_label": None,
        "is_correct": None,
        "error": None
    }
    
    # Successful response
    success_data = base_data.copy()
    success_data.update({
        "api_response_text": "Let me solve this step by step...\n\nAnswer: B",
        "parsed_answer": "B",
        "model_choice_original_label": "B",
        "is_correct": True
    })
    success_result = ExperimentResult(**success_data)
    
    # Parse error - response received but can't extract answer
    parse_error_data = base_data.copy()
    parse_error_data.update({
        "question_id": "test_q1",
        "api_response_text": "The answer is probably B but I'm not sure. Maybe it could be C.",
        "parsed_answer": None,
        "model_choice_original_label": None,
        "is_correct": None
    })
    parse_error_result = ExperimentResult(**parse_error_data)
    
    # API error - API call failed
    api_error_data = base_data.copy()
    api_error_data.update({
        "question_id": "test_q2",
        "api_call_successful": False,
        "api_response_text": "",
        "error": "API rate limit exceeded",
        "parsed_answer": None,
        "model_choice_original_label": None,
        "is_correct": None
    })
    api_error_result = ExperimentResult(**api_error_data)
    
    return {
        "success": success_result,
        "parse_error": parse_error_result,
        "api_error": api_error_result
    }


def test_failure_handling():
    """Test the smart runner with different failure scenarios"""
    
    print("🧪 TESTING FAILURE HANDLING")
    print("="*60)
    
    # Clean up any existing test results
    test_results_file = Path("results/test_subtask_test_model_en_ibase_obase.jsonl")
    test_summary_file = Path("results/test_subtask_test_model_en_ibase_obase_summary.json")
    
    # Remove if exists
    if test_results_file.exists():
        test_results_file.unlink()
    if test_summary_file.exists():
        test_summary_file.unlink()
    
    # Create mock responses
    mock_responses = create_mock_responses()
    
    # Define test scenario
    def mock_run_single_experiment(**kwargs):
        """Mock function that returns different results based on question index"""
        q_idx = kwargs.get("question_idx", 0)
        
        if q_idx == 0:
            # First question: always succeeds
            return mock_responses["success"]
        elif q_idx == 1:
            # Second question: parse error on first try, success on retry
            if not hasattr(mock_run_single_experiment, 'q1_attempts'):
                mock_run_single_experiment.q1_attempts = 0
            mock_run_single_experiment.q1_attempts += 1
            
            if mock_run_single_experiment.q1_attempts == 1:
                return mock_responses["parse_error"]
            else:
                # Success on retry - create new instance with updated values
                result = create_mock_responses()["success"]
                result.parsed_answer = "C"
                result.model_choice_original_label = "C"
                return result
        elif q_idx == 2:
            # Third question: API error, then still fails on retry
            return mock_responses["api_error"]
        elif q_idx == 3:
            # Fourth question: Unknown error (exception)
            raise Exception("Connection timeout")
        else:
            # All others succeed
            return mock_responses["success"]
    
    # Patch the run_single_experiment function
    with patch('smart_runner.run_single_experiment', side_effect=mock_run_single_experiment):
        # Create runner with small test
        runner = SmartExperimentRunner(
            subtask="test_subtask",
            model_name="test_model",
            api_key="test_key",
            language="en",
            input_format="base",
            output_format="base",
            num_questions=4,  # Test 4 questions
            start_question=0
        )
        
        # Override rate limiting for faster test
        with patch('time.sleep', return_value=None):
            runner.run()
    
    # Check the results
    print("\n" + "="*60)
    print("CHECKING RESULTS")
    print("="*60)
    
    # Load summary
    with open(test_summary_file, 'r') as f:
        summary = json.load(f)
    
    print("\nSummary:")
    for key, value in summary.items():
        if key not in ["created_at", "completed_at", "completed_tasks"]:
            print(f"  {key}: {value}")
    
    print("\nDetailed Results:")
    
    # Read JSONL file to check results
    results_by_task = {}
    with open(test_results_file, 'r') as f:
        for line in f:
            result = json.loads(line)
            task_id = result.get("task_id", "unknown")
            results_by_task[task_id] = result
    
    # Check successful tasks
    print("\n✅ Completed tasks:")
    completed_tasks = summary.get("completed_tasks", [])
    for task_id in sorted(completed_tasks):
        if task_id in results_by_task:
            result = results_by_task[task_id]
            print(f"  {task_id}: Answer={result.get('parsed_answer')}, "
                  f"Original={result.get('model_choice_original_label')}, "
                  f"Retries={result.get('retry_attempt', 1)}")
    
    # Check abandoned tasks
    print("\n❌ Abandoned tasks:")
    abandoned = summary.get("abandoned_tasks", {})
    for task_id, info in abandoned.items():
        print(f"  {task_id}: {info['final_error']} (after {info['attempts']} attempts)")
    
    # Verify expected behavior
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    
    # Count by question
    q0_completed = len([t for t in completed_tasks if t.startswith("q0_")])
    q1_completed = len([t for t in completed_tasks if t.startswith("q1_")])
    q2_abandoned = len([t for t in abandoned if t.startswith("q2_")])
    q3_abandoned = len([t for t in abandoned if t.startswith("q3_")])
    
    print(f"Question 0 (should all succeed): {q0_completed} completed")
    print(f"Question 1 (should succeed on retry): {q1_completed} completed")
    print(f"Question 2 (should be abandoned - API error): {q2_abandoned} abandoned")
    print(f"Question 3 (should be abandoned - unknown error): {q3_abandoned} abandoned")
    
    # Check specific error types
    print("\nError Types in Abandoned Tasks:")
    for task_id, task_data in abandoned.items():
        error_type = "API error" if "API" in task_data['final_error'] else "Unknown error"
        print(f"  {task_id}: {error_type}")
    
    # Verify JSONL contains complete data
    print("\nData Completeness Check:")
    if results_by_task:
        sample_result = list(results_by_task.values())[0]
        required_fields = [
            "trial_id", "question_id", "prompt_used", "api_response_text",
            "parsed_answer", "model_choice_original_label", "timestamp"
        ]
        missing_fields = [f for f in required_fields if f not in sample_result]
        if missing_fields:
            print(f"  ⚠️  Missing fields: {missing_fields}")
        else:
            print(f"  ✅ All required fields present")
            print(f"  Sample prompt length: {len(sample_result.get('prompt_used', ''))}")
            print(f"  Sample response length: {len(sample_result.get('api_response_text', ''))}")
    
    # Clean up test files
    print("\n✅ Test complete! Test files saved in results/ directory")
    print(f"  - {test_results_file}")
    print(f"  - {test_summary_file}")


if __name__ == "__main__":
    test_failure_handling()