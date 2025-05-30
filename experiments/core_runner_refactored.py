# experiments/core_runner_refactored.py
"""
Refactored core runner using the new modular components.
"""
import uuid
from typing import Dict, List, Optional, Any, Tuple
from formatters import PromptFormatter
from parsers import ResponseParser
from api_clients import APIClientFactory, LLMClient


class ExperimentRunner:
    """Orchestrates experiment execution with clean separation of concerns."""
    
    def __init__(self, model_family: str):
        self.formatter = PromptFormatter()
        self.parser = ResponseParser()
        self.api_client = APIClientFactory.create(model_family)
        if not self.api_client:
            raise ValueError(f"Failed to create API client for {model_family}")
    
    def run_single_trial(self,
                        data_item: Dict,
                        option_order: List[str],
                        language: str,
                        model_name: str,
                        input_format: str,
                        output_format: str,
                        subtask: str,
                        question_index: int) -> Dict:
        """Run a single trial and return structured result."""
        
        # Format the prompt
        prompt = self.formatter.format_prompt(
            data_item, option_order, language, input_format, output_format
        )
        
        if not prompt:
            return self._create_error_result(
                data_item, subtask, language, model_name,
                input_format, output_format, option_order, question_index,
                "Failed to format prompt"
            )
        
        # Call API
        raw_response, api_success = self.api_client.call(prompt, model_name)
        
        # Extract text from response
        response_text = None
        if api_success and raw_response:
            response_text = self.api_client.extract_text(raw_response)
        
        # Parse response
        extracted_answer = None
        if response_text:
            extracted_answer = self.parser.parse(response_text, output_format)
        
        # Structure result
        return self._structure_result(
            data_item=data_item,
            subtask=subtask,
            language=language,
            model_name=model_name,
            input_format=input_format,
            output_format=output_format,
            option_permutation=option_order,
            api_raw_response=raw_response,
            api_call_successful=api_success,
            extracted_answer=extracted_answer,
            question_index=question_index,
            api_response_text=response_text
        )
    
    def _structure_result(self, **kwargs) -> Dict:
        """Structure the result maintaining original format."""
        data_item = kwargs['data_item']
        option_permutation = kwargs['option_permutation']
        extracted_answer = kwargs['extracted_answer']
        api_call_successful = kwargs['api_call_successful']
        
        # Get ground truth
        ground_truth_label = data_item.get('answer_label', 'UNKNOWN')
        
        # Map extracted answer to original label
        model_choice_original_label = None
        if api_call_successful and extracted_answer in ['A', 'B', 'C', 'D']:
            try:
                choice_index = ord(extracted_answer) - ord('A')
                if 0 <= choice_index < len(option_permutation):
                    model_choice_original_label = option_permutation[choice_index]
            except Exception:
                model_choice_original_label = "ERROR_MAP"
        
        # Determine correctness
        is_correct = None
        if (model_choice_original_label and 
            model_choice_original_label not in ["ERROR_MAP", "INVALID_EXT"] and
            ground_truth_label not in ["UNKNOWN", "ERROR_GT"]):
            is_correct = (model_choice_original_label == ground_truth_label)
        
        # Build result dict
        return {
            "trial_id": str(uuid.uuid4()),
            "question_id": data_item.get('id', f"idx_{kwargs['question_index']}"),
            "question_index": kwargs['question_index'],
            "subtask": kwargs['subtask'],
            "language": kwargs['language'],
            "model_name": kwargs['model_name'],
            "input_format": kwargs['input_format'],
            "output_format": kwargs['output_format'],
            "option_permutation": "".join(option_permutation),
            "api_call_successful": api_call_successful,
            "extracted_answer": extracted_answer,
            "model_choice_original_label": model_choice_original_label,
            "log_probabilities": None,
            "ground_truth_answer": ground_truth_label,
            "is_correct": is_correct,
            "api_response_text": kwargs.get('api_response_text'),
            "api_raw_response": str(kwargs['api_raw_response']) if kwargs['api_raw_response'] else None
        }
    
    def _create_error_result(self, data_item, subtask, language, model_name,
                           input_format, output_format, option_permutation,
                           question_index, error_msg) -> Dict:
        """Create an error result maintaining the expected format."""
        return self._structure_result(
            data_item=data_item,
            subtask=subtask,
            language=language,
            model_name=model_name,
            input_format=input_format,
            output_format=output_format,
            option_permutation=option_permutation,
            api_raw_response=None,
            api_call_successful=False,
            extracted_answer=None,
            question_index=question_index,
            api_response_text=error_msg
        )