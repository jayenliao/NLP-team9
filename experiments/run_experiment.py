# experiments/run_experiment.py
import logging
import sys
import os
import argparse
import json
import time
import itertools
from tqdm import tqdm
from collections import deque # For circular shifts

# Assuming core_runner and utils are in the same directory or PYTHONPATH is set
from core_runner import (
    load_prompt_template, format_prompt, parse_response,
    structure_result, get_api_client, call_llm_api
)
from utils import load_prepared_dataset, load_api_keys

# Logging Setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Default INFO

# Construct paths relative to this script's file location
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir) # Assumes 'experiments' is one level down from project root

log_file_path = os.path.join(project_root, 'logs', 'experiment.log')
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

# Prevent duplicate handlers if script is re-run (e.g., in some IDEs or notebooks)
if not logger.handlers:
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setLevel(logging.INFO)
    f_handler = logging.FileHandler(log_file_path)
    f_handler.setLevel(logging.INFO)

    log_format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format_str = '%Y-%m-%d %H:%M:%S'
    log_formatter = logging.Formatter(log_format_str, datefmt=date_format_str)

    c_handler.setFormatter(log_formatter)
    f_handler.setFormatter(log_formatter)

    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

def generate_circular_permutations(original_labels: list[str]) -> list[list[str]]:
    """
    Generates 4 circular shift permutations for the content mapping.
    The `original_labels` are the semantic labels ('A', 'B', 'C', 'D').
    The output lists define which original choice content maps to the displayed A, B, C, D.

    Example: For original_labels = ['A', 'B', 'C', 'D']
    Yields permutations for `option_order` in `format_prompt`:
        1. ['A', 'B', 'C', 'D']  (Displayed A=Orig A, Disp B=Orig B, etc.)
        2. ['D', 'A', 'B', 'C']  (Displayed A=Orig D, Disp B=Orig A, etc.) - Content shifts right
        3. ['C', 'D', 'A', 'B']  (Displayed A=Orig C, Disp B=Orig D, etc.)
        4. ['B', 'C', 'D', 'A']  (Displayed A=Orig B, Disp B=Orig C, etc.)
    """
    if not original_labels or len(original_labels) != 4:
        logger.error("Original labels must be a list of 4 elements for circular shift.")
        return []

    permutations = []
    # items_to_place_at_displayed_positions represents the original semantic labels
    # whose content will be placed at the displayed positions A, B, C, D.
    items_to_place_at_displayed_positions = deque(original_labels)

    for _ in range(len(original_labels)):
        # The current state of 'items_to_place_at_displayed_positions' IS the permutation list
        # that format_prompt needs for its `option_order` argument.
        permutations.append(list(items_to_place_at_displayed_positions))
        # Rotate the deque: the last item moves to the first position.
        # This means the content that *was* at original D now maps to displayed A,
        # content at original A maps to displayed B, and so on.
        items_to_place_at_displayed_positions.rotate(1)
    return permutations


