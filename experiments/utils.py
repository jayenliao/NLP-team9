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

import prompts.prompt_templates as templates

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


def format_multichoice_question(row, in_style='base', out_style='base', lang="en"):
    # print("in utils")
    ###################################
    # Input:                          #
    # - row: Question, A, B, C, D     #
    # - style: 'plain', 'json', 'xml' #
    # - lang: "EN-US", "FR-FR"        #
    # Output: formatted prompt        #
    ###################################
    try:
        intro = templates.INTRO[lang]
        template = None
        # print(row)
        # choice = CHOICE[lang]
        answer_format_lang = 0
        if in_style == 'json':
            if out_style == 'json':
                template = templates.QUERY_TEMPLATE_JSON_JSON
            elif out_style == 'xml':   
                template = templates.QUERY_TEMPLATE_JSON_XML
            else:
                if lang == 'en':
                    template = templates.QUERY_TEMPLATE_JSON_BASE_EN
                else:   
                    template = templates.QUERY_TEMPLATE_JSON_BASE_FR
        elif in_style == 'xml':
            if out_style == 'json':
                template = templates.QUERY_TEMPLATE_XML_JSON
            elif out_style == 'xml':   
                template = templates.QUERY_TEMPLATE_XML_XML
            else:
                if lang == 'en':
                    template = templates.QUERY_TEMPLATE_XML_BASE_EN
                else:   
                    template = templates.QUERY_TEMPLATE_XML_BASE_FR
        else:
            if out_style == 'json':
                answer_format_lang = 1
                template = templates.QUERY_TEMPLATE_BASE_JSON
            elif out_style == 'xml':
                answer_format_lang = 1
                template = templates.QUERY_TEMPLATE_BASE_XML
            else:
                if lang == 'en':
                    template = templates.QUERY_TEMPLATE_BASE_BASE_EN
                else:   
                    template = templates.QUERY_TEMPLATE_BASE_BASE_FR

        row['Intro'] = intro
        row['Instruction'] = templates.INSTRUCTION_FORMATTED[lang]
        if answer_format_lang:
            row['AnswerFormat'] = templates.ANSWER_FORMAT_PROMPT[lang]

        #print(template)
        # print(type(template))
        test = template.format(**row)
        # print(test)
        return test #Choice = choice
    except KeyError as e:
        print(f"KeyError: {e}")
        return None
    # except (KeyError, IndexError): # Handle missing keys or incorrect list sizes
    #     print(KeyError, IndexError)
    #     return None
    # except Exception: # Generic catch-all
    #     print(Exception)
    #     return None

if __name__ == "__main__":
    # Test for format_multichoice_question
    row = {
        'Question': 'What is the capital of France?',
        'A': 'Berlin',
        'B': 'Madrid',
        'C': 'Paris',
        'D': 'Rome'
    }

    in_type = 'xml'
    out_type = 'base'
    lang_type = ['en', 'fr']

    for lang in lang_type:
        formatted_question = format_multichoice_question(row, in_style=in_type, out_style=out_type, lang=lang)
        print(f"Formatted question ({in_type}, {out_type}, {lang}):")
        print(formatted_question)
        print("-" * 40)
