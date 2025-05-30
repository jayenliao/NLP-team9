# experiments/run_experiment.py
"""
Updated run_experiment.py that uses the refactored components
while maintaining backward compatibility.
"""
import logging
import sys
import os
import argparse
import json
import time
from tqdm import tqdm

# Import new refactored components
from core_runner_refactored import ExperimentRunner
from permutations import PermutationGenerator
from utils import load_prepared_dataset, load_api_keys

# Logging setup (kept exactly the same)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

log_file_path = os.path.join(project_root, 'logs', 'experiment.log')
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

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


def main():
    # Parse arguments (kept exactly the same)
    parser = argparse.ArgumentParser(description="Run LLM evaluation experiments for order sensitivity.")
    parser.add_argument("--model_family", type=str, required=True, choices=['gemini', 'mistral'], 
                       help="LLM family ('gemini' or 'mistral').")
    parser.add_argument("--model_name", type=str, required=True, 
                       help="Specific model name (e.g., 'gemini-1.5-flash-latest', 'mistral-small-latest').")
    parser.add_argument("--language", type=str, default='en', choices=['en', 'fr'], 
                       help="Language code ('en' or 'fr').")
    parser.add_argument("--prompt_format", type=str, default='base', choices=['base', 'json', 'xml'], 
                       help="Prompt format ('base', 'json', 'xml'). This corresponds to 'style' in format_prompt.")
    parser.add_argument("--output_format", type=str, default='base', choices=['base', 'json', 'xml'], 
                       help="Prompt format ('base', 'json', 'xml'). This corresponds to 'style' in format_prompt.")
    parser.add_argument("--subtasks", type=str, default='all', 
                       help="Comma-separated list of subtasks, or 'all'.")
    parser.add_argument("--num_questions", type=int, default=100, 
                       help="Number of questions per subtask to process from the start_index.")
    parser.add_argument('--permutation_type', type=str, default='factorial', choices=['factorial', 'circular'],
                       help='Type of permutation generation: "factorial" for all permutations up to num_factorial_permutations, "circular" for 4 circular shifts.')
    parser.add_argument('--num_factorial_permutations', type=int, default=24,
                       help='Number of permutations to run if permutation_type is "factorial" (default: 24, max: 24). Ignored if type is "circular".')
    parser.add_argument("--start_index", type=int, default=0, 
                       help="0-based index of the first question within each subtask's language data.")
    parser.add_argument("--output_dir", type=str, default='results_output', 
                       help="Subdirectory within the project's 'results' folder to save results files.")
    parser.add_argument("--output_file", type=str, default=None, 
                       help="Specific name for the output JSONL file. If None, a name is generated.")
    parser.add_argument("--delay", type=float, default=1.0, 
                       help="Delay in seconds between API calls.")

    args = parser.parse_args()
    logger.info(f"Starting experiment with arguments: {args}")

    # Initialize with new components
    logger.info("Initializing API keys and experiment runner...")
    load_api_keys()
    
    try:
        runner = ExperimentRunner(args.model_family)
    except ValueError as e:
        logger.critical(f"Fatal: {e}")
        return

    # Load dataset (kept the same)
    logger.info("Loading prepared dataset...")
    full_dataset = load_prepared_dataset()
    if not full_dataset:
        logger.critical("Fatal: Failed to load prepared dataset (expected ds_selected.pkl).")
        return

    # Determine subtasks (kept the same)
    if args.subtasks.lower() == 'all':
        subtasks_to_run = list(full_dataset.keys())
    else:
        requested_subtasks = [st.strip() for st in args.subtasks.split(',')]
        subtasks_to_run = [st for st in requested_subtasks if st in full_dataset]
        if not subtasks_to_run:
            logger.critical(f"Fatal: No valid subtasks found from '{args.subtasks}' in the loaded dataset.")
            return
    logger.info(f"Will run experiment for subtasks: {subtasks_to_run}")

    # Prepare output file (kept the same)
    if args.output_file is None:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{args.model_family}_{args.model_name}_{args.language}_i-{args.prompt_format}_o-{args.output_format}_{args.permutation_type}_{timestamp}.jsonl"
    else:
        filename = args.output_file if args.output_file.endswith(".jsonl") else f"{args.output_file}.jsonl"

    results_base_dir = os.path.join(project_root, "results")
    output_path_dir = os.path.join(results_base_dir, args.output_dir)
    os.makedirs(output_path_dir, exist_ok=True)
    output_path = os.path.join(output_path_dir, filename)
    logger.info(f"Results will be saved to: {output_path}")

    # Create permutation generator
    perm_generator = PermutationGenerator()

    # Main experiment loop (refactored to use new components)
    logger.info("Starting main experiment loop...")
    total_api_calls_attempted = 0
    
    try:
        with open(output_path, 'a', encoding='utf-8') as f_out:
            for subtask in tqdm(subtasks_to_run, desc="Overall Subtasks Progress"):
                logger.info(f"--- Processing Subtask: {subtask} ---")

                if subtask not in full_dataset or args.language not in full_dataset[subtask]:
                    logger.warning(f"Data for subtask '{subtask}' or language '{args.language}' not found. Skipping subtask.")
                    continue

                task_data = full_dataset[subtask][args.language]

                # Determine questions to process (kept the same)
                if args.start_index >= len(task_data):
                    logger.info(f"Start index {args.start_index} is out of bounds for subtask {subtask} (length {len(task_data)}). Skipping subtask.")
                    continue
                
                num_questions_to_process = min(args.num_questions, len(task_data) - args.start_index)
                
                if num_questions_to_process <= 0:
                    logger.info(f"No questions to process for subtask {subtask} with start_index {args.start_index} and num_questions {args.num_questions}. Skipping subtask.")
                    continue

                actual_end_index = args.start_index + num_questions_to_process
                logger.info(f"For subtask '{subtask}', processing questions from index {args.start_index} to {actual_end_index - 1}")
                
                question_indices_to_process = range(args.start_index, actual_end_index)

                for i in tqdm(question_indices_to_process, desc=f"  Questions in {subtask}", leave=False):
                    data_item = task_data[i]
                    
                    logger.debug(f"Processing {subtask} - {args.language} - Dataset Question Index: {i} (ID: {data_item.get('id', 'N/A')})")

                    # Generate permutations using new component
                    try:
                        permutations = perm_generator.generate(
                            permutation_type=args.permutation_type,
                            num_factorial=args.num_factorial_permutations
                        )
                    except ValueError as e:
                        logger.error(f"Error generating permutations: {e}")
                        continue

                    if not permutations:
                        logger.warning(f"No permutations were generated for Q_idx:{i}. Skipping question.")
                        continue
                    
                    total_permutations = len(permutations)
                    logger.debug(f"Generated {total_permutations} {args.permutation_type} permutations for Q_idx:{i}")

                    for p_idx, option_order in enumerate(permutations):
                        perm_string = "".join(option_order)
                        logger.info(f"    Q_idx:{i}, Permutation {p_idx + 1}/{total_permutations} (Order: {perm_string})")
                        
                        # Run single trial using new runner
                        result_dict = runner.run_single_trial(
                            data_item=data_item,
                            option_order=option_order,
                            language=args.language,
                            model_name=args.model_name,
                            input_format=args.prompt_format,  # Maps to input_format in new system
                            output_format=args.output_format,
                            subtask=subtask,
                            question_index=i
                        )
                        
                        total_api_calls_attempted += 1
                        
                        # Log extracted answer if successful
                        if result_dict['api_call_successful'] and result_dict['extracted_answer']:
                            logger.info(f"    Parsed LLM choice: '{result_dict['extracted_answer']}' (for permuted prompt)")
                        elif result_dict['api_call_successful']:
                            logger.warning(f"    Failed to parse LLM choice from response")
                        else:
                            logger.warning(f"    API call failed for Q_idx:{i}, Perm:{perm_string}")

                        # Write result (kept the same)
                        try:
                            json_string = json.dumps(result_dict, ensure_ascii=False)
                            f_out.write(json_string + '\n')
                            f_out.flush()
                        except Exception as e_write:
                            logger.error(f"Failed to write result for Q_idx:{i}, Perm:{perm_string}: {e_write}", exc_info=True)

                        # Delay between calls (kept the same)
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
        
        # Log output directory (kept the same)
        logs_for_filter_dir = os.path.join(project_root, "results", "__logs__")
        os.makedirs(logs_for_filter_dir, exist_ok=True)
        to_fix_log_path = os.path.join(logs_for_filter_dir, '0-to-Filter-Runs.log')
        to_fix_path = os.path.join(logs_for_filter_dir, '0-to-Filter')
        try:
            with open(to_fix_log_path, 'a', encoding='utf-8') as f_log_filter:
                f_log_filter.write(f"Run completed at {time.strftime('%Y-%m-%d %H:%M:%S')}: Output directory '{output_path_dir}', File '{filename}'\n")
            with open(to_fix_path, 'a', encoding='utf-8') as f_log_filter:
                f_log_filter.write(f"{args.output_dir}\n")
        except Exception as e_log_write:
            logger.error(f"Failed to write to '{to_fix_log_path}': {e_log_write}")


if __name__ == "__main__":
    main()

"""
The command-line interface remains EXACTLY the same:

--- Example: To run circular permutations ---
python experiments/run_experiment.py \
    --model_family gemini \
    --model_name gemini-1.5-flash-latest \
    --language en \
    --prompt_format base \
    --output_format base \
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
    --output_format json \
    --subtasks anatomy \
    --num_questions 1 \
    --permutation_type factorial \
    --num_factorial_permutations 5 \
    --delay 2
"""