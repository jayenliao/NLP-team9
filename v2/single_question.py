# single_question.py
#!/usr/bin/env python3
"""
Phase 1: Single Question Pipeline
Test running one question through the entire system
"""

import json
import pickle
import os
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re
from pathlib import Path

# For API calls
from google import genai as google_genai
from mistralai import Mistral
from dotenv import load_dotenv

# Import our format handlers (assuming they're in the same v2 directory)
try:
    from format_handlers import Question, PromptFormatter, ResponseParser
except ImportError:
    # If running as a module
    from .format_handlers import Question, PromptFormatter, ResponseParser


@dataclass
class ExperimentResult:
    """Result from running one experiment"""
    question_id: str
    subtask: str
    model: str
    language: str
    input_format: str
    output_format: str
    permutation: List[int]  # [0,1,2,3] means ABCD, [1,0,2,3] means BACD
    prompt_used: str
    raw_response: str
    parsed_answer: Optional[str]  # 'A', 'B', 'C', 'D', or None
    is_correct: Optional[bool]
    timestamp: str
    error: Optional[str] = None


class APIClient:
    """Handles API calls with proper error handling"""
    
    def __init__(self, model_name: str, api_key: str):
        self.model_name = model_name
        self.model_family = "gemini" if "gemini" in model_name else "mistral"
        
        if self.model_family == "gemini":
            self.client = google_genai.Client(api_key=api_key)
        else:
            self.client = Mistral(api_key=api_key)
    
    def call(self, prompt: str) -> Tuple[str, Optional[str]]:
        """
        Make API call
        Returns: (response_text, error_message)
        """
        try:
            if self.model_family == "gemini":
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                return response.text, None
            else:
                response = self.client.chat.complete(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.choices[0].message.content, None
                
        except Exception as e:
            return "", str(e)


def load_question(subtask: str, question_idx: int = 0, language: str = "en") -> Question:
    """Load a single question from the dataset"""
    # Path relative to project root
    import sys
    from pathlib import Path
    
    # Get project root (parent of v2 directory)
    project_root = Path(__file__).parent.parent
    data_path = project_root / "data" / "ds_selected.pkl"
    
    with open(data_path, 'rb') as f:
        dataset = pickle.load(f)
    
    # Use the language parameter instead of hardcoded 'en'
    questions = dataset[subtask][language]  # ← Fixed!
    q_data = questions[question_idx]
    
    return Question(
        id=q_data.get('id', f"{subtask}_{question_idx}"),
        question=q_data['question'],
        choices=q_data['choices'],
        correct_answer=q_data['answer_label'],
        subtask=subtask
    )


def run_single_experiment(
    model_name: str = "gemini-2.0-flash",
    api_key: str = "",
    subtask: str = "abstract_algebra",
    question_idx: int = 0,
    permutation: List[int] = [0, 1, 2, 3],
    input_format: str = "base",
    output_format: str = "base",
    language: str = "en"
) -> ExperimentResult:
    """Run a single question through the pipeline"""
    
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
    
    # Make API call
    response_text, error = api_client.call(prompt)
    
    # Parse response
    parsed_answer = None
    if response_text and not error:
        parsed_answer = parser.parse(response_text, output_format, language)
    
    # Determine if correct
    is_correct = None
    if parsed_answer:
        # Map back to original position
        answer_idx = ord(parsed_answer) - ord('A')
        if 0 <= answer_idx < 4:
            original_position = permutation[answer_idx]
            original_label = chr(ord('A') + original_position)
            is_correct = (original_label == question.correct_answer)
    
    return ExperimentResult(
        question_id=question.id,
        subtask=subtask,
        model=model_name,
        language=language,
        input_format=input_format,
        output_format=output_format,
        permutation=permutation,
        prompt_used=prompt,
        raw_response=response_text,
        parsed_answer=parsed_answer,
        is_correct=is_correct,
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        error=error
    )


def save_result(result: ExperimentResult, output_dir: str = "v2_results"):
    """Save result to file"""
    from pathlib import Path
    
    # Get project root
    project_root = Path(__file__).parent.parent
    output_path = project_root / output_dir
    output_path.mkdir(exist_ok=True)
    
    # Convert to dict for JSON serialization
    result_dict = {
        "question_id": result.question_id,
        "subtask": result.subtask,
        "model": result.model,
        "language": result.language,
        "input_format": result.input_format,
        "output_format": result.output_format,
        "permutation": result.permutation,
        "prompt_used": result.prompt_used,
        "raw_response": result.raw_response,
        "parsed_answer": result.parsed_answer,
        "is_correct": result.is_correct,
        "timestamp": result.timestamp,
        "error": result.error
    }
    
    # Save to subtask-specific file
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
    
    result = run_single_experiment(
        model_name="gemini-2.0-flash",
        api_key=GOOGLE_API_KEY,
        subtask="abstract_algebra",
        question_idx=0,
        permutation=[0, 1, 2, 3],  # Normal ABCD order
        input_format="base",
        output_format="base",
        language="en"
    )
    
    print(f"\nQuestion: {result.prompt_used}")
    print(f"\nResponse: {result.raw_response}")
    print(f"\nParsed Answer: {result.parsed_answer}")
    print(f"Correct: {result.is_correct}")
    print(f"Error: {result.error}")
    
    if not result.error:
        output_file = save_result(result)
        print(f"\nResult saved to: {output_file}")


if __name__ == "__main__":
    test_single_question()