# experiments/utils.py

import pickle
import time
import os
from dotenv import load_dotenv
from mistralai import Mistral
from google import genai
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from prompts.prompt_templates import (
    QUERY_TEMPLATE_PLAIN,
    QUERY_TEMPLATE_JSON,
    QUERY_TEMPLATE_XML,
    INTRO,
    INSTRUCTION,
    CHOICE
)

def load_prepared_dataset():
    """
    Loads the prepared dataset from a pickle file.

    Args:
        file_path (str): The path to the pickle file.

    Returns:
        dict: A dictionary containing the selected datasets,
              or None if the file does not exist.
    """
    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "ds_selected.pkl")
    if not os.path.exists(file_path):
        print(f"No dataset at {file_path}")
        return None
    with open(file_path, "rb") as f:
        return pickle.load(f)
    
if __name__ == "__main__":
    dataset = load_prepared_dataset()



def load_api_keys():
    """
    Loads API keys from the .env file.
    """
    load_dotenv() 
    google_api_key = os.getenv("GOOGLE_API_KEY")
    mistral_api_key = os.getenv("MISTRAL_API_KEY")

    if not google_api_key:
        print("Warning: GOOGLE_API_KEY not found in .env")
    if not mistral_api_key:
        print("Warning: MISTRAL_API_KEY not found in .env")

    return google_api_key, mistral_api_key



# # Test Block for load dataset(remove later)
#     if dataset:
#         print(f"Loaded dataset contains {len(dataset)} subtasks.")
#         first_subtask = list(dataset.keys())[0]
#         print(f"First subtask: {first_subtask}")
#         first_question_en = dataset[first_subtask]['en'][0]
#         print("Example English question:", first_question_en)


def format_multichoice_question(row, style='plain', lang="en"):
    # print("in utils")
    ###################################
    # Input:                          #
    # - row: Question, A, B, C, D     #
    # - style: 'plain', 'json', 'xml' #
    # - lang: "EN-US", "FR-FR"        #
    # Output: formatted prompt        #
    ###################################
    try:
        intro = INTRO[lang]
        instruction = INSTRUCTION[lang]
        template = None
        # print(row)
        # choice = CHOICE[lang]
        if style == 'json':
            template = QUERY_TEMPLATE_JSON
        elif style == 'xml':
            template = QUERY_TEMPLATE_XML
        else:
            template = QUERY_TEMPLATE_PLAIN
        row['Intro'] = intro
        row['Instruction'] = instruction
        # print(template)
        # print(type(template))
        test = template.format(**row)
        # print(test)
        return test #Choice = choice
    except (KeyError, IndexError): # Handle missing keys or incorrect list sizes
        return None
    except Exception: # Generic catch-all
        return None

