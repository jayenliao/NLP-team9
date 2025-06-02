#!/usr/bin/env python3
"""
Smart Experiment Runner with JSONL output and complete data storage
Saves ALL API responses and experimental data as required

Output format:
- {experiment_id}.jsonl: Complete results, one JSON object per line (one per API call)
- {experiment_id}_summary.json: Summary statistics and progress tracking

Each line in the JSONL file contains:
- Complete prompt sent
- Full API response (raw and text)
- Parsing results and mapping
- Timing information
- Error details if any
- All question and permutation details
"""

import json
import time
import os
import uuid
import importlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import sys

# Add project directory to path
sys.path.append(str(Path(__file__).parent))

# Force reload of single_question module to get latest changes
import importlib
if 'single_question' in sys.modules:
    importlib.reload(sys.modules['single_question'])

from single_question import run_single_experiment
from format_handlers import Question


class SmartExperimentRunner:
    """Runner that saves complete data in JSONL format"""
    
    def __init__(self, 
                 subtask: str,
                 model_name: str,
                 api_key: str,
                 language: str,
                 input_format: str,
                 output_format: str,
                 num_questions: int = 100,
                 start_question: int = 0):
        
        self.subtask = subtask
        self.model_name = model_name
        self.api_key = api_key
        self.language = language
        self.input_format = input_format
        self.output_format = output_format
        self.num_questions = num_questions
        self.start_question = start_question
        
        # Experiment ID
        self.experiment_id = f"{subtask}_{model_name}_{language}_i{input_format}_o{output_format}"
        
        # File paths
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        
        # JSONL file for complete results (one line per API call)
        self.results_file = self.results_dir / f"{self.experiment_id}.jsonl"
        
        # Summary JSON file for quick status checking
        self.summary_file = self.results_dir / f"{self.experiment_id}_summary.json"
        
        # Permutations (circular only for now)
        self.permutations = [
            [0, 1, 2, 3],  # ABCD
            [3, 0, 1, 2],  # DABC
            [2, 3, 0, 1],  # CDAB
            [1, 2, 3, 0],  # BCDA
        ]
        
        # Load or create summary
        self.summary = self._load_or_create_summary()
        
        # Track current session stats
        self.session_stats = {
            "started": datetime.now().isoformat(),
            "completed": 0,
            "failed": 0,
            "retried": 0
        }
    
    def _load_or_create_summary(self) -> dict:
        """Load existing summary or create new one"""
        if self.summary_file.exists():
            with open(self.summary_file, 'r') as f:
                summary = json.load(f)
            
            # Check if experiment parameters have changed
            expected_total = self.num_questions * len(self.permutations)
            if summary.get("total_expected") != expected_total:
                print(f"⚠️  Experiment parameters changed (was {summary.get('total_expected')} tasks, now {expected_total})")
                summary["total_expected"] = expected_total
                summary["num_questions"] = self.num_questions
                
            return summary
        
        # Create new summary
        total_tasks = self.num_questions * len(self.permutations)
        return {
            "experiment_id": self.experiment_id,
            "subtask": self.subtask,
            "model": self.model_name,
            "language": self.language,
            "input_format": self.input_format,
            "output_format": self.output_format,
            "num_questions": self.num_questions,
            "start_question": self.start_question,
            "created_at": datetime.now().isoformat(),
            "status": "running",
            "total_expected": total_tasks,
            "completed": 0,
            "failed": 0,
            "abandoned": 0,
            "retry_queue": {},
            "abandoned_tasks": {},
            "completed_tasks": set()  # Will be converted to list for JSON
        }
    
    def _save_summary(self):
        """Save summary to file"""
        # Convert set to list for JSON serialization
        summary_to_save = self.summary.copy()
        summary_to_save["completed_tasks"] = list(self.summary.get("completed_tasks", set()))
        
        with open(self.summary_file, 'w') as f:
            json.dump(summary_to_save, f, indent=2)
    
    def _append_result(self, result: dict):
        """Append a result to the JSONL file"""
        with open(self.results_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + '\n')
    
    def _get_task_id(self, question_idx: int, perm_idx: int) -> str:
        """Generate task ID"""
        return f"q{question_idx}_p{perm_idx}"
    
    def _is_task_completed(self, task_id: str) -> bool:
        """Check if task is already completed"""
        completed_tasks = set(self.summary.get("completed_tasks", []))
        return task_id in completed_tasks
    
    def _mark_task_completed(self, task_id: str):
        """Mark a task as completed in summary"""
        if isinstance(self.summary.get("completed_tasks"), list):
            self.summary["completed_tasks"] = set(self.summary["completed_tasks"])
        self.summary["completed_tasks"].add(task_id)
        self.summary["completed"] = len(self.summary["completed_tasks"])
    
    def run(self):
        """Run the experiment"""
        print(f"\n{'='*60}")
        print(f"Starting Smart Experiment: {self.experiment_id}")
        print(f"{'='*60}")
        print(f"Questions: {self.start_question} to {self.start_question + self.num_questions - 1}")
        print(f"Total tasks: {self.summary['total_expected']}")
        print(f"Output: {self.results_file}")
        print(f"{'='*60}\n")
        
        # Phase 1: Initial run through all tasks
        print("Phase 1: Initial run")
        self._run_all_tasks()
        
        # Phase 2: Retry failed tasks once
        if self.summary.get("retry_queue"):
            print(f"\nPhase 2: Retrying {len(self.summary['retry_queue'])} failed tasks")
            time.sleep(30)  # Wait 30 seconds before retry
            self._retry_failed_tasks()
        
        # Mark experiment as completed
        self.summary["status"] = "completed"
        self.summary["completed_at"] = datetime.now().isoformat()
        self._save_summary()
        
        # Print final summary
        self._print_summary()
    
    def _run_all_tasks(self):
        """Run through all tasks once"""
        task_count = 0
        total_tasks = self.num_questions * len(self.permutations)  # Calculate fresh, don't use summary
        
        for q_idx in range(self.start_question, self.start_question + self.num_questions):
            for p_idx, permutation in enumerate(self.permutations):
                task_count += 1
                task_id = self._get_task_id(q_idx, p_idx)
                
                # Skip if already completed
                if self._is_task_completed(task_id):
                    print(f"[{task_count}/{total_tasks}] Skipping {task_id} (already completed)")
                    continue
                
                print(f"[{task_count}/{total_tasks}] Running {task_id}...", end=" ")
                
                try:
                    # Run the experiment
                    result = run_single_experiment(
                        model_name=self.model_name,
                        api_key=self.api_key,
                        subtask=self.subtask,
                        question_idx=q_idx,
                        permutation=permutation,
                        input_format=self.input_format,
                        output_format=self.output_format,
                        language=self.language
                    )
                    
                    # Convert result to dict and add task_id
                    result_dict = asdict(result)
                    result_dict["task_id"] = task_id
                    
                    # Save the complete result
                    self._append_result(result_dict)
                    
                    # Update summary based on success/failure
                    if result.error:
                        # API error
                        print(f"❌ API Error: {result.error}")
                        self.summary["retry_queue"][task_id] = {
                            "attempts": 1,
                            "last_error": result.error,
                            "question_idx": q_idx,
                            "perm_idx": p_idx
                        }
                        self.session_stats["failed"] += 1
                    elif not result.parsed_answer:
                        # Parse error
                        print(f"❌ Parse Error")
                        self.summary["retry_queue"][task_id] = {
                            "attempts": 1,
                            "last_error": "Failed to parse answer",
                            "question_idx": q_idx,
                            "perm_idx": p_idx
                        }
                        self.session_stats["failed"] += 1
                    else:
                        # Success - use dict to access fields safely
                        original_label = result_dict.get("model_choice_original_label", "?")
                        print(f"✅ Answer: {result.parsed_answer} → {original_label}, Correct: {result.is_correct}")
                        self._mark_task_completed(task_id)
                        self.session_stats["completed"] += 1
                    
                except Exception as e:
                    # Unknown error
                    print(f"❌ Unknown Error: {str(e)}")
                    
                    # Still try to save what we can
                    error_result = {
                        "task_id": task_id,
                        "trial_id": str(uuid.uuid4()),
                        "question_index": q_idx,
                        "subtask": self.subtask,
                        "error": f"Unknown error: {str(e)}",
                        "api_call_successful": False,
                        "timestamp": datetime.now().isoformat()
                    }
                    self._append_result(error_result)
                    
                    self.summary["retry_queue"][task_id] = {
                        "attempts": 1,
                        "last_error": str(e),
                        "question_idx": q_idx,
                        "perm_idx": p_idx
                    }
                    self.session_stats["failed"] += 1
                
                # Save summary periodically
                if task_count % 10 == 0:
                    self._save_summary()
                
                # Rate limiting
                time.sleep(5)
        
        # Final save
        self._save_summary()
    
    def _retry_failed_tasks(self):
        """Retry failed tasks once"""
        import uuid
        
        retry_tasks = list(self.summary["retry_queue"].items())
        
        for task_id, task_info in retry_tasks:
            print(f"Retrying {task_id}...", end=" ")
            
            try:
                # Run the experiment again
                result = run_single_experiment(
                    model_name=self.model_name,
                    api_key=self.api_key,
                    subtask=self.subtask,
                    question_idx=task_info["question_idx"],
                    permutation=self.permutations[task_info["perm_idx"]],
                    input_format=self.input_format,
                    output_format=self.output_format,
                    language=self.language
                )
                
                # Convert result and add metadata
                result_dict = asdict(result)
                result_dict["task_id"] = task_id
                result_dict["retry_attempt"] = 2
                
                # Save the result
                self._append_result(result_dict)
                
                # Check if successful
                if result.error:
                    # Still failing - abandon
                    print(f"❌ Still failing: {result.error}")
                    self.summary["abandoned_tasks"][task_id] = {
                        "attempts": 2,
                        "final_error": result.error,
                        "abandoned_at": datetime.now().isoformat()
                    }
                    del self.summary["retry_queue"][task_id]
                    self.summary["abandoned"] = len(self.summary["abandoned_tasks"])
                    
                elif not result.parsed_answer:
                    # Still can't parse - abandon
                    print(f"❌ Still can't parse")
                    self.summary["abandoned_tasks"][task_id] = {
                        "attempts": 2,
                        "final_error": "Parse error after retry",
                        "abandoned_at": datetime.now().isoformat()
                    }
                    del self.summary["retry_queue"][task_id]
                    self.summary["abandoned"] = len(self.summary["abandoned_tasks"])
                    
                else:
                    # Success on retry!
                    original_label = result_dict.get("model_choice_original_label", "?")
                    print(f"✅ Fixed! Answer: {result.parsed_answer} → {original_label}")
                    self._mark_task_completed(task_id)
                    del self.summary["retry_queue"][task_id]
                    self.session_stats["retried"] += 1
                    
            except Exception as e:
                # Still unknown error - abandon
                print(f"❌ Still unknown error: {str(e)}")
                
                # Save error result
                error_result = {
                    "task_id": task_id,
                    "trial_id": str(uuid.uuid4()),
                    "retry_attempt": 2,
                    "error": f"Unknown error on retry: {str(e)}",
                    "api_call_successful": False,
                    "timestamp": datetime.now().isoformat()
                }
                self._append_result(error_result)
                
                self.summary["abandoned_tasks"][task_id] = {
                    "attempts": 2,
                    "final_error": str(e),
                    "abandoned_at": datetime.now().isoformat()
                }
                del self.summary["retry_queue"][task_id]
                self.summary["abandoned"] = len(self.summary["abandoned_tasks"])
            
            # Save after each retry
            self._save_summary()
            
            # Rate limiting
            time.sleep(5)
        
        # Clear retry queue
        self.summary["failed"] = 0
    
    def _print_summary(self):
        """Print final summary"""
        print(f"\n{'='*60}")
        print(f"EXPERIMENT COMPLETE: {self.experiment_id}")
        print(f"{'='*60}")
        
        total = self.summary["total_expected"]
        completed = self.summary["completed"]
        abandoned = self.summary.get("abandoned", 0)
        success_rate = (completed / total * 100) if total > 0 else 0
        
        print(f"Total tasks: {total}")
        print(f"Completed: {completed} ({success_rate:.2f}%)")
        print(f"Abandoned: {abandoned}")
        
        if abandoned > 0:
            print(f"\nAbandoned tasks:")
            for task_id, info in list(self.summary["abandoned_tasks"].items())[:5]:
                print(f"  {task_id}: {info['final_error']}")
            if abandoned > 5:
                print(f"  ... and {abandoned - 5} more")
        
        print(f"\nSession stats:")
        print(f"  Completed in this run: {self.session_stats['completed']}")
        print(f"  Failed then retried: {self.session_stats['retried']}")
        print(f"  Initially failed: {self.session_stats['failed']}")
        
        print(f"\nResults saved to:")
        print(f"  Data: {self.results_file}")
        print(f"  Summary: {self.summary_file}")


