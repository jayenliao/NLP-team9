# experiments/core_runner.py
import os
import re
import uuid
from typing import Any
from google import genai as google_genai
from mistralai import Mistral
from utils import load_api_keys 

def load_prompt_template(format_name: str) -> str | None:
    """Loads the content of a prompt template file."""
    template_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
    template_filename = f"{format_name}_prompt.txt"
    template_path = os.path.join(template_dir, template_filename)
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception: 
        return None

def format_prompt(template_content: str, data_item: dict, option_order: list[str]) -> str | None:
    """Formats the prompt template with question data and specified option order."""
    try:
        if len(data_item['choices']) != 4 or len(option_order) != 4:
            return None # Basic validation

        original_choices = {'A': data_item['choices'][0], 'B': data_item['choices'][1], 'C': data_item['choices'][2], 'D': data_item['choices'][3]}
        format_context = {
            'Question': data_item['question'],
            'A': original_choices[option_order[0]],
            'B': original_choices[option_order[1]],
            'C': original_choices[option_order[2]],
            'D': original_choices[option_order[3]],
        }
        return template_content.format(**format_context)
    except (KeyError, IndexError): # Handle missing keys or incorrect list sizes
        return None
    except Exception: # Generic catch-all
        return None

def parse_response(api_response_text: str) -> str | None:
    """Parses the API response text to extract the answer choice (A, B, C, or D)."""
    if not api_response_text:
        return None
    # Regex to find 'Answer: $LETTER' at the start/end of a line, case-insensitive
    match = re.search(r"^\s*Answer:\s*([A-D])\s*$", api_response_text, re.IGNORECASE | re.MULTILINE)
    if match:
        return match.group(1).upper()
    else:
        return None

def structure_result(
    data_item: dict,
    subtask: str,
    language: str,
    model_name: str,
    input_format: str,
    option_permutation: list[str],
    api_raw_response: Any | None,
    api_call_successful: bool,
    extracted_answer: str | None,
    log_probabilities: dict | None = None,
    question_index: int = -1
) -> dict:
    """Structures the results of a single experiment trial into a dictionary."""
    ground_truth_label = None
    is_correct = None
    try:
        # Determine ground truth
        if 'answer_label' in data_item:
            ground_truth_label = data_item['answer_label']
        elif 'answer' in data_item and isinstance(data_item['answer'], int):
            ground_truth_label = chr(ord('A') + data_item['answer'])
        elif 'Answer' in data_item and isinstance(data_item['Answer'], str):
             ground_truth_label = data_item['Answer'].upper()
        else:
            ground_truth_label = "UNKNOWN"

        if extracted_answer is not None and ground_truth_label not in ["UNKNOWN", "ERROR"]:
            is_correct = (extracted_answer == ground_truth_label)
    except Exception:
        ground_truth_label = "ERROR"
        is_correct = None

    # Determine Question ID
    q_id = data_item.get('id', data_item.get('index', data_item.get('Unnamed: 0', f"idx_{question_index}")))

    result = {
        "trial_id": str(uuid.uuid4()),
        "question_id": q_id,
        "question_index": question_index,
        "subtask": subtask,
        "language": language,
        "model_name": model_name,
        "input_format": input_format,
        "option_permutation": "".join(option_permutation),
        "api_call_successful": api_call_successful,
        "api_raw_response": str(api_raw_response) if api_raw_response is not None else None,
        "extracted_answer": extracted_answer,
        "log_probabilities": log_probabilities,
        "ground_truth_answer": ground_truth_label,
        "is_correct": is_correct
    }
    return result

def get_api_client(model_family: str) -> Any | None:
    """Initializes and returns the API client based on the model family."""
    google_api_key, mistral_api_key = load_api_keys()

    if model_family.lower() == 'gemini':
        if not google_api_key: return None
        try:
            return google_genai.Client(api_key=google_api_key)
        except Exception:
            return None
    elif model_family.lower() == 'mistral':
        if not mistral_api_key: return None
        try:
            return Mistral(api_key=mistral_api_key)
        except Exception:
            return None
    else:
        return None

def call_llm_api(client: Any, model_family: str, model_name: str, prompt: str) -> tuple[Any | None, bool]:
    """Calls the appropriate LLM API based on the client/model family."""
    raw_response = None
    success = False

    try:
        if model_family.lower() == 'gemini':
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            raw_response = response
            success = True
        elif model_family.lower() == 'mistral':
            messages = [{"role": "user", "content": prompt}]
            response = client.chat.complete(
                model=model_name,
                messages=messages
            )
            raw_response = response
            success = True
        else:
            # Error handled by returning initial values (None, False)
            pass
    except Exception:
        # Error handled by returning initial values (None, False)
        pass 

    return raw_response, success