def main():
    parser = argparse.ArgumentParser(description="Run LLM evaluation experiments for order sensitivity.")
    parser.add_argument("--model_family", type=str, required=True, choices=['gemini', 'mistral'], help="LLM family ('gemini' or 'mistral').")
    parser.add_argument("--model_name", type=str, required=True, help="Specific model name (e.g., 'gemini-1.5-flash-latest', 'mistral-small-latest').")
    parser.add_argument("--language", type=str, default='en', choices=['en', 'fr'], help="Language code ('en' or 'fr').")
    parser.add_argument("--prompt_format", type=str, default='base', choices=['base', 'json', 'xml'], help="Prompt format ('base', 'json', 'xml'). This corresponds to 'style' in format_prompt.")
    parser.add_argument("--subtasks", type=str, default='all', help="Comma-separated list of subtasks, or 'all'.")
    parser.add_argument("--num_questions", type=int, default=100, help="Number of questions per subtask to process from the start_index.")
    
    parser.add_argument('--permutation_type', type=str, default='factorial', choices=['factorial', 'circular'],
                        help='Type of permutation generation: "factorial" for all permutations up to num_factorial_permutations, "circular" for 4 circular shifts.')
    parser.add_argument('--num_factorial_permutations', type=int, default=24,
                        help='Number of permutations to run if permutation_type is "factorial" (default: 24, max: 24). Ignored if type is "circular".')

    parser.add_argument("--start_index", type=int, default=0, help="0-based index of the first question within each subtask's language data.")
    parser.add_argument("--output_dir", type=str, default='results_output', help="Subdirectory within the project's 'results' folder to save results files.") # Clarified name
    parser.add_argument("--output_file", type=str, default=None, help="Specific name for the output JSONL file. If None, a name is generated.")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay in seconds between API calls.")

    args = parser.parse_args()
    logger.info(f"Starting experiment with arguments: {args}")

    # Initialize
    logger.info("Initializing API keys and client...")
    # load_api_keys() from utils.py loads them into environment variables if using python-dotenv
    # It doesn't need to return them if get_api_client handles fetching from os.getenv()
    load_api_keys() 
    client = get_api_client(args.model_family)
    if not client:
        logger.critical(f"Fatal: Failed to initialize API client for {args.model_family}.")
        return

    logger.info("Loading prepared dataset...")
    full_dataset = load_prepared_dataset() # Expects ds_selected.pkl in project_root/data/
    if not full_dataset:
        logger.critical("Fatal: Failed to load prepared dataset (expected ds_selected.pkl).")
        return

    logger.info(f"Loading prompt file for format: {args.prompt_format}_prompt.txt (Note: actual template used by format_prompt might depend on 'style' argument)")
    template_content_from_file = load_prompt_template(args.prompt_format) # args.prompt_format is 'base', 'json', or 'xml'
    if not template_content_from_file:
        logger.warning(f"Warning: Failed to load prompt template file for '{args.prompt_format}_prompt.txt'. "
                       "The experiment will proceed if format_prompt uses internally defined templates based on the 'style' (prompt_format argument).")

    # Determine Subtasks
    if args.subtasks.lower() == 'all':
        subtasks_to_run = list(full_dataset.keys())
    else:
        requested_subtasks = [st.strip() for st in args.subtasks.split(',')]
        subtasks_to_run = [st for st in requested_subtasks if st in full_dataset]
        if not subtasks_to_run:
            logger.critical(f"Fatal: No valid subtasks found from '{args.subtasks}' in the loaded dataset.")
            return
    logger.info(f"Will run experiment for subtasks: {subtasks_to_run}")

    # Prepare Output File Path
    if args.output_file is None:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{args.model_family}_{args.model_name}_{args.language}_{args.prompt_format}_{args.permutation_type}_{timestamp}.jsonl"
    else:
        filename = args.output_file if args.output_file.endswith(".jsonl") else f"{args.output_file}.jsonl"

    # Ensure output directory is within project_root/results/
    results_base_dir = os.path.join(project_root, "results")
    output_path_dir = os.path.join(results_base_dir, args.output_dir)
    os.makedirs(output_path_dir, exist_ok=True)
    output_path = os.path.join(output_path_dir, filename)
    logger.info(f"Results will be saved to: {output_path}")

    # Experiment Loop
    logger.info("Starting main experiment loop...")
    total_api_calls_attempted = 0
    try:
        with open(output_path, 'a', encoding='utf-8') as f_out:
            for subtask in tqdm(subtasks_to_run, desc="Overall Subtasks Progress"):
                logger.info(f"--- Processing Subtask: {subtask} ---")

                if subtask not in full_dataset or args.language not in full_dataset[subtask]:
                    logger.warning(f"Data for subtask '{subtask}' or language '{args.language}' not found. Skipping subtask.")
                    continue

                task_data = full_dataset[subtask][args.language] # List of question dicts

                # Determine the actual number of questions to process for this subtask
                if args.start_index >= len(task_data):
                    logger.info(f"Start index {args.start_index} is out of bounds for subtask {subtask} (length {len(task_data)}). Skipping subtask.")
                    continue
                
                # Calculate number of questions to process, ensuring it doesn't exceed available data
                num_questions_to_process = min(args.num_questions, len(task_data) - args.start_index)
                
                if num_questions_to_process <= 0:
                    logger.info(f"No questions to process for subtask {subtask} with start_index {args.start_index} and num_questions {args.num_questions}. Skipping subtask.")
                    continue

                actual_end_index = args.start_index + num_questions_to_process
                logger.info(f"For subtask '{subtask}', processing questions from index {args.start_index} to {actual_end_index - 1}")
                
                question_indices_to_process = range(args.start_index, actual_end_index)

                for i in tqdm(question_indices_to_process, desc=f"  Questions in {subtask}", leave=False):
                    data_item = task_data[i] # This is the standardized question dict
                    
                    logger.debug(f"Processing {subtask} - {args.language} - Dataset Question Index: {i} (ID: {data_item.get('id', 'N/A')})")

                    original_labels = ['A', 'B', 'C', 'D'] # Semantic labels for original choice order
                    permutations_to_iterate: list[list[str]] = [] # This will hold the `option_order` lists
                    
                    if args.permutation_type == 'circular':
                        permutations_to_iterate = generate_circular_permutations(original_labels)
                        logger.debug(f"Generated {len(permutations_to_iterate)} circular permutations for Q_idx:{i}")
                    elif args.permutation_type == 'factorial':
                        num_perms_to_run_factorial = min(args.num_factorial_permutations, 24)
                        if args.num_factorial_permutations > 24:
                            logger.warning(f"--num_factorial_permutations requested {args.num_factorial_permutations}, using 24.")
                        
                        perm_gen = itertools.islice(itertools.permutations(original_labels), num_perms_to_run_factorial)
                        permutations_to_iterate = [list(p) for p in perm_gen]
                        logger.debug(f"Generated {len(permutations_to_iterate)} factorial permutations for Q_idx:{i}")
                    else:
                        logger.error(f"Unknown permutation type: {args.permutation_type}. This should not happen due to argparse choices. Skipping question.")
                        continue

                    if not permutations_to_iterate:
                        logger.warning(f"No permutations were generated for Q_idx:{i} with strategy {args.permutation_type}. Skipping question.")
                        continue
                        
                    total_permutations_for_this_question = len(permutations_to_iterate)

                    for p_idx, current_option_order in enumerate(permutations_to_iterate):
                        perm_string = "".join(current_option_order)
                        logger.info(f"    Q_idx:{i}, Permutation {p_idx + 1}/{total_permutations_for_this_question} (Order: {perm_string})")
                        
                        current_prompt = format_prompt(
                            template_content_from_file, # May be unused if style dictates template
                            data_item,
                            current_option_order, # This is the key list for remapping choices
                            args.language,
                            args.prompt_format # This is the 'style' for format_multichoice_question
                        )
                        if not current_prompt:
                            logger.warning(f"Failed to format prompt for Q_idx:{i}, Perm:{perm_string}. Skipping this trial.")
                            continue
                        
                        api_response, api_ok = call_llm_api(client, args.model_family, args.model_name, current_prompt)
                        total_api_calls_attempted += 1
                        
                        if not api_ok:
                            logger.warning(f"API call failed for Q_idx:{i}, Perm:{perm_string}. Raw response will be logged if available.")

                        parsed_answer = None # Positional answer (A/B/C/D) relative to the permuted prompt
                        if api_ok and api_response:
                            response_text = None
                            try:
                                if args.model_family == 'gemini':
                                    if hasattr(api_response, 'text'): # Simplest case
                                        response_text = api_response.text
                                    elif api_response.parts: # Common structure
                                        response_text = "".join(part.text for part in api_response.parts if hasattr(part, 'text'))
                                    elif api_response.candidates and api_response.candidates[0].content and api_response.candidates[0].content.parts:
                                        response_text = api_response.candidates[0].content.parts[0].text
                                elif args.model_family == 'mistral':
                                    if api_response.choices:
                                        response_text = api_response.choices[0].message.content
                            except AttributeError as e_attr:
                                logger.warning(f"Attribute error accessing response text for Q_idx:{i}, Perm:{perm_string}. Error: {e_attr}. Response: {str(api_response)[:200]}")
                            except Exception as e_parse_resp:
                                logger.error(f"Unexpected error accessing response text for Q_idx:{i}, Perm:{perm_string}: {e_parse_resp}", exc_info=True)
                            
                            if response_text:
                                parsed_answer = parse_response(response_text)
                                if parsed_answer:
                                    logger.info(f"    Parsed LLM choice: '{parsed_answer}' (for permuted prompt)")
                                else:
                                    logger.warning(f"    Failed to parse LLM choice from text: {response_text[:100]}...")
                            else:
                                logger.warning(f"    No response text extracted from successful API call for Q_idx:{i}, Perm:{perm_string}")
                        
                        result_dict = structure_result(
                            data_item=data_item,
                            subtask=subtask,
                            language=args.language,
                            model_name=args.model_name,
                            input_format=args.prompt_format,
                            option_permutation=current_option_order, # The list like ['D', 'A', 'B', 'C']
                            api_raw_response=str(api_response) if api_response is not None else None,
                            api_call_successful=api_ok,
                            extracted_answer=parsed_answer, # e.g., 'A', 'B', 'C', or 'D'
                            log_probabilities=None,
                            question_index=i # Absolute index from the dataset for this subtask/language
                        )

                        try:
                            json_string = json.dumps(result_dict, ensure_ascii=False)
                            f_out.write(json_string + '\n')
                            f_out.flush() # Ensure data is written to disk
                        except Exception as e_write:
                            logger.error(f"Failed to write result for Q_idx:{i}, Perm:{perm_string}: {e_write}", exc_info=True)

                        if args.delay > 0:
                            logger.debug(f"Delaying for {args.delay} seconds...")
                            time.sleep(args.delay)
                
                logger.info(f"Finished processing all selected questions for subtask: {subtask}")

    except KeyboardInterrupt:
        logger.warning("Experiment interrupted by user (KeyboardInterrupt). Partial results may have been saved.")
    except Exception as e_main:
        logger.critical(f"A critical error occurred during the experiment: {e_main}", exc_info=True)
    finally:
        logger.info(f"Experiment run finished or terminated. Total API calls attempted: {total_api_calls_attempted}")
        
        # Log the output directory for tracking purposes, as in original script
        # Ensure this log path is robust
        logs_for_filter_dir = os.path.join(project_root, "results", "__logs__")
        os.makedirs(logs_for_filter_dir, exist_ok=True)
        to_fix_log_path = os.path.join(logs_for_filter_dir, '0-to-Filter-Runs.log')

        try:
            with open(to_fix_log_path, 'a', encoding='utf-8') as f_log_filter:
                f_log_filter.write(f"Run completed at {time.strftime('%Y-%m-%d %H:%M:%S')}: Output directory '{output_path_dir}', File '{filename}'\n")
        except Exception as e_log_write:
            logger.error(f"Failed to write to '{to_fix_log_path}': {e_log_write}")

if __name__ == "__main__":
    main()

"""
    --- Example: To run circular permutations ---
    python experiments/run_experiment.py \
    --model_family gemini \
    --model_name gemini-1.5-flash-latest \
    --language en \
    --prompt_format base \
    --subtasks abstract_algebra \
    --num_questions 2 \
    --permutation_type circular \
    --delay 2
    
    --- Example: To run factorial permutations ---
    python experiments/run_experiment.py \
    --model_family mistral \
    --model_name mistral-small-latest \
    --language fr \
    --prompt_format xml \
    --subtasks anatomy \
    --num_questions 1 \
    --permutation_type factorial \
    --num_factorial_permutations 5 \
    --delay 2
    """
