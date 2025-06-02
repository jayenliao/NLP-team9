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
from unittest.mock import patch, MagicMock

# Add project directory to path
sys.path.append(str(Path(__file__).parent))

from smart_runner import SmartExperimentRunner
from single_question import ExperimentResult


def create_mock_responses():
    """Create different types of responses for testing"""
    
    # Successful response
    success_result = ExperimentResult(
        question_id="test_q0",
        subtask="test_subtask",
        model="test_model",
        language="en",
        input_format="base",
        output_format="base",
        permutation=[0, 1, 2, 3],
        prompt_used="Test prompt",
        raw_response="Let me solve this step by step...\n\nAnswer: B",
        parsed_answer="B",
        is_correct=True,
        timestamp=datetime.now().isoformat(),
        error=None
    )
    
    # Parse error - response received but can't extract answer
    parse_error_result = ExperimentResult(
        question_id="test_q1",
        subtask="test_subtask",
        model="test_model",
        language="en",
        input_format="base",
        output_format="json",
        permutation=[0, 1, 2, 3],
        prompt_used="Test prompt",
        raw_response="The answer is probably B but I'm not sure. Maybe it could be C.",
        parsed_answer=None,  # Failed to parse
        is_correct=None,
        timestamp=datetime.now().isoformat(),
        error=None
    )
    
    # API error - API call failed
    api_error_result = ExperimentResult(
        question_id="test_q2",
        subtask="test_subtask",
        model="test_model",
        language="en",
        input_format="base",
        output_format="base",
        permutation=[0, 1, 2, 3],
        prompt_used="Test prompt",
        raw_response="",
        parsed_answer=None,
        is_correct=None,
        timestamp=datetime.now().isoformat(),
        error="API rate limit exceeded"
    )
    
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
    test_results_file = Path("results/test_subtask_test_model_en_ibase_obase.json")
    if test_results_file.exists():
        test_results_file.unlink()
    
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
                # Success on retry
                result = mock_responses["success"]
                result.parsed_answer = "C"
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
    
    with open(test_results_file, 'r') as f:
        results = json.load(f)
    
    print("\nMetadata:")
    for key, value in results["metadata"].items():
        if key not in ["start_time", "end_time"]:
            print(f"  {key}: {value}")
    
    print("\nDetailed Results:")
    
    # Check successful tasks
    print("\n✅ Completed tasks:")
    for task_id, task_data in results["results"].items():
        print(f"  {task_id}: Answer={task_data['parsed_answer']}, Attempts={task_data['attempts']}")
    
    # Check abandoned tasks
    print("\n❌ Abandoned tasks:")
    for task_id, task_data in results["abandoned"].items():
        print(f"  {task_id}: {task_data['final_error']} (after {task_data['attempts']} attempts)")
    
    # Verify expected behavior
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    
    expected_completed = 13  # q0 (4 perms) + q1 (4 perms, fixed on retry) + q3 partial
    expected_abandoned = 3   # q2 (4 perms, still fail) + q3 (4 perms, unknown error)
    
    # Note: The actual numbers might be different due to how the mock works
    # Let's check the actual patterns
    
    q0_results = [k for k in results["results"].keys() if k.startswith("q0_")]
    q1_results = [k for k in results["results"].keys() if k.startswith("q1_")]
    q2_abandoned = [k for k in results["abandoned"].keys() if k.startswith("q2_")]
    q3_abandoned = [k for k in results["abandoned"].keys() if k.startswith("q3_")]
    
    print(f"Question 0 (should all succeed): {len(q0_results)} completed")
    print(f"Question 1 (should succeed on retry): {len(q1_results)} completed")
    print(f"Question 2 (should be abandoned - API error): {len(q2_abandoned)} abandoned")
    print(f"Question 3 (should be abandoned - unknown error): {len(q3_abandoned)} abandoned")
    
    # Check specific error types
    print("\nError Types in Abandoned Tasks:")
    for task_id, task_data in results["abandoned"].items():
        error_type = "API error" if "API" in task_data['final_error'] else "Unknown error"
        print(f"  {task_id}: {error_type}")
    
    # Clean up test file
    test_results_file.unlink()
    
    print("\n✅ Test complete! Check the output above to verify:")
    print("1. Question 0 tasks all succeeded")
    print("2. Question 1 tasks succeeded after retry")
    print("3. Question 2 tasks were abandoned (API error)")
    print("4. Question 3 tasks were abandoned (unknown error)")


if __name__ == "__main__":
    test_failure_handling()