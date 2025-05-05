"""
results_jsonl_format = {
  "trial_id": "unique_identifier_string",
  "question_id": "mmlu_original_question_id",
  "question_index": 0, // Index within the run (0-99)
  "subtask": "mmlu_subtask_name",
  "language": "en",
  "model_name": "specific_model_used",
  "input_format": "format_description",
  "option_permutation": "BCAD", // The actual order options were presented
  "api_call_successful": true,
  "api_raw_response": { "... raw api response ..." },
  "extracted_answer": "A", // The positional answer ('A'/'B'/'C'/'D') from the prompt output. Null if parsing/call failed.
  "model_choice_original_label": "C", // Added: The original label ('A'/'B'/'C'/'D') corresponding to the choice made by the model. Null if parsing/call/mapping failed.
  "log_probabilities": { "...": ... }, // Null if unavailable/not requested.
  "ground_truth_answer": "C", // The correct original answer label
  "is_correct": true // boolean: Does model_choice_original_label match ground_truth_answer? Null if cannot be determined.
}
"""