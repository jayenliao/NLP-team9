# experiments/run_prob_selected.py
import logging
import sys
import os
import argparse
import json
import time
import itertools
from tqdm import tqdm

from core_runner import (
    load_prompt_template, format_prompt, parse_response,
    structure_result, get_api_client, call_llm_api
)
from utils import load_prepared_dataset, load_api_keys

# Logging Setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_file_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'experiment.log')
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
if not logger.handlers:
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setLevel(logging.INFO)
    f_handler = logging.FileHandler(log_file_path)
    f_handler.setLevel(logging.INFO)
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    c_handler.setFormatter(log_format)
    f_handler.setFormatter(log_format)
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

ORI_NAME = "gemini-2.0-flash-lite_fr_json_20250511-214603_api_failed"
MODEL_FAMILY = "gemini"
MODEL_NAME = "gemini-2.0-flash-lite"
LANGUAGE = "fr"
PROMPT_FORMAT = "json"
SUBTASKS = "high_school_european_history"
OUTPUT_DIR = "results/rerun"
OUTPUT_FILE = ORI_NAME + "_reruned.jsonl"
DELAY = 5
TO_RERUN = "results/failed/" + ORI_NAME + ".jsonl"

def main():
    # Parse Arguments
    parser = argparse.ArgumentParser(description="Run LLM evaluation experiments for order sensitivity.")

    # args = parser.parse_args()
    # logger.info(f"Starting experiment with args: {args}")

    # Initialize
    logger.info("Initializing")
    load_api_keys()
    client = get_api_client(MODEL_FAMILY)
    if not client:
        print(f"Fatal: Failed to initialize API client for {MODEL_FAMILY}.")
        return

    full_dataset = load_prepared_dataset()
    if not full_dataset:
        print("Fatal: Failed to load prepared dataset.")
        return

    template_content = load_prompt_template(PROMPT_FORMAT)
    if not template_content:
        print(f"Fatal: Failed to load prompt template '{PROMPT_FORMAT}'.")
        return

    # Determine Subtasks
    if SUBTASKS.lower() == 'all':
        subtasks_to_run = list(full_dataset.keys())
    else:
        requested_subtasks = SUBTASKS.split(',')
        subtasks_to_run = [st for st in requested_subtasks if st in full_dataset]
        if not subtasks_to_run:
            print("Fatal: No valid subtasks found in dataset.")
            return
    logger.info(f"Running subtasks: {subtasks_to_run}")


    output_path_dir = os.path.join(os.path.dirname(__file__), '..', OUTPUT_DIR)
    os.makedirs(output_path_dir, exist_ok=True)
    output_path = os.path.join(output_path_dir, OUTPUT_FILE)
    logger.info(f"Saving results to: {output_path}")

    rerun_list = []
    # Determined to run
    with open(TO_RERUN, "r") as file:
        for line in file:
            add_q = {}
            jsonl_obj = json.loads(line)
            add_q["q"] = jsonl_obj["question_index"]
            add_q["p"] = jsonl_obj["option_permutation"]
            rerun_list.append(add_q)
    # Experiment Loop
    total = len(rerun_list)
    logger.info(f"Starting experiment for rerunning {total} questions")
    total_processed_count = 0
    
    try:
        with open(output_path, 'a', encoding='utf-8') as f_out:
            for subtask in tqdm(subtasks_to_run, desc="Subtasks Progress"):
                if subtask not in full_dataset or LANGUAGE not in full_dataset[subtask]:
                    logger.warning(f"Subtask {subtask} or language {LANGUAGE} not found in dataset. Skipping.")
                    continue
                task_data = full_dataset[subtask][LANGUAGE]
                for torun in rerun_list:
                    question_index_in_run = torun["q"]
                    current_permutation = torun["p"]
                    data_item = task_data[question_index_in_run]
                    logger.info(f"Processing {subtask} - {LANGUAGE} - Question: {question_index_in_run} - Running Permutation {current_permutation}")
                    current_prompt = format_prompt(template_content, data_item, current_permutation, LANGUAGE, PROMPT_FORMAT)
                    if not current_prompt:
                        logger.warning(f"Skipping Q:{question_index_in_run}, Perm:{current_permutation} - Failed to format prompt.")
                        continue
                    api_response, api_ok = call_llm_api(client, MODEL_FAMILY, MODEL_NAME, current_prompt)
                    if not api_ok:
                        logger.warning(f"API call failed for Q:{question_index_in_run}, Perm:{current_permutation}")

                    # Parse Response
                    parsed_answer = None
                    if api_ok and api_response:
                        response_text = None
                        try:
                            if MODEL_FAMILY == 'gemini':
                                response_text = api_response.text
                            elif MODEL_FAMILY == 'mistral':
                                response_text = api_response.choices[0].message.content
                        except AttributeError:
                            logger.warning(f"Attribute error for Q:{question_index_in_run}, Perm:{current_permutation}. Response: {api_response}")
                            response_text = None
                        except Exception as e:
                            logger.error(f"Error accessing response for Q:{question_index_in_run}, Perm:{current_permutation}: {e}")
                            response_text = None

                        if response_text:
                            parsed_answer = parse_response(response_text)
                            if parsed_answer:
                                logger.info(f"Parsed answer for Q:{question_index_in_run}, Perm:{current_permutation}: '{parsed_answer}'")
                            else:
                                logger.warning(f"Failed to parse answer for Q:{question_index_in_run}, Perm:{current_permutation}: {response_text[:100]}...")
                        else:
                            logger.warning(f"No response text for Q:{question_index_in_run}, Perm:{current_permutation}")

                    # Structure Result
                    result_dict = structure_result(
                        data_item=data_item,
                        subtask=subtask,
                        language=LANGUAGE,
                        model_name=MODEL_NAME,
                        input_format=PROMPT_FORMAT,
                        option_permutation=current_permutation,
                        api_raw_response=api_response,
                        api_call_successful=api_ok,
                        extracted_answer=parsed_answer,
                        log_probabilities=None,
                        question_index=question_index_in_run
                    )

                    # Save Result
                    try:
                        json_string = json.dumps(result_dict, ensure_ascii=False)
                        f_out.write(json_string + '\n')
                        total_processed_count += 1
                    except Exception as e:
                        logger.error(f"Failed to write result for Q:{question_index_in_run}, Perm:{current_permutation}: {e}")

                    # Delay
                    if DELAY > 0:
                        logger.debug(f"Delaying for {DELAY} seconds...")
                        time.sleep(DELAY)
                    
                logger.info(f"Finished subtask: {subtask}")

    except Exception as e:
        logger.error(f"Experiment error: {e}")
    finally:
        logger.info("Experiment finished")
        logger.info(f"Total questions processed: {total_processed_count}")
    

if __name__ == "__main__":
    main()

"""
    --- How to run in terminal ---
    --model_family gemini \
    --model_name gemini-2.0-flash-lite \
    --language en \   
    --prompt_format base \
    --subtasks abstract_algebra \
    --num_questions 1 \
    --output_file output_file_name.jsonl \      
    --delay 5
    
    """
