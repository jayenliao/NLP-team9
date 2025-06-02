#!/usr/bin/env python3
"""
Phase 1: Single Question Pipeline
Test running one question through the entire system
"""

import json
import pickle
import os
import time
import uuid
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import re
from pathlib import Path

# For API calls
from google import genai as google_genai
from mistralai import Mistral
from dotenv import load_dotenv

# Import our format handlers (assuming they're in the same directory)
try:
    from format_handlers import Question, PromptFormatter, ResponseParser
except ImportError:
    # If running as a module
    from .format_handlers import Question, PromptFormatter, ResponseParser


@dataclass
class ExperimentResult:
    """Complete result from running one experiment"""
    # Identifiers
    trial_id: str  # Unique ID for this API call
    question_id: str
    question_index: int
    subtask: str
    
    # Model configuration
    model: str
    language: str
    input_format: str
    output_format: str
    
    # Permutation details
    permutation: List[int]  # [0,1,2,3] means ABCD
    permutation_string: str  # "ABCD"
    
    # API call details
    prompt_used: str
    api_call_successful: bool
    api_raw_response: str  # Full API response object as string
    api_response_text: str  # Extracted text from response
    
    # Ground truth
    ground_truth_answer: str
    
    # Question content
    question_text: str
    original_choices: List[str]  # Original order [A, B, C, D]
    permuted_choices: List[str]  # After permutation
    
    # Metadata
    timestamp: str
    
    # Optional fields with defaults (must come last)
    response_time_ms: Optional[int] = None
    parsed_answer: Optional[str] = None  # 'A', 'B', 'C', 'D', or None
    model_choice_original_label: Optional[str] = None  # After mapping back through permutation
    is_correct: Optional[bool] = None
    error: Optional[str] = None


class APIClient:
    """Handles API calls with proper error handling"""
    
    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.model_family = "gemini" if "gemini" in model_name else "mistral"
        self.last_raw_response = None  # Store raw response for access
        
        if self.model_family == "gemini":
            self.client = google_genai.Client(api_key=api_key)
        else:
            self.client = Mistral(api_key=api_key)
    
    def call(self, prompt: str) -> Tuple[str, Optional[str]]:
        """
        Make API call
        Returns: (response_text, error_message)
        """
        self.last_raw_response = None
        
        try:
            if self.model_family == "gemini":
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                self.last_raw_response = response
                return response.text, None
            else:
                response = self.client.chat.complete(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}]
                )
                self.last_raw_response = response
                return response.choices[0].message.content, None
                
        except Exception as e:
            return "", str(e)


def load_question(subtask: str, question_idx: int = 0, language: str = "en") -> Question:
    """Load a single question from the dataset"""
    # Path relative to project root
    import sys
    from pathlib import Path
    
    # Get project root (parent of current directory)
    project_root = Path(__file__).parent
    data_path = project_root / "data" / "ds_selected.pkl"
    
    with open(data_path, 'rb') as f:
        dataset = pickle.load(f)
    
    # Get questions for specified language
    if subtask not in dataset or language not in dataset[subtask]:
        raise ValueError(f"Subtask '{subtask}' or language '{language}' not found in dataset")
    
    questions = dataset[subtask][language]
    if question_idx >= len(questions):
        raise ValueError(f"Question index {question_idx} out of range for subtask {subtask}")
    
    q_data = questions[question_idx]
    
    return Question(
        id=q_data.get('id', f"{subtask}_{question_idx}"),
        question=q_data['question'],
        choices=q_data['choices'],
        correct_answer=q_data['answer_label'],
        subtask=subtask
    )


