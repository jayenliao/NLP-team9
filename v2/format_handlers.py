#!/usr/bin/env python3
"""
Format Handlers for all input/output combinations
Handles: base, json, xml formats for both input and output
"""

import json
import re
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Question:
    """Question data structure"""
    id: str
    question: str
    choices: List[str]
    correct_answer: str
    subtask: str


class PromptFormatter:
    """Handles all prompt formatting combinations"""
    
    TEMPLATES = {
        'en': {
            'intro': "Answer the following multiple choice question.",
            'instruction': "The last line of your response should be of the following format: 'Answer: $LETTER' (without quotes) where LETTER is one of ABCD.",
            'instruction_think': "Think step by step before answering.",
            'answer_prefix': "Answer:",
            'choice_label': "choices"
        },
        'fr': {
            'intro': "Répondez à la question à choix multiples suivante.",
            'instruction': "La dernière ligne de votre réponse doit être au format suivant : « Réponse : $LETTRE » (sans les guillemets) où LETTRE est l'une des lettres ABCD.",
            'instruction_think': "Réfléchissez étape par étape avant de répondre.",
            'answer_prefix': "Réponse:",
            'choice_label': "choix"
        }
    }
    
    def format_prompt(self, question: Question, permutation: List[int], 
                     input_format: str, output_format: str, language: str) -> str:
        """
        Format a question into a prompt based on input/output format combination
        
        5 combinations:
        1. base -> base
        2. base -> json
        3. base -> xml
        4. json -> base
        5. xml -> base
        """
        
        # Reorder choices based on permutation
        reordered_choices = [question.choices[i] for i in permutation]
        
        # Get language templates
        lang_templates = self.TEMPLATES[language]
        
        # Build the prompt based on format combination
        if input_format == "base":
            if output_format == "base":
                return self._format_base_to_base(question, reordered_choices, lang_templates)
            elif output_format == "json":
                return self._format_base_to_json(question, reordered_choices, lang_templates)
            elif output_format == "xml":
                return self._format_base_to_xml(question, reordered_choices, lang_templates)
        
        elif input_format == "json":
            if output_format == "base":
                return self._format_json_to_base(question, reordered_choices, lang_templates, language)
            
        elif input_format == "xml":
            if output_format == "base":
                return self._format_xml_to_base(question, reordered_choices, lang_templates, language)
        
        raise ValueError(f"Unsupported format combination: {input_format} -> {output_format}")
    
    def _format_base_to_base(self, question: Question, choices: List[str], templates: dict) -> str:
        """Base input -> Base output (original format)"""
        prompt = f"{templates['intro']}\n"
        prompt += f"{templates['instruction']}\n\n"
        prompt += f"{question.question}\n\n"
        
        for i, choice in enumerate(choices):
            prompt += f"{chr(65+i)}) {choice}\n"
        
        return prompt.strip()
    
    def _format_base_to_json(self, question: Question, choices: List[str], templates: dict) -> str:
        """Base input -> JSON output"""
        prompt = f"{templates['intro']}\n"
        prompt += f"{templates['instruction_think']}\n\n"
        prompt += f"{question.question}\n\n"
        
        for i, choice in enumerate(choices):
            prompt += f"{chr(65+i)}) {choice}\n"
        
        prompt += f"\n{templates['answer_prefix']}\n"
        prompt += "```json\n"
        prompt += "{\n"
        prompt += '  "reasoning": "Your step-by-step reasoning here",\n'
        prompt += '  "answer": "A | B | C | D"\n'
        prompt += "}\n"
        prompt += "```"
        
        return prompt.strip()
    
    def _format_base_to_xml(self, question: Question, choices: List[str], templates: dict) -> str:
        """Base input -> XML output"""
        prompt = f"{templates['intro']}\n"
        prompt += f"{templates['instruction_think']}\n\n"
        prompt += f"{question.question}\n\n"
        
        for i, choice in enumerate(choices):
            prompt += f"{chr(65+i)}) {choice}\n"
        
        prompt += f"\n{templates['answer_prefix']}\n"
        prompt += "```xml\n"
        prompt += "<response>\n"
        prompt += "  <reasoning>Your step-by-step reasoning here</reasoning>\n"
        prompt += "  <answer>A | B | C | D</answer>\n"
        prompt += "</response>\n"
        prompt += "```"
        
        return prompt.strip()
    
    def _format_json_to_base(self, question: Question, choices: List[str], templates: dict, language: str) -> str:
        """JSON input -> Base output"""
        # Create JSON structure
        json_data = {
            "instruction": templates['intro'],
            "output_format": templates['instruction'],
            "question": question.question,
            templates['choice_label']: {
                chr(65+i): choice for i, choice in enumerate(choices)
            }
        }
        
        prompt = json.dumps(json_data, ensure_ascii=False, indent=2)
        return prompt
    
    def _format_xml_to_base(self, question: Question, choices: List[str], templates: dict, language: str) -> str:
        """XML input -> Base output"""
        prompt = f"""<task>
  <instruction>{templates['intro']}</instruction>
  <output_format>{templates['instruction']}</output_format>
  <question>{question.question}</question>
  <{templates['choice_label']}>
    <A>{choices[0]}</A>
    <B>{choices[1]}</B>
    <C>{choices[2]}</C>
    <D>{choices[3]}</D>
  </{templates['choice_label']}>
</task>"""
        
        return prompt


