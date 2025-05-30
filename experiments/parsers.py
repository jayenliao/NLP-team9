# experiments/parsers.py
"""
Response parsing for different output formats.
"""
import re
import json
from typing import Optional
from abc import ABC, abstractmethod


class ResponseParser:
    """Main parser that delegates to format-specific parsers."""
    
    def __init__(self):
        self.parsers = {
            'base': BaseResponseParser(),
            'json': JSONResponseParser(),
            'xml': XMLResponseParser()
        }
    
    def parse(self, response_text: str, output_format: str) -> Optional[str]:
        """
        Parse response based on output format.
        
        Returns:
            Extracted answer ('A', 'B', 'C', 'D') or None if parsing fails
        """
        parser = self.parsers.get(output_format)
        if not parser:
            return None
            
        return parser.extract_answer(response_text)


class FormatParser(ABC):
    """Base class for format-specific parsers."""
    
    @abstractmethod
    def extract_answer(self, response_text: str) -> Optional[str]:
        """Extract the answer from response text."""
        pass


class BaseResponseParser(FormatParser):
    """Parser for plain text responses."""
    
    # Answer prefixes for different languages
    ANSWER_PREFIXES = [
        r"Answer\s*:",         # English
        r"Réponse\s*:",        # French
    ]
    
    def extract_answer(self, response_text: str) -> Optional[str]:
        # Build regex pattern
        prefix_pattern = r"(?:" + "|".join(self.ANSWER_PREFIXES) + r")"
        pattern = rf"^\s*(?:[*\#_]*)?\s*{prefix_pattern}\s*[*\#_]*([A-D])"
        
        match = re.search(pattern, response_text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1).upper()
        
        return None


class JSONResponseParser(FormatParser):
    """Parser for JSON responses."""
    
    def extract_answer(self, response_text: str) -> Optional[str]:
        # Try to find JSON block
        json_block_pattern = r"```json\s*(\{.*?\})\s*```"
        json_match = re.search(json_block_pattern, response_text, re.DOTALL | re.IGNORECASE)
        
        if json_match:
            try:
                json_obj = json.loads(json_match.group(1))
                answer = json_obj.get("answer", "").upper()
                if answer in ["A", "B", "C", "D"]:
                    return answer
            except json.JSONDecodeError:
                pass
        
        # Fallback: try to parse entire response as JSON
        try:
            json_obj = json.loads(response_text)
            answer = json_obj.get("answer", "").upper()
            if answer in ["A", "B", "C", "D"]:
                return answer
        except:
            pass
            
        return None


class XMLResponseParser(FormatParser):
    """Parser for XML responses."""
    
    def extract_answer(self, response_text: str) -> Optional[str]:
        # Try to find XML block
        xml_block_pattern = r"```xml\s*(.*?)\s*```"
        xml_match = re.search(xml_block_pattern, response_text, re.DOTALL | re.IGNORECASE)
        
        if xml_match:
            xml_text = xml_match.group(1)
        else:
            xml_text = response_text
            
        # Extract answer from XML
        answer_pattern = r"<answer>\s*([A-D])\s*</answer>"
        answer_match = re.search(answer_pattern, xml_text, re.IGNORECASE)
        
        if answer_match:
            return answer_match.group(1).upper()
            
        return None

