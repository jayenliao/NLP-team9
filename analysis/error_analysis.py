import numpy as np
import pandas as pd
import json
import os

RESULT_DIR = "results/"

def get_result_data(args):
    if args.fn and not args.fn.endswith(".jsonl"):
        raise ValueError("Provided filename must end with .jsonl")

    if args.fn:
        fn = args.fn if RESULT_DIR in args.fn else os.path.join(RESULT_DIR, args.fn)
    else:
        print("No filename provided. Automatically selecting a file based on the model name, language, and format.")
        fn_prefix = f"{args.model_name}_{args.lang}_{args.format}_"
        fn_candidates = os.listdir(RESULT_DIR)
        fn_candidates = [f for f in fn_candidates if f.startswith(fn_prefix) and f.endswith(".jsonl")]
        if len(fn_candidates) == 0:
            raise ValueError(f"No files found with prefix {fn_prefix}.")
        elif len(fn_candidates) > 1:
            raise ValueError(f"Multiple files found with prefix {fn_prefix}. Please specify the file name.")
        fn = os.path.join(RESULT_DIR, fn_candidates[0])
        print(f"Automatically selected file: {fn} based on prefix {fn_prefix}")

    with open(fn, "r") as f:
        data = [json.loads(line) for line in f]
    return pd.DataFrame(data)

def get_user_input(prompt):
    while True:
        user_input = input(prompt).strip().lower()
        if user_input in ['y', 'n']:
            return user_input
        print("Invalid input. Please enter 'y' or 'n'.")

def main(args):
    data = get_result_data(args)

    print(f"Total number of samples: {len(data)}")
    print(f"Total number of successful API calls: {data['api_call_successful'].sum()}")
    print(f"Total number of samples with raw response: {data['api_raw_response'].notnull().sum()}")
    print(f"Total number of samples with parsed answer: {data['extracted_answer'].notnull().sum()}")
    print(f"Total number of samples with no raw response: {data['api_raw_response'].isnull().sum()}")
    print(f"Total number of samples with no parsed answer: {data['extracted_answer'].isnull().sum()}")

    id_selected = data["extracted_answer"].isnull() & data["api_raw_response"].notnull()
    print(f"Total number of samples with pure answer-parsing error (successful API call): {id_selected.sum()}")

    api_call_failure_rate = 1 - data["api_call_successful"].mean()
    no_api_raw_response_rate = data["api_raw_response"].isnull().mean()
    parse_ans_failure_rate = data["extracted_answer"].isnull().mean()

    print(f"API Call Failure Rate: {api_call_failure_rate:.2%}")
    print(f"API No Raw Response Rate: {no_api_raw_response_rate:.2%}")
    print(f"Parse Answer Failure Rate: {parse_ans_failure_rate:.2%}")
    print(f"Pure Answer-Parsing Failure rate (successful API call): {id_selected.mean():.2%}")

    # Ask user if they want to inspect API call failures
    user_input = get_user_input("\nShow samples with API call failure? (y/n): ")
    if user_input == 'y':
        print()
        print(data.loc[data["api_raw_response"].isnull()][["question_id", "option_permutation"]].to_markdown(index=True))

    # Ask user if they want to inspect parse answer failures
    user_input = get_user_input("\nShow samples with pure answer-parsing failure (sucessful API call)? (y/n): ")
    if user_input == 'y':
        print()
        print(data.loc[id_selected, ["question_id", "option_permutation"]].to_markdown(index=True))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Error analysis for model predictions.")
    parser.add_argument("--fn", type=str, default=None, help="Path to the JSON file containing model predictions.")
    parser.add_argument("--model_name", "-m", type=str, default="gemini-2.0-flash-lite", help="Name of the model used for predictions.")
    parser.add_argument("--lang", "-l", type=str, default="en", help="Language of the data.", choices=["en", "fr"])
    parser.add_argument("--format", "-f", type=str, default="json", help="Format of the data.", choices=["base", "json", "xml"])
    args = parser.parse_args()
    main(args)