class ResponseParser:
    """Enhanced response parser for all output formats"""
    
    def parse(self, response_text: str, output_format: str, language: str) -> Optional[str]:
        """
        Parse response based on expected output format
        Returns: 'A', 'B', 'C', 'D', or None
        """
        
        if not response_text:
            return None
        
        # Try format-specific parsing first
        if output_format == "base":
            answer = self._parse_base_format(response_text, language)
        elif output_format == "json":
            answer = self._parse_json_format(response_text)
        elif output_format == "xml":
            answer = self._parse_xml_format(response_text)
        else:
            answer = None
        
        # If format-specific parsing failed, try fallback strategies
        if not answer:
            answer = self._parse_with_fallback_patterns(response_text)
        
        
        return answer
    
    def _parse_base_format(self, text: str, language: str) -> Optional[str]:
        """Parse expected base format"""
        patterns = {
            'en': [
                r"Answer:\s*([A-D])",
                r"answer:\s*([A-D])",
                r"Answer\s*:\s*([A-D])",
                r"^([A-D])$"  # Just the letter on its own line
            ],
            'fr': [
                r"Réponse\s*:\s*([A-D])",
                r"réponse\s*:\s*([A-D])",
                r"Réponse:\s*([A-D])",
                r"^([A-D])$"
            ]
        }
        
        lang_patterns = patterns.get(language, patterns['en'])
        
        for pattern in lang_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).upper()
        
        return None
    
    def _parse_json_format(self, text: str) -> Optional[str]:
        """Parse JSON format response"""
        
        # Try to extract JSON block
        json_pattern = r'```json\s*(.*?)\s*```'
        json_match = re.search(json_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if json_match:
            json_str = json_match.group(1)
            try:
                data = json.loads(json_str)
                answer = data.get('answer', '').strip().upper()
                if answer in ['A', 'B', 'C', 'D']:
                    return answer
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON without code block
        try:
            # Look for JSON-like structure
            json_start = text.find('{')
            json_end = text.rfind('}')
            if json_start != -1 and json_end != -1:
                json_str = text[json_start:json_end+1]
                data = json.loads(json_str)
                answer = data.get('answer', '').strip().upper()
                if answer in ['A', 'B', 'C', 'D']:
                    return answer
        except:
            pass
        
        # Look for answer field pattern
        answer_pattern = r'"answer"\s*:\s*"([A-D])"'
        match = re.search(answer_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        
        return None
    
    def _parse_xml_format(self, text: str) -> Optional[str]:
        """Parse XML format response"""
        
        # Try to extract XML block
        xml_pattern = r'```xml\s*(.*?)\s*```'
        xml_match = re.search(xml_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if xml_match:
            xml_str = xml_match.group(1)
        else:
            xml_str = text
        
        # Look for answer tag
        answer_patterns = [
            r'<answer>([A-D])</answer>',
            r'<answer>\s*([A-D])\s*</answer>',
            r'<answer>.*?([A-D]).*?</answer>'  # Answer might have extra text
        ]
        
        for pattern in answer_patterns:
            match = re.search(pattern, xml_str, re.IGNORECASE)
            if match:
                potential_answer = match.group(1).upper()
                if potential_answer in ['A', 'B', 'C', 'D']:
                    return potential_answer
        
        return None
    
    def _parse_with_fallback_patterns(self, text: str) -> Optional[str]:
        """Try common answer patterns regardless of format"""
        
        # Common patterns across formats
        patterns = [
            # Direct answer patterns
            r"the answer is\s*:?\s*([A-D])",
            r"correct answer is\s*:?\s*([A-D])",
            r"my answer is\s*:?\s*([A-D])",
            r"final answer\s*:?\s*([A-D])",
            
            # Letter in parentheses or with punctuation
            r"\(([A-D])\)",
            r"\b([A-D])\)",
            r"\b([A-D])\.",
            
            # Choosing patterns
            r"choose\s*:?\s*([A-D])",
            r"select\s*:?\s*([A-D])",
            r"pick\s*:?\s*([A-D])",
            
            # Answer patterns with quotes
            r"[\"']([A-D])[\"']",
            r"answer[\"']\s*:\s*[\"']([A-D])[\"']",
            
            # Standalone letter at end of text
            r"([A-D])\s*$"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).upper()
        
        return None


# Test the format handlers
if __name__ == "__main__":
    # Create a test question
    test_question = Question(
        id="test_1",
        question="What is the capital of France?",
        choices=["London", "Berlin", "Paris", "Madrid"],
        correct_answer="C",
        subtask="geography"
    )
    
    formatter = PromptFormatter()
    parser = ResponseParser()
    
    # Test all format combinations
    formats = [
        ("base", "base"),
        ("base", "json"),
        ("base", "xml"),
        ("json", "base"),
        ("xml", "base")
    ]
    
    print("Testing all format combinations:\n")
    
    for in_fmt, out_fmt in formats:
        print(f"\n{'='*60}")
        print(f"Format: {in_fmt} -> {out_fmt}")
        print(f"{'='*60}")
        
        prompt = formatter.format_prompt(
            test_question,
            [0, 1, 2, 3],  # Normal order
            in_fmt,
            out_fmt,
            "en"
        )
        
        print(prompt)
        print()