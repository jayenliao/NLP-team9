# experiments/core_runner.py
import os
import re
import uuid
from typing import Any
from google import genai as google_genai
from mistralai import Mistral
from utils import load_api_keys, format_multichoice_question
import json
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

def format_prompt(data_item: dict, option_order: list[str], lang: str, in_style: str, out_style: str) -> str | None:
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
    handling multilingual prefixes for "Answer:" and multiple output formats.

    Args:
        api_response_text: The raw text output from the LLM.

    Returns:
        The normalized extracted answer ('A', 'B', 'C', 'D') or None if parsing fails.
    """
    
    if not api_response_text or not isinstance(api_response_text, str):
        return None
    
    # Step 1: Try to extract from JSON code block
    json_block_pattern = r"```json\s*(\{.*?\})\s*```"
    json_block_match = re.search(json_block_pattern, api_response_text, re.DOTALL | re.IGNORECASE)
    
    if json_block_match:
        json_text = json_block_match.group(1)
        try:
            json_obj = json.loads(json_text)
            # Check various possible key names
            answer = json_obj.get("answer", json_obj.get("Answer", json_obj.get("ANSWER")))
            if answer and str(answer).upper() in ["A", "B", "C", "D"]:
                return str(answer).upper()
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON block: {e}")
    
    # Step 2: Try to extract from XML code block
    xml_block_pattern = r"```xml\s*(.*?)\s*```"
    xml_block_match = re.search(xml_block_pattern, api_response_text, re.DOTALL | re.IGNORECASE)
    
    if xml_block_match:
        xml_text = xml_block_match.group(1)
        answer_match = re.search(r"<answer>\s*([A-D])\s*</answer>", xml_text, re.IGNORECASE)
        if answer_match:
            return answer_match.group(1).upper()
    
    # Step 3: Try to parse raw JSON (not in code block)
    json_patterns = [
        r'\{[^{}]*["\']answer["\']\s*:\s*["\']([A-D])["\'][^{}]*\}',
        r'"answer"\s*:\s*"([A-D])"',
    ]
    
    for pattern in json_patterns:
        match = re.search(pattern, api_response_text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
    
    # Step 4: Try to parse raw XML (not in code block)
    xml_answer_pattern = r"<answer>\s*([A-D])\s*</answer>"
    xml_match = re.search(xml_answer_pattern, api_response_text, re.IGNORECASE)
    
    if xml_match:
        return xml_match.group(1).upper()
    
    # Step 5: Fall back to original plain text parsing
    ANSWER_PREFIXES = [
        r"Answer\s*:",         # English
        r"Réponse\s*:",        # French
    ]
    COMBINED_ANSWER_PREFIX_REGEX = r"(?:" + "|".join(ANSWER_PREFIXES) + r")"
    
    # Enhanced pattern with better quote handling
    QUOTE_CHARS = r"""[«»\"''"'"'„"〈〉【】〔〕‹›❝❞❮❯⟨⟩]"""
    pattern = rf"^\s*[*\#_]*\s*{QUOTE_CHARS}?\s*{COMBINED_ANSWER_PREFIX_REGEX}\s*{QUOTE_CHARS}?\s*:?\s*[*\#_$]*\s*([A-D])\s*{QUOTE_CHARS}?"
    match = re.search(pattern, api_response_text, re.IGNORECASE | re.MULTILINE)
    
    if match:
        return match.group(1).upper()
    
    # Step 6: Try more lenient patterns
    lenient_patterns = [
        rf"{COMBINED_ANSWER_PREFIX_REGEX}.*?([A-D])\b",  # Answer anywhere after prefix
        r"^\s*\(?([A-D])\)?\s*$",  # Just (A) or A alone on a line
        r"\b([A-D])\b\s*$",  # Letter at the end
    ]
    
    for pattern in lenient_patterns:
        match = re.search(pattern, api_response_text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).upper()
    
    return None


def structure_result(
    data_item: dict,
    subtask: str,
    language: str,
    model_name: str,
    input_format: str,
    output_format: str,
    option_permutation: list[str], # e.g., ['C', 'A', 'D', 'B']
    api_raw_response: Any | None,
    api_call_successful: bool,
    extracted_answer: str | None, # e.g., 'B' (the positional answer chosen)
    log_probabilities: dict | None = None, # We'll keep this None as requested
    question_index: int = -1,
    api_response_text: str | None = None
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
        "output_format": output_format,
        "option_permutation": "".join(option_permutation), # Save the permutation used
        "api_call_successful": api_call_successful,
        "extracted_answer": extracted_answer, # The positional answer (A/B/C/D relative to permutation)
        "model_choice_original_label": model_choice_original_label, # **The added field** (Original A/B/C/D based on content)
        "log_probabilities": log_probabilities, # Keeping as None
        "ground_truth_answer": ground_truth_label, # The original correct label ('A'/'B'/'C'/'D')
        "is_correct": is_correct, # Boolean or None
        "api_response_text": api_response_text, # Raw text from the API
        "api_raw_response": str(api_raw_response) if api_raw_response is not None else None,
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
