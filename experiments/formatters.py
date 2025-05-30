# experiments/formatters.py
"""
Unified formatting system for prompt generation across all format combinations.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import json
import os
import sys

# Add project root to path (same as utils.py does)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

import prompts.prompt_templates as templates


class PromptFormatter:
    """Main formatter that delegates to specific format handlers."""
    
    def __init__(self):
        self.input_formatters = {
            'base': BaseInputFormatter(),
            'json': JSONInputFormatter(),
            'xml': XMLInputFormatter()
        }
        self.output_formatters = {
            'base': BaseOutputFormatter(),
            'json': JSONOutputFormatter(),
            'xml': XMLOutputFormatter()
        }
    
    def format_prompt(self, 
                     question_data: Dict,
                     option_order: List[str],
                     lang: str,
                     input_format: str,
                     output_format: str) -> Optional[str]:
        """
        Format a prompt with the specified input/output formats.
        
        Args:
            question_data: Dict with 'question', 'choices' (list of 4), 'answer_label'
            option_order: List like ['C', 'A', 'D', 'B'] mapping original to displayed positions
            lang: Language code ('en' or 'fr')
            input_format: Input format style ('base', 'json', 'xml')
            output_format: Output format style ('base', 'json', 'xml')
            
        Returns:
            Formatted prompt string or None if formatting fails
        """
        try:
            # Get components
            intro = templates.INTRO[lang]
            instruction = templates.INSTRUCTION_FORMATTED[lang]
            
            # Map choices according to option_order
            original_choices = {
                'A': question_data['choices'][0],
                'B': question_data['choices'][1], 
                'C': question_data['choices'][2],
                'D': question_data['choices'][3]
            }
            
            mapped_choices = {
                'A': original_choices[option_order[0]],
                'B': original_choices[option_order[1]],
                'C': original_choices[option_order[2]],
                'D': original_choices[option_order[3]]
            }
            
            # Format the question part
            input_formatter = self.input_formatters.get(input_format)
            if not input_formatter:
                return None
                
            question_part = input_formatter.format_question(
                question_data['question'],
                mapped_choices,
                lang
            )
            
            # Format the answer instruction part
            output_formatter = self.output_formatters.get(output_format)
            if not output_formatter:
                return None
                
            answer_part = output_formatter.format_answer_instruction(lang)
            
            # Combine with intro and instruction
            return input_formatter.combine_parts(
                intro, instruction, question_part, answer_part, lang
            )
            
        except Exception as e:
            # Log error if logger available
            return None


class InputFormatter(ABC):
    """Base class for input format handlers."""
    
    @abstractmethod
    def format_question(self, question: str, choices: Dict[str, str], lang: str) -> str:
        """Format the question and choices."""
        pass
    
    @abstractmethod
    def combine_parts(self, intro: str, instruction: str, 
                     question_part: str, answer_part: str, lang: str) -> str:
        """Combine all parts into final prompt."""
        pass


class BaseInputFormatter(InputFormatter):
    """Handles plain text input format."""
    
    def format_question(self, question: str, choices: Dict[str, str], lang: str) -> str:
        return f"{question}\n\nA) {choices['A']}\nB) {choices['B']}\nC) {choices['C']}\nD) {choices['D']}"
    
    def combine_parts(self, intro: str, instruction: str, 
                     question_part: str, answer_part: str, lang: str) -> str:
        return f"{intro}\n{instruction}\n\n{question_part}\n\n{answer_part}"


class JSONInputFormatter(InputFormatter):
    """Handles JSON input format."""
    
    def format_question(self, question: str, choices: Dict[str, str], lang: str) -> str:
        return json.dumps({
            "question": question,
            "choices": choices
        }, indent=2, ensure_ascii=False)
    
    def combine_parts(self, intro: str, instruction: str,
                     question_part: str, answer_part: str, lang: str) -> str:
        # Add comments at the top
        comments = f'// "{intro}"\n// "{instruction}"'
        
        # Parse the question JSON and add answer_format
        question_obj = json.loads(question_part)
        question_obj["answer_format"] = answer_part
        
        return f"{comments}\n\n{json.dumps(question_obj, indent=2, ensure_ascii=False)}"


class XMLInputFormatter(InputFormatter):
    """Handles XML input format."""
    
    def format_question(self, question: str, choices: Dict[str, str], lang: str) -> str:
        return f"""<question>
  <text>{question}</text>
  <choices>
    <A>{choices['A']}</A>
    <B>{choices['B']}</B>
    <C>{choices['C']}</C>
    <D>{choices['D']}</D>
  </choices>"""
    
    def combine_parts(self, intro: str, instruction: str,
                     question_part: str, answer_part: str, lang: str) -> str:
        comment = f"<!--\n{intro}\n{instruction}\n-->"
        
        # Insert answer format into question XML
        question_with_format = question_part + f"\n  <answer_format>\n    <format>\n      {answer_part}\n    </format>\n  </answer_format>\n</question>"
        
        return f"{comment}\n\n{question_with_format}"


class OutputFormatter(ABC):
    """Base class for output format handlers."""
    
    @abstractmethod
    def format_answer_instruction(self, lang: str) -> str:
        """Format the answer instruction based on output format."""
        pass


class BaseOutputFormatter(OutputFormatter):
    """Plain text output format."""
    
    def format_answer_instruction(self, lang: str) -> str:
        if lang == 'en':
            return "'Answer: $LETTER' (without quotes) where LETTER is one of ABCD"
        else:  # fr
            return "« Réponse : $LETTRE » (sans les guillemets) où LETTRE est l'une des lettres ABCD"


class JSONOutputFormatter(OutputFormatter):
    """JSON output format."""
    
    def format_answer_instruction(self, lang: str) -> str:
        return '{\n  "answer": "A | B | C | D"\n}'


class XMLOutputFormatter(OutputFormatter):
    """XML output format."""
    
    def format_answer_instruction(self, lang: str) -> str:
        return '<answer>A | B | C | D</answer>'

