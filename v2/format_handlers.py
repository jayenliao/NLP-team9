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
        
        # Build the prompt based on format combination
        if input_format == "base":
            if output_format == "base":
                return self._format_base_to_base(question, reordered_choices, language)
            elif output_format == "json":
                return self._format_base_to_json(question, reordered_choices, language)
            elif output_format == "xml":
                return self._format_base_to_xml(question, reordered_choices, language)
        
        elif input_format == "json":
            if output_format == "base":
                return self._format_json_to_base(question, reordered_choices, language)
            
        elif input_format == "xml":
            if output_format == "base":
                return self._format_xml_to_base(question, reordered_choices, language)
        
        raise ValueError(f"Unsupported format combination: {input_format} -> {output_format}")
    
    def _format_base_to_base(self, question: Question, choices: List[str], language: str) -> str:
        """Base input -> Base output using exact templates"""
        if language == "en":
            # QUERY_TEMPLATE_BASE_BASE_EN
            template = """Answer the following multiple choice question.
The last line of your response should be your answer of the following format: 'Answer: $LETTER' (without quotes) where LETTER is one of ABCD. Think step by step before answering.

{Question}

A) {A}
B) {B}
C) {C}
D) {D}

Answer format: 'Answer: $LETTER' (without quotes) where LETTER is one of ABCD.""".strip()
        else:  # fr
            # QUERY_TEMPLATE_BASE_BASE_FR
            template = """Répondez à la question à choix multiples suivante.
La dernière ligne de votre réponse doit être au format suivant : « Réponse : $LETTRE » (sans les guillemets). Réfléchissez étape par étape avant de répondre.

{Question}

A) {A}
B) {B}
C) {C}
D) {D}

Format de réponse: « Réponse : $LETTRE » (sans les guillemets) où LETTRE est l'une des lettres ABCD""".strip()
        
        return template.format(
            Question=question.question,
            A=choices[0],
            B=choices[1],
            C=choices[2],
            D=choices[3]
        )
    
    def _format_base_to_json(self, question: Question, choices: List[str], language: str) -> str:
        """Base input -> JSON output using QUERY_TEMPLATE_BASE_JSON"""
        intro = "Answer the following multiple choice question." if language == "en" else "Répondez à la question à choix multiples suivante."
        
        if language == "en":
            instruction = "The last line of your response should be your answer of the following format: 'Answer: $LETTER' (without quotes) where LETTER is one of ABCD. Think step by step before answering."
        else:
            instruction = "La dernière ligne de votre réponse doit être au format suivant : « Réponse : $LETTRE » (sans les guillemets). Réfléchissez étape par étape avant de répondre."
        
        answer_format = "Answer format" if language == "en" else "Format de réponse"
        
        template = """{Intro}
{Instruction}

{Question}

A) {A}
B) {B}
C) {C}
D) {D}

{AnswerFormat}: 
```json
  {{
    "step_by_step_reasoning": ...,
    "answer": "A | B | C | D",
  }}
```""".strip()
        
        return template.format(
            Intro=intro,
            Instruction=instruction,
            Question=question.question,
            A=choices[0],
            B=choices[1],
            C=choices[2],
            D=choices[3],
            AnswerFormat=answer_format
        )
    
    def _format_base_to_xml(self, question: Question, choices: List[str], language: str) -> str:
        """Base input -> XML output using QUERY_TEMPLATE_BASE_XML"""
        intro = "Answer the following multiple choice question." if language == "en" else "Répondez à la question à choix multiples suivante."
        
        if language == "en":
            instruction = "The last line of your response should be your answer of the following format: 'Answer: $LETTER' (without quotes) where LETTER is one of ABCD. Think step by step before answering."
        else:
            instruction = "La dernière ligne de votre réponse doit être au format suivant : « Réponse : $LETTRE » (sans les guillemets). Réfléchissez étape par étape avant de répondre."
        
        answer_format = "Answer format" if language == "en" else "Format de réponse"
        
        template = """{Intro}
{Instruction}

{Question}

A) {A}
B) {B}
C) {C}
D) {D}

{AnswerFormat}: 
```xml
  <response>
    <step_by_step_reasoning>...</step_by_step_reasoning>
    <answer>A | B | C | D</answer>
  </response>
```""".strip()
        
        return template.format(
            Intro=intro,
            Instruction=instruction,
            Question=question.question,
            A=choices[0],
            B=choices[1],
            C=choices[2],
            D=choices[3],
            AnswerFormat=answer_format
        )
    
    def _format_json_to_base(self, question: Question, choices: List[str], language: str) -> str:
        """JSON input -> Base output using exact templates"""
        intro = "Answer the following multiple choice question." if language == "en" else "Répondez à la question à choix multiples suivante."
        
        if language == "en":
            instruction = "The last line of your response should be your answer of the following format: 'Answer: $LETTER' (without quotes) where LETTER is one of ABCD. Think step by step before answering."
        else:
            instruction = "La dernière ligne de votre réponse doit être au format suivant : « Réponse : $LETTRE » (sans les guillemets). Réfléchissez étape par étape avant de répondre."
        
        if language == "en":
            # QUERY_TEMPLATE_JSON_BASE_EN
            template = """// "{Intro}"
// "{Instruction}"

{{
  "question": "{Question}",
  "choices": {{
    "A": "{A}",
    "B": "{B}",
    "C": "{C}",
    "D": "{D}"
  }},
  "answer_format": "'Answer: $LETTER' (without quotes) where LETTER is one of ABCD."
 }}""".strip()
        else:  # fr
            # QUERY_TEMPLATE_JSON_BASE_FR
            template = """// "{Intro}"
// "{Instruction}"

{{
  "question": "{Question}",
  "choices": {{
    "A": "{A}",
    "B": "{B}",
    "C": "{C}",
    "D": "{D}"
  }},
  "answer_format": "« Réponse : $LETTRE » (sans les guillemets) où LETTRE est l'une des lettres ABCD."
 }}""".strip()
        
        # Escape quotes in question and choices
        escaped_question = question.question.replace('"', '\\"')
        escaped_choices = [c.replace('"', '\\"') for c in choices]
        
        return template.format(
            Intro=intro,
            Instruction=instruction,
            Question=escaped_question,
            A=escaped_choices[0],
            B=escaped_choices[1],
            C=escaped_choices[2],
            D=escaped_choices[3]
        )
    
    def _format_xml_to_base(self, question: Question, choices: List[str], language: str) -> str:
        """XML input -> Base output using exact templates"""
        intro = "Answer the following multiple choice question." if language == "en" else "Répondez à la question à choix multiples suivante."
        
        if language == "en":
            instruction = "The last line of your response should be your answer of the following format: 'Answer: $LETTER' (without quotes) where LETTER is one of ABCD. Think step by step before answering."
        else:
            instruction = "La dernière ligne de votre réponse doit être au format suivant : « Réponse : $LETTRE » (sans les guillemets). Réfléchissez étape par étape avant de répondre."
        
        if language == "en":
            # QUERY_TEMPLATE_XML_BASE_EN
            template = """<!--
{Intro}
{Instruction}
-->

<question>
  <text>{Question}</text>
  <choices>
    <A>{A}</A>
    <B>{B}</B>
    <C>{C}</C>
    <D>{D}</D>
  </choices>
  <answer_format>
    <format>
      'Answer: $LETTER' (without quotes) where LETTER is one of ABCD
    </format>
  </answer_format>
</question>""".strip()
        else:  # fr
            # QUERY_TEMPLATE_XML_BASE_FR
            template = """<!--
{Intro}
{Instruction}
-->

<question>
  <text>{Question}</text>
  <choices>
    <A>{A}</A>
    <B>{B}</B>
    <C>{C}</C>
    <D>{D}</D>
  </choices>
  <answer_format>
    <format>
      « Réponse : $LETTRE » (sans les guillemets) où LETTRE est l'une des lettres ABCD
    </format>
  </answer_format>
</question>""".strip()
        
        # Escape XML special characters
        escaped_question = question.question.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        escaped_choices = [c.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') for c in choices]
        
        return template.format(
            Intro=intro,
            Instruction=instruction,
            Question=escaped_question,
            A=escaped_choices[0],
            B=escaped_choices[1],
            C=escaped_choices[2],
            D=escaped_choices[3]
        )


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
        
        # If format-specific parsing failed, check for common issues
        if not answer:
            # Check if model indicates no answer
            if self._indicates_no_answer(response_text):
                return None
            
            # Only use fallback if response seems to contain an answer
            if self._likely_contains_answer(response_text, language):
                answer = self._parse_with_fallback(response_text, language)
        
        return answer
    
    def _parse_base_format(self, text: str, language: str) -> Optional[str]:
        """Parse expected base format"""
        if language == "en":
            # Look for the exact format specified in template
            patterns = [
                r"Answer:\s*([A-D])",
                r"answer:\s*([A-D])",
                r"^([A-D])$"  # Just the letter on its own line
            ]
        else:  # French
            patterns = [
                r"Réponse\s*:\s*([A-D])",
                r"réponse\s*:\s*([A-D])",
                r"^([A-D])$"
            ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).upper()
        
        return None
    
    def _parse_json_format(self, text: str) -> Optional[str]:
        """Parse JSON format response"""
        
        # Look for JSON code block first
        json_block_pattern = r'```json\s*(.*?)\s*```'
        json_match = re.search(json_block_pattern, text, re.DOTALL | re.IGNORECASE)
        
        json_str = None
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # Try to find JSON object in the text
            brace_start = text.find('{')
            brace_end = text.rfind('}')
            if brace_start != -1 and brace_end != -1 and brace_end > brace_start:
                json_str = text[brace_start:brace_end+1]
        
        if json_str:
            try:
                # Clean up common issues
                json_str = json_str.replace('...', '"..."')  # Replace ellipsis
                json_str = re.sub(r',\s*}', '}', json_str)  # Remove trailing commas
                
                data = json.loads(json_str)
                
                # Look for 'answer' field
                if 'answer' in data:
                    answer = data['answer'].strip().upper()
                    # Make sure it's a single letter, not the template
                    if answer in ['A', 'B', 'C', 'D']:
                        return answer
                
            except json.JSONDecodeError:
                pass
        
        # Fallback: look for answer field in text
        answer_pattern = r'"answer"\s*:\s*"([A-D])"'
        match = re.search(answer_pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        
        return None
    
    def _parse_xml_format(self, text: str) -> Optional[str]:
        """Parse XML format response"""
        
        # Look for XML code block first
        xml_block_pattern = r'```xml\s*(.*?)\s*```'
        xml_match = re.search(xml_block_pattern, text, re.DOTALL | re.IGNORECASE)
        
        if xml_match:
            xml_content = xml_match.group(1)
        else:
            xml_content = text
        
        # Look for <answer> tag
        answer_pattern = r'<answer>\s*([A-D])\s*</answer>'
        match = re.search(answer_pattern, xml_content, re.IGNORECASE)
        if match:
            return match.group(1).upper()
        
        return None
    
    def _indicates_no_answer(self, text: str) -> bool:
        """Check if model explicitly says no answer"""
        no_answer_patterns = [
            r"none of the (?:above )?options",
            r"no correct answer",
            r"cannot determine",
            r"insufficient information",
            r"aucune.*réponse.*correcte",
            r"pas de réponse correcte"
        ]
        
        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in no_answer_patterns)
    
    def _likely_contains_answer(self, text: str, language: str) -> bool:
        """Check if response likely contains an answer attempt"""
        if language == "en":
            indicators = [
                r"answer is",
                r"correct answer",
                r"choose",
                r"select",
                r"my answer"
            ]
        else:
            indicators = [
                r"réponse est",
                r"réponse correcte",
                r"choisis",
                r"sélectionne",
                r"ma réponse"
            ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in indicators)
    
    def _parse_with_fallback(self, text: str, language: str) -> Optional[str]:
        """Fallback parsing - only for clear cases"""
        
        # Common patterns that indicate a clear answer
        if language == "en":
            patterns = [
                r"the answer is\s*:?\s*([A-D])",
                r"correct answer is\s*:?\s*([A-D])",
                r"i choose\s*:?\s*([A-D])",
                r"therefore,?\s*([A-D])"
            ]
        else:
            patterns = [
                r"la réponse est\s*:?\s*([A-D])",
                r"réponse correcte est\s*:?\s*([A-D])",
                r"je choisis\s*:?\s*([A-D])"
            ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        # Last resort: look for letter in parentheses at end
        match = re.search(r'\(([A-D])\)\s*\.?\s*$', text, re.IGNORECASE)
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