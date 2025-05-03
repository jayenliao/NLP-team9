"""
results_jsonl_format = {
    "trial_id": str(uuid.uuid4()), # Generate a unique ID for this specific trial run
    "question_id": q_id,
    "question_index": question_index, # Index within the run (0-99)
    "subtask": subtask,
    "language": language,
    "model_name": model_name,
    "input_format": input_format,
    "option_permutation": "".join(option_permutation), # Store as string e.g., "BCAD"
    "api_call_successful": api_call_successful,
    "api_raw_response": str(api_raw_response) if api_raw_response is not None else None, # Store as string for simpler JSON
    "extracted_answer": extracted_answer,
    "log_probabilities": log_probabilities, # Store as is (dict or None)
    "ground_truth_answer": ground_truth_label,
    "is_correct": is_correct
}
"""