import time
from core_runner import (
    format_prompt, parse_response,
    structure_result, get_api_client, call_llm_api
)
from utils import load_prepared_dataset

def run_one_problem(client, model_family, model_name, language, input_format, task_problem, permutation):
    """
    Run a single problem through the model and return the result.
    """
    # Format the prompt
    data_item = task_problem
    template_content = ""
    prompt = format_prompt(template_content, data_item, permutation, language, input_format)
    if not prompt:
        print(f"Warning: Skipping This question - Failed to format prompt.")
        return None
    api_response, api_ok = call_llm_api(client, model_family, model_name, prompt)
    if not api_ok:
        print(f"Warning: API call failed for this question, Perm:{permutation}")
        return None

    # Parse Response
    parsed_answer = None
    if api_ok and api_response:
        response_text = None
        try:
            if model_family == 'gemini':
                response_text = api_response.text
            elif model_family == 'mistral':
                response_text = api_response.choices[0].message.content
        except AttributeError:
            print(f"Warninig: Attribute error for this question, Perm:{permutation}. Response: {api_response}")
            return None
        except Exception as e:
            print(f"Error: Error accessing response for this question, Perm:{permutation}: {e}")
            response_text = None

        if response_text:
            parsed_answer = parse_response(response_text)
            if parsed_answer:
                print(f"Parsed answer for this question, Perm:{permutation}: '{parsed_answer}'")
            else:
                print(f"Warning: Failed to parse answer for this question, Perm:{permutation}: {response_text[:100]}...")
        else:
            print(f"Warning: No response text for this question, Perm:{permutation}")
    
    print(f"Delaying for {2} seconds...")
    time.sleep(2)

    return {
        "api_raw_response": api_response,
        "api_ok": api_ok,
        "parsed_answer": parsed_answer
    }

def run_question_selected(model_family, model_name, language, input_format, question):
    """
    Run a single question through the model and return the result.
    """ 
    # Initialize the model based on the model name
    client = get_api_client(model_family)
    if not client:
        print(f"Fatal: Failed to initialize API client for {model_family}.")
        return

    subtask = question["subtask"]
    # load the dataset
    full_dataset = load_prepared_dataset()
    if not full_dataset:
        print("Fatal: Failed to load prepared dataset.")
        return question
    print(f"Running subtasks: {subtask} - {language} - {input_format}")
    if subtask not in full_dataset or language not in full_dataset[subtask]:
        print(f"Subtask {subtask} or language {language} not found in dataset. Skipping.")
        return question
    task_problem = full_dataset[subtask][language][question["question_index"]]
    permutation = question["option_permutation"]
    # Run the question through the model
    id = question["option_permutation"]
    print(f"Processing {subtask} - {language} - Question: {id} - Running Permutation {permutation}")
    result = run_one_problem(client, model_family, model_name, language, input_format, task_problem, permutation)
    if not result:
        print(f"Warning: Failed to run question {question['question_index']} with permutation {permutation}.")
        return question
    # Structure the result
    result_dict = structure_result(
        data_item=task_problem,
        subtask=subtask,
        language=language,
        model_name=model_name,
        input_format=input_format,
        option_permutation=permutation,
        api_raw_response=result["api_raw_response"],
        api_call_successful=result["api_ok"],
        extracted_answer=result["parsed_answer"],
        log_probabilities=None,
        question_index=question["question_index"]
    )
    return result_dict