#!/usr/bin/env python3
"""
Smart Experiment Runner with Single JSON per subtask
Handles failures gracefully without blocking
"""

import json
import time
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import sys

# Add project directory to path
sys.path.append(str(Path(__file__).parent))

from single_question import run_single_experiment
from format_handlers import Question


@dataclass
class TaskResult:
    """Result for a single task"""
    question_id: str
    status: str  # "completed", "failed", "abandoned"
    attempts: int
    result: Optional[dict] = None
    error: Optional[str] = None
    last_attempt: Optional[str] = None
    next_retry: Optional[str] = None


class SmartExperimentRunner:
    """Runner that uses single JSON file per experiment"""
    
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
        
        # Results file
        self.results_dir = Path("results")
        self.results_dir.mkdir(exist_ok=True)
        self.results_file = self.results_dir / f"{self.experiment_id}.json"
        
        # Permutations (circular only for now)
        self.permutations = [
            [0, 1, 2, 3],  # ABCD
            [3, 0, 1, 2],  # DABC
            [2, 3, 0, 1],  # CDAB
            [1, 2, 3, 0],  # BCDA
        ]
        
        # Load existing results if any
        self.data = self._load_or_create_data()
    
    def _load_or_create_data(self) -> dict:
        """Load existing data or create new structure"""
        if self.results_file.exists():
            with open(self.results_file, 'r') as f:
                return json.load(f)
        
        # Create new data structure
        total_tasks = self.num_questions * len(self.permutations)
        return {
            "metadata": {
                "experiment_id": self.experiment_id,
                "subtask": self.subtask,
                "model": self.model_name,
                "language": self.language,
                "input_format": self.input_format,
                "output_format": self.output_format,
                "num_questions": self.num_questions,
                "start_question": self.start_question,
                "start_time": datetime.now().isoformat(),
                "status": "running",
                "total_expected": total_tasks,
                "completed": 0,
                "failed": 0,
                "abandoned": 0
            },
            "retry_queue": {},
            "abandoned": {},
            "results": {}
        }
    
    def _save_data(self):
        """Save current data to file"""
        with open(self.results_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def _get_task_id(self, question_idx: int, perm_idx: int) -> str:
        """Generate task ID"""
        return f"q{question_idx}_p{perm_idx}"
    
    def _update_stats(self):
        """Update metadata statistics"""
        completed = len([r for r in self.data["results"].values() 
                        if r.get("status") == "completed"])
        failed = len(self.data["retry_queue"])
        abandoned = len(self.data["abandoned"])
        
        self.data["metadata"]["completed"] = completed
        self.data["metadata"]["failed"] = failed
        self.data["metadata"]["abandoned"] = abandoned
    
    def run(self):
        """Run the experiment"""
        print(f"\n{'='*60}")
        print(f"Starting Smart Experiment: {self.experiment_id}")
        print(f"{'='*60}")
        print(f"Questions: {self.start_question} to {self.start_question + self.num_questions - 1}")
        print(f"Total tasks: {self.data['metadata']['total_expected']}")
        print(f"{'='*60}\n")
        
        # Phase 1: Initial run through all tasks
        print("Phase 1: Initial run")
        self._run_all_tasks()
        
        # Phase 2: Retry failed tasks once
        if self.data["retry_queue"]:
            print(f"\nPhase 2: Retrying {len(self.data['retry_queue'])} failed tasks")
            time.sleep(30)  # Wait 30 seconds before retry
            self._retry_failed_tasks()
        
        # Mark experiment as completed
        self.data["metadata"]["status"] = "completed"
        self.data["metadata"]["end_time"] = datetime.now().isoformat()
        self._save_data()
        
        # Print final summary
        self._print_summary()
    
    def _run_all_tasks(self):
        """Run through all tasks once"""
        task_count = 0
        total_tasks = self.data["metadata"]["total_expected"]
        
        for q_idx in range(self.start_question, self.start_question + self.num_questions):
            for p_idx, permutation in enumerate(self.permutations):
                task_count += 1
                task_id = self._get_task_id(q_idx, p_idx)
                
                # Skip if already completed
                if task_id in self.data["results"]:
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
                    
                    # Check if successful
                    if result.error:
                        # API error
                        print(f"❌ API Error: {result.error}")
                        self.data["retry_queue"][task_id] = {
                            "attempts": 1,
                            "last_attempt": datetime.now().isoformat(),
                            "next_retry": (datetime.now() + timedelta(seconds=30)).isoformat(),
                            "error": result.error,
                            "question_idx": q_idx,
                            "permutation": permutation
                        }
                    elif not result.parsed_answer:
                        # Parse error
                        print(f"❌ Parse Error")
                        self.data["retry_queue"][task_id] = {
                            "attempts": 1,
                            "last_attempt": datetime.now().isoformat(),
                            "next_retry": (datetime.now() + timedelta(seconds=30)).isoformat(),
                            "error": "Failed to parse answer from response",
                            "question_idx": q_idx,
                            "permutation": permutation,
                            "raw_response": result.raw_response[:200]  # Store first 200 chars
                        }
                    else:
                        # Success
                        print(f"✅ Answer: {result.parsed_answer}, Correct: {result.is_correct}")
                        self.data["results"][task_id] = {
                            "status": "completed",
                            "attempts": 1,
                            "question_id": result.question_id,
                            "parsed_answer": result.parsed_answer,
                            "is_correct": result.is_correct,
                            "timestamp": result.timestamp
                        }
                    
                except Exception as e:
                    # Unknown error
                    print(f"❌ Unknown Error: {str(e)}")
                    self.data["retry_queue"][task_id] = {
                        "attempts": 1,
                        "last_attempt": datetime.now().isoformat(),
                        "next_retry": (datetime.now() + timedelta(seconds=30)).isoformat(),
                        "error": f"Unknown error: {str(e)}",
                        "question_idx": q_idx,
                        "permutation": permutation
                    }
                
                # Update stats and save periodically
                if task_count % 10 == 0:
                    self._update_stats()
                    self._save_data()
                
                # Rate limiting
                time.sleep(1)
        
        # Final save
        self._update_stats()
        self._save_data()
    
    def _retry_failed_tasks(self):
        """Retry failed tasks once"""
        retry_tasks = list(self.data["retry_queue"].items())
        
        for task_id, task_info in retry_tasks:
            print(f"Retrying {task_id}...", end=" ")
            
            try:
                # Run the experiment again
                result = run_single_experiment(
                    model_name=self.model_name,
                    api_key=self.api_key,
                    subtask=self.subtask,
                    question_idx=task_info["question_idx"],
                    permutation=task_info["permutation"],
                    input_format=self.input_format,
                    output_format=self.output_format,
                    language=self.language
                )
                
                # Check if successful
                if result.error:
                    # Still failing - abandon
                    print(f"❌ Still failing: {result.error}")
                    self.data["abandoned"][task_id] = {
                        "attempts": 2,
                        "abandoned_at": datetime.now().isoformat(),
                        "final_error": result.error,
                        "question_idx": task_info["question_idx"],
                        "permutation": task_info["permutation"]
                    }
                    del self.data["retry_queue"][task_id]
                    
                elif not result.parsed_answer:
                    # Still can't parse - abandon
                    print(f"❌ Still can't parse")
                    self.data["abandoned"][task_id] = {
                        "attempts": 2,
                        "abandoned_at": datetime.now().isoformat(),
                        "final_error": "Parse error after retry",
                        "question_idx": task_info["question_idx"],
                        "permutation": task_info["permutation"],
                        "raw_response": result.raw_response[:200]
                    }
                    del self.data["retry_queue"][task_id]
                    
                else:
                    # Success on retry!
                    print(f"✅ Fixed! Answer: {result.parsed_answer}")
                    self.data["results"][task_id] = {
                        "status": "completed",
                        "attempts": 2,
                        "question_id": result.question_id,
                        "parsed_answer": result.parsed_answer,
                        "is_correct": result.is_correct,
                        "timestamp": result.timestamp
                    }
                    del self.data["retry_queue"][task_id]
                    
            except Exception as e:
                # Still unknown error - abandon
                print(f"❌ Still unknown error: {str(e)}")
                self.data["abandoned"][task_id] = {
                    "attempts": 2,
                    "abandoned_at": datetime.now().isoformat(),
                    "final_error": f"Unknown error: {str(e)}",
                    "question_idx": task_info["question_idx"],
                    "permutation": task_info["permutation"]
                }
                del self.data["retry_queue"][task_id]
            
            # Save after each retry
            self._update_stats()
            self._save_data()
            
            # Rate limiting
            time.sleep(1)
    
    def _print_summary(self):
        """Print final summary"""
        print(f"\n{'='*60}")
        print(f"EXPERIMENT COMPLETE: {self.experiment_id}")
        print(f"{'='*60}")
        
        meta = self.data["metadata"]
        total = meta["total_expected"]
        completed = meta["completed"]
        abandoned = meta["abandoned"]
        success_rate = (completed / total * 100) if total > 0 else 0
        
        print(f"Total tasks: {total}")
        print(f"Completed: {completed} ({success_rate:.2f}%)")
        print(f"Abandoned: {abandoned}")
        
        if abandoned > 0:
            print(f"\nAbandoned tasks:")
            for task_id, info in self.data["abandoned"].items():
                print(f"  {task_id}: {info['final_error']}")
        
        print(f"\nResults saved to: {self.results_file}")


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