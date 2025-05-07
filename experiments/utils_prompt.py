# experiments/utils.py

import pickle
import os
from dotenv import load_dotenv
from mistralai import Mistral
from google import genai

from prompts.prompt_templates import (
    QUERY_TEMPLATE_PLAIN,
    QUERY_TEMPLATE_JSON,
    QUERY_TEMPLATE_XML,
    INTRO,
    INSTRUCTION,
    CHOICE
)

def format_multichoice_question(row, style='plain', lang="EN-US"):
    ###################################
    # Input:                          #
    # - row: Question, A, B, C, D     #
    # - style: 'plain', 'json', 'xml' #
    # - lang: "EN-US", "FR-FR"        #
    # Output: formatted prompt        #
    ###################################
    intro = INTRO[lang]
    instruction = INSTRUCTION[lang]
    template = None
    # choice = CHOICE[lang]
    if style == 'json':
        template = QUERY_TEMPLATE_JSON
    elif style == 'xml':
        template = QUERY_TEMPLATE_XML
    else:
        template = QUERY_TEMPLATE_PLAIN
    return template.format(Intro = intro, Instruction = instruction, **row) #Choice = choice