def run_single_experiment(
    model_name: str = "gemini-2.0-flash-lite",
    api_key: str = "",
    subtask: str = "abstract_algebra",
    question_idx: int = 0,
    permutation: List[int] = [0, 1, 2, 3],
    input_format: str = "base",
    output_format: str = "base",
    language: str = "en"
) -> ExperimentResult:
    """Run a single question through the pipeline"""
    
    import uuid
    
    # Initialize components
    formatter = PromptFormatter()
    parser = ResponseParser()
    api_client = APIClient(model_name, api_key)
    
    # Load question
    question = load_question(subtask, question_idx, language)
    
    # Format prompt
    prompt = formatter.format_prompt(
        question, permutation, input_format, output_format, language
    )
    
    # Time the API call
    start_time = time.time()
    
    # Make API call
    response_text, error = api_client.call(prompt)
    
    response_time_ms = int((time.time() - start_time) * 1000)
    
    # Get raw API response (for Gemini/Mistral specific handling)
    api_raw_response = ""
    if hasattr(api_client, 'last_raw_response'):
        api_raw_response = str(api_client.last_raw_response)
    
    # Parse response
    parsed_answer = None
    model_choice_original_label = None
    is_correct = None
    
    if response_text and not error:
        parsed_answer = parser.parse(response_text, output_format, language)
        
        # Map back to original position
        if parsed_answer:
            answer_idx = ord(parsed_answer) - ord('A')
            if 0 <= answer_idx < 4:
                original_position = permutation[answer_idx]
                model_choice_original_label = chr(ord('A') + original_position)
                is_correct = (model_choice_original_label == question.correct_answer)
    
    # Create permutation string (e.g., "ABCD" or "DABC")
    permutation_string = ''.join([chr(ord('A') + p) for p in permutation])
    
    # Get permuted choices
    permuted_choices = [question.choices[i] for i in permutation]
    
    return ExperimentResult(
        trial_id=str(uuid.uuid4()),
        question_id=question.id,
        question_index=question_idx,
        subtask=subtask,
        model=model_name,
        language=language,
        input_format=input_format,
        output_format=output_format,
        permutation=permutation,
        permutation_string=permutation_string,
        prompt_used=prompt,
        api_call_successful=(error is None),
        api_raw_response=api_raw_response,
        api_response_text=response_text,
        ground_truth_answer=question.correct_answer,
        question_text=question.question,
        original_choices=question.choices,
        permuted_choices=permuted_choices,
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        # Optional fields
        response_time_ms=response_time_ms,
        parsed_answer=parsed_answer,
        model_choice_original_label=model_choice_original_label,
        is_correct=is_correct,
        error=error
    )


def save_result(result: ExperimentResult, output_dir: str = "results"):
    """Save result to JSONL file with complete data"""
    from pathlib import Path
    
    # Use current directory as base
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    # Convert to dict for JSON serialization - includes ALL fields
    result_dict = asdict(result)
    
    # Save to subtask-specific JSONL file
    output_file = output_path / f"{result.subtask}_test.jsonl"
    
    with open(output_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(result_dict, ensure_ascii=False) + '\n')
    
    return str(output_file)


# Test function
def test_single_question():
    """Test the pipeline with one question"""
    
    # Load from .env file in project root
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    
    if not GOOGLE_API_KEY:
        print("Please set GOOGLE_API_KEY in .env file or environment variable")
        return
    
    print("Running single question test...")
    
    try:
        result = run_single_experiment(
            model_name="gemini-2.0-flash-lite",
            api_key=GOOGLE_API_KEY,
            subtask="abstract_algebra",
            question_idx=0,
            permutation=[0, 1, 2, 3],  # Normal ABCD order
            input_format="base",
            output_format="base",
            language="en"
        )
    
        print(f"\nTrial ID: {result.trial_id}")
        print(f"Question: {result.question_text[:100]}...")
        print(f"Permutation: {result.permutation_string}")
        print(f"\nPrompt sent ({len(result.prompt_used)} chars):")
        print(f"{result.prompt_used[:200]}...\n")
        print(f"Response received ({len(result.api_response_text)} chars):")
        print(f"{result.api_response_text[:200]}...\n")
        print(f"Parsed Answer: {result.parsed_answer}")
        print(f"Original Label: {getattr(result, 'model_choice_original_label', 'N/A')}")
        print(f"Ground Truth: {result.ground_truth_answer}")
        print(f"Correct: {result.is_correct}")
        print(f"Response Time: {result.response_time_ms}ms")
        print(f"Error: {result.error}")
    
        if not result.error:
            output_file = save_result(result)
            print(f"\nComplete result saved to: {output_file}")
            print(f"Result size: ~{len(json.dumps(asdict(result)))} bytes")
    
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_single_question()