def run_smart_experiment(subtask: str, model_name: str, api_key: str,
                        language: str, input_format: str, output_format: str,
                        num_questions: int = 100, start_question: int = 0):
    """Convenience function to run an experiment"""
    runner = SmartExperimentRunner(
        subtask=subtask,
        model_name=model_name,
        api_key=api_key,
        language=language,
        input_format=input_format,
        output_format=output_format,
        num_questions=num_questions,
        start_question=start_question
    )
    runner.run()


if __name__ == "__main__":
    import argparse
    from dotenv import load_dotenv
    
    parser = argparse.ArgumentParser(description="Run smart experiment")
    parser.add_argument("--subtask", required=True, help="Subtask to run")
    parser.add_argument("--model", default="gemini-2.0-flash-lite", help="Model name")
    parser.add_argument("--language", default="en", choices=["en", "fr"], help="Language")
    parser.add_argument("--input-format", default="base", help="Input format")
    parser.add_argument("--output-format", default="base", help="Output format")
    parser.add_argument("--num-questions", type=int, default=5, help="Number of questions")
    parser.add_argument("--start-question", type=int, default=0, help="Starting question")
    
    args = parser.parse_args()
    
    # Load API key
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    # Determine API key based on model
    if "gemini" in args.model:
        api_key = os.getenv("GOOGLE_API_KEY", "")
    else:
        api_key = os.getenv("MISTRAL_API_KEY", "")
    
    if not api_key:
        print(f"Please set API key for {args.model}")
        sys.exit(1)
    
    # Run experiment
    run_smart_experiment(
        subtask=args.subtask,
        model_name=args.model,
        api_key=api_key,
        language=args.language,
        input_format=args.input_format,
        output_format=args.output_format,
        num_questions=args.num_questions,
        start_question=args.start_question
    )