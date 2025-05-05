# experiments/core_runner.py
import os
import re
import uuid
from typing import Any
from google import genai as google_genai
from mistralai import Mistral
from utils import load_api_keys 

import logging
logger = logging.getLogger(__name__)

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

# --- Define Answer Prefixes  ---
# Based on simple-evals MULTILINGUAL_ANSWER_REGEXES
# only English and French for now
ANSWER_PREFIXES = [
    r"Answer\s*:",         # English
    r"Réponse\s*:",        # French
    # Add other relevant prefixes from simple-evals list if you add more languages
]
# Combine prefixes into a non-capturing group using '|' (OR)
COMBINED_ANSWER_PREFIX_REGEX = r"(?:" + "|".join(ANSWER_PREFIXES) + r")"

def parse_response(api_response_text: str) -> str | None:
    """
    Parses the API response text to extract the answer choice (A, B, C, or D),
    handling multilingual prefixes for "Answer:".

    Looks for a line starting with known 'Answer:' equivalents followed by A, B, C, or D.
    It tries to be flexible regarding whitespace and case.

    Args:
        api_response_text: The raw text output from the LLM.

    Returns:
        The normalized extracted answer ('A', 'B', 'C', 'D') or None if parsing fails.
    """
    
    # Regex Reference:
    # ^                 - Start of a line (due to re.MULTILINE)
    # \s* - Optional leading whitespace
    # (?:...)           - Non-capturing group for the OR condition of prefixes
    #   Answer\s*:      - English prefix
    #   |               - OR
    #   Réponse\s*:     - French prefix
    # \s* - Optional whitespace after the prefix/colon
    # ([A-D])           - Capturing group 1: Exactly one character that is A, B, C, or D
    #                     (We assume the model follows instructions to use A-D)
    # \s* - Optional trailing whitespace
    # $                 - End of the line (due to re.MULTILINE)
    # We use COMBINED_ANSWER_PREFIX_REGEX which expands to (?:Answer\s*:|Réponse\s*:)
    
    # pattern = rf"^\s*{COMBINED_ANSWER_PREFIX_REGEX}\s*([A-D])\s*$" #from common.py, but too strict

    pattern = rf"^\s*{COMBINED_ANSWER_PREFIX_REGEX}\s*([A-D])"
    match = re.search(pattern, api_response_text, re.IGNORECASE | re.MULTILINE)

    if match:
        extracted_raw = match.group(1) # Get the captured group (the letter A-D)
        normalized_answer = extracted_raw
        return normalized_answer
    
    # If want to add more languages like Japanese use this
    #     # Normalize the extracted letter (e.g., to uppercase, handle potential future non-Latin chars)
    #     normalized_answer = normalize_extracted_answer(extracted_raw)
    #     if normalized_answer in ['A', 'B', 'C', 'D']:
    #          logger.info(f"Successfully parsed and normalized answer: {normalized_answer}")
    #          return normalized_answer
    #     else:
    #          logger.warning(f"Pattern matched but normalization resulted in unexpected value: '{normalized_answer}' from raw '{extracted_raw}'.")
    #          return None # Or handle as needed
    # else:
    #     logger.warning(f"Parsing response failed: Could not find pattern matching known prefixes and [A-D].")
    #     return None

# # --- normalize_extracted_answer function in case want to add japanese (from simple-evals) ---
# def normalize_extracted_answer(extracted_answer: str) -> str:
#     """
#     Normalizes the extracted answer string.
#     For now, mainly handles potential non-Latin chars if the regex were broader,
#     and standardizes to uppercase Latin A-D, stripping whitespace.
#     (Adapted from simple-evals common.py)
#     """

#     # Basic normalization: uppercase and strip whitespace
#     normalized = extracted_answer.upper().strip()

#     # Add specific character replacements if the regex were capturing non-Latin chars
#     # (Based on simple-evals: Arabic, Bengali, Japanese Full-width)
#     replacements = {
#         "أ": "A", "ب": "B", "ج": "C", "د": "D", # Arabic
#         "অ": "A", "ব": "B", "ড": "C", "ঢ": "D", # Bengali
#         "Ａ": "A", "Ｂ": "B", "Ｃ": "C", "Ｄ": "D", # Japanese Full-width
#     }

#     for original, replacement in replacements.items():
#         normalized = normalized.replace(original, replacement)

#     # Return the final standardized character, stripped of any extra space added during replacement
#     return normalized.strip()


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
    """
    Structures the results of a single experiment trial into a dictionary.
    (Simplified version using standardized data_item keys from updated save_datsets.py)
    """
    logger.debug("Structuring result (using standardized keys).")

    # --- Determine Ground Truth (Simplified) ---
    ground_truth_label = "UNKNOWN"
    is_correct = None
    try:
        # Assumes 'answer_label' key ('A'/'B'/'C'/'D') exists due to standardization
        if 'answer_label' in data_item:
             ground_truth_label = data_item['answer_label']
        else:
             logger.warning(f"Standardized key 'answer_label' not found in data_item! Keys: {list(data_item.keys())}")

        if extracted_answer is not None and ground_truth_label != "UNKNOWN":
            is_correct = (extracted_answer == ground_truth_label)

    except Exception as e:
        logger.error(f"Error determining ground truth or correctness: {e}", exc_info=True)
        ground_truth_label = "ERROR"
        is_correct = None

    # --- Determine Question ID (Simplified) ---
    # Use 'id' key exists from standardization
    q_id = data_item.get('id', f"idx_{question_index}") # Use .get just in case, fallback to index

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
    logger.debug(f"Result structured: {result}")
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
            pass
    except Exception:
        pass 

    return raw_response, success
