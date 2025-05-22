# experiments/core_runner.py
import os
import re
import uuid
from typing import Any
from google import genai as google_genai
from mistralai import Mistral
from utils import load_api_keys, format_multichoice_question

import logging
logger = logging.getLogger(__name__)

# def load_prompt_templat(format_name: str) -> str | None:
#     """Loads the content of a prompt template file."""
#     template_dir = os.path.join(os.path.dirname(__file__), '..', 'prompts')
#     template_filename = f"{format_name}_prompt.txt"
#     template_path = os.path.join(template_dir, template_filename)
#     try:
#         with open(template_path, 'r', encoding='utf-8') as f:
#             return f.read()
#     except Exception: 
#         return None

def format_prompt(data_item: dict, option_order: list[str], lang: str, in_style: str, out_style) -> str | None:
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
        # return template_content.format(**format_context)
        return format_multichoice_question(format_context, in_style=in_style, out_style=out_style, lang=lang)
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

    # pattern = rf"^\s*{COMBINED_ANSWER_PREFIX_REGEX}\s*([A-D])"
    pattern = rf"^\s*(?:[*\#_]*)?\s*{COMBINED_ANSWER_PREFIX_REGEX}\s*([A-D])" #Added regex for bold answers
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
    option_permutation: list[str], # e.g., ['C', 'A', 'D', 'B']
    api_raw_response: Any | None,
    api_call_successful: bool,
    extracted_answer: str | None, # e.g., 'B' (the positional answer chosen)
    log_probabilities: dict | None = None, # We'll keep this None as requested
    question_index: int = -1
) -> dict:
    """
    Structures the results of a single experiment trial into a dictionary.
    Calculates the original label corresponding to the model's choice
    based on the permutation.
    """
    logger.debug("Structuring result...")

    ground_truth_label = "UNKNOWN"
    model_choice_original_label = None
    is_correct = None

    # 1. Determine Ground Truth from the standardized data
    try:
        # Assumes 'answer_label' key ('A'/'B'/'C'/'D') exists due to standardization
        if 'answer_label' in data_item:
             ground_truth_label = data_item['answer_label']
             logger.debug(f"Ground truth label: {ground_truth_label}")
        else:
             logger.warning(f"Standardized key 'answer_label' not found in data_item! Keys: {list(data_item.keys())}. Cannot determine ground truth.")

    except Exception as e:
        logger.error(f"Error determining ground truth: {e}", exc_info=True)
        ground_truth_label = "ERROR_GT" # Use a distinct value for errors

    # 2. Determine the Original Label of the Model's Choice based on permutation
    if api_call_successful and extracted_answer in ['A', 'B', 'C', 'D']:
        try:
            # Find the 0-based index corresponding to the extracted positional answer
            # 'A' -> 0, 'B' -> 1, 'C' -> 2, 'D' -> 3
            choice_index = ord(extracted_answer.upper()) - ord('A')

            # Use this index to find the original label from the permutation list
            if 0 <= choice_index < len(option_permutation):
                model_choice_original_label = option_permutation[choice_index]
                logger.debug(f"Extracted answer (positional): '{extracted_answer}', "
                             f"Permutation: {option_permutation}, "
                             f"Calculated original label: '{model_choice_original_label}'")
            else:
                 logger.warning(f"Extracted answer '{extracted_answer}' resulted in an invalid index {choice_index} "
                                f"for permutation {option_permutation}. Cannot determine original label.")
                 model_choice_original_label = "ERROR_MAP" # Indicate mapping error

        except Exception as e:
            logger.error(f"Error mapping extracted answer to original label: {e}", exc_info=True)
            model_choice_original_label = "ERROR_MAP"
    elif api_call_successful and extracted_answer is not None:
         logger.warning(f"Extracted answer '{extracted_answer}' is not A, B, C, or D. Cannot determine original label.")
         model_choice_original_label = "INVALID_EXT" # Indicate invalid extraction
    elif not api_call_successful:
        logger.debug("API call failed or no response, cannot determine model choice.")
        model_choice_original_label = None # Explicitly None if API failed
    else: # Extracted answer was None even if API call successful
         logger.debug("API call successful but no answer extracted, cannot determine model choice.")
         model_choice_original_label = None


    # 3. Determine Correctness by comparing ORIGINAL labels
    if model_choice_original_label and model_choice_original_label not in ["ERROR_MAP", "INVALID_EXT"] and \
       ground_truth_label != "UNKNOWN" and ground_truth_label != "ERROR_GT":
        try:
            is_correct = (model_choice_original_label == ground_truth_label)
            logger.debug(f"Comparing model original '{model_choice_original_label}' with ground truth '{ground_truth_label}'. Correct: {is_correct}")
        except Exception as e:
             logger.error(f"Error comparing labels for correctness: {e}", exc_info=True)
             is_correct = None # Error during comparison
    else:
        logger.debug("Cannot determine correctness (missing model choice, ground truth, or error occurred).")
        is_correct = None # Cannot determine correctness

    # 4. Determine Question ID
    q_id = data_item.get('id', f"idx_{question_index}") # Use .get just in case, fallback to index

    # 5. Assemble the final result dictionary
    result = {
        "trial_id": str(uuid.uuid4()), # Keep unique ID for each trial (permutation)
        "question_id": q_id,
        "question_index": question_index, # Index within the dataset slice being run
        "subtask": subtask,
        "language": language,
        "model_name": model_name,
        "input_format": input_format,
        "option_permutation": "".join(option_permutation), # Save the permutation used
        "api_call_successful": api_call_successful,
        "api_raw_response": str(api_raw_response) if api_raw_response is not None else None,
        "extracted_answer": extracted_answer, # The positional answer (A/B/C/D relative to permutation)
        "model_choice_original_label": model_choice_original_label, # **The added field** (Original A/B/C/D based on content)
        "log_probabilities": log_probabilities, # Keeping as None
        "ground_truth_answer": ground_truth_label, # The original correct label ('A'/'B'/'C'/'D')
        "is_correct": is_correct # Boolean or None
    }
    logger.info(f"Result structured for q_idx {question_index}, perm {''.join(option_permutation)}: "
                f"Extracted='{extracted_answer}', Orig='{model_choice_original_label}', GT='{ground_truth_label}', Correct={is_correct}")
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
