#!/usr/bin/env python3
"""
Phase 2: Batch Runner with Retry Logic
Run complete experiments with automatic retry for failures
"""

import json
import time
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from single_question import (
    run_single_experiment,
    load_question,
    Question,
    ExperimentResult
)


@dataclass
class ExperimentConfig:
    """Configuration for a batch experiment"""
    subtask: str
    model_name: str
    language: str
    input_format: str
    output_format: str
    permutation_type: str  # 'circular' or 'factorial'
    num_questions: int = 100
    start_question: int = 0
    
    def get_experiment_id(self) -> str:
        """Generate unique experiment ID"""
        # Include num_questions and start_question to make each run unique
        base_id = f"{self.subtask}_{self.model_name}_{self.language}_i{self.input_format}_o{self.output_format}_{self.permutation_type}"
        
        # Add question range if not default (100 questions starting at 0)
        if self.num_questions != 100 or self.start_question != 0:
            base_id += f"_q{self.start_question}-{self.start_question + self.num_questions - 1}"
        
        return base_id


class ExperimentStatus:
    """Track experiment progress"""
    def __init__(self, config: ExperimentConfig):
        self.config = config
        self.total_expected = self._calculate_total()
        self.completed = 0
        self.failed = 0
        self.pending_retry = {}  # task_id -> retry_count
        self.start_time = datetime.now()
        
        # Create status directory
        self.status_dir = Path("v2_results") / config.get_experiment_id()
        self.status_dir.mkdir(parents=True, exist_ok=True)
        
        # Subdirectories
        self.completed_dir = self.status_dir / "completed"
        self.pending_dir = self.status_dir / "pending"
        self.completed_dir.mkdir(exist_ok=True)
        self.pending_dir.mkdir(exist_ok=True)
        
        # Load existing status if resuming
        self._load_status()
    
    def _calculate_total(self) -> int:
        """Calculate total number of API calls needed"""
        num_perms = 4 if self.config.permutation_type == 'circular' else 24
        return self.config.num_questions * num_perms
    
    def _load_status(self):
        """Load existing status if resuming an experiment"""
        status_file = self.status_dir / "status.json"
        if status_file.exists():
            with open(status_file, 'r') as f:
                data = json.load(f)
                self.completed = data.get('completed', 0)
                self.failed = data.get('failed', 0)
                self.pending_retry = data.get('pending_retry', {})
                print(f"Resuming experiment: {self.completed}/{self.total_expected} completed")
    
    def save_status(self):
        """Save current status to file"""
        status_file = self.status_dir / "status.json"
        status_data = {
            'config': asdict(self.config),
            'total_expected': self.total_expected,
            'completed': self.completed,
            'failed': self.failed,
            'pending_retry': self.pending_retry,
            'start_time': self.start_time.isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        
        with open(status_file, 'w') as f:
            json.dump(status_data, f, indent=2)
    
    def mark_completed(self, task_id: str):
        """Mark a task as completed"""
        self.completed += 1
        if task_id in self.pending_retry:
            del self.pending_retry[task_id]
        self.save_status()
    
    def mark_failed(self, task_id: str):
        """Mark a task as failed, add to retry queue"""
        if task_id not in self.pending_retry:
            self.pending_retry[task_id] = 0
        self.pending_retry[task_id] += 1
        self.save_status()
    
    def get_progress_str(self) -> str:
        """Get formatted progress string"""
        percent = (self.completed / self.total_expected * 100) if self.total_expected > 0 else 0
        elapsed = datetime.now() - self.start_time
        
        return (f"Progress: {self.completed}/{self.total_expected} ({percent:.1f}%) | "
                f"Pending: {len(self.pending_retry)} | "
                f"Elapsed: {elapsed}")


def get_permutations(perm_type: str) -> List[List[int]]:
    """Get permutations based on type"""
    if perm_type == 'circular':
        return [
            [0, 1, 2, 3],  # ABCD
            [3, 0, 1, 2],  # DABC
            [2, 3, 0, 1],  # CDAB
            [1, 2, 3, 0],  # BCDA
        ]
    else:  # factorial
        import itertools
        return list(itertools.permutations([0, 1, 2, 3]))


def create_task_id(question_idx: int, perm_idx: int) -> str:
    """Create unique task ID"""
    return f"q{question_idx}_p{perm_idx}"


def parse_task_id(task_id: str) -> Tuple[int, int]:
    """Parse task ID back to indices"""
    parts = task_id.split('_')
    q_idx = int(parts[0][1:])
    p_idx = int(parts[1][1:])
    return q_idx, p_idx


def run_batch_experiment(config: ExperimentConfig, api_key: str, max_retries: int = 3):
    """Run a complete batch experiment with retry logic"""
    
    print(f"\n{'='*60}")
    print(f"Starting Batch Experiment")
    print(f"{'='*60}")
    print(f"Config: {config.get_experiment_id()}")
    print(f"Questions: {config.start_question} to {config.start_question + config.num_questions - 1}")
    print(f"Permutations: {config.permutation_type}")
    print(f"{'='*60}\n")
    
    # Initialize status tracking
    status = ExperimentStatus(config)
    
    # Get permutations
    permutations = get_permutations(config.permutation_type)
    
    # Generate all tasks
    all_tasks = []
    for q_idx in range(config.start_question, config.start_question + config.num_questions):
        for p_idx, perm in enumerate(permutations):
            task_id = create_task_id(q_idx, p_idx)
            
            # Skip if already completed
            completed_file = status.completed_dir / f"{task_id}.json"
            if completed_file.exists():
                continue
                
            all_tasks.append((task_id, q_idx, p_idx, perm))
    
    print(f"Tasks to run: {len(all_tasks)}")
    
    # Process all tasks
    for task_idx, (task_id, q_idx, p_idx, perm) in enumerate(all_tasks):
        
        # Check if this is a retry
        retry_count = status.pending_retry.get(task_id, 0)
        if retry_count >= max_retries:
            print(f"\n[{task_idx+1}/{len(all_tasks)}] Skipping {task_id} - max retries exceeded")
            continue
        
        print(f"\n[{task_idx+1}/{len(all_tasks)}] Running {task_id} (retry: {retry_count})")
        
        try:
            # Run the experiment
            result = run_single_experiment(
                model_name=config.model_name,
                api_key=api_key,
                subtask=config.subtask,
                question_idx=q_idx,
                permutation=perm,
                input_format=config.input_format,
                output_format=config.output_format,
                language=config.language
            )
            
            # Check if successful
            if result.error:
                print(f"  ❌ API Error: {result.error}")
                # Save to pending
                pending_file = status.pending_dir / f"{task_id}.json"
                with open(pending_file, 'w') as f:
                    json.dump({
                        'task_id': task_id,
                        'question_idx': q_idx,
                        'permutation_idx': p_idx,
                        'permutation': perm,
                        'error': result.error,
                        'retry_count': retry_count + 1
                    }, f, indent=2)
                status.mark_failed(task_id)
                
            else:
                # Save successful result
                completed_file = status.completed_dir / f"{task_id}.json"
                with open(completed_file, 'w') as f:
                    json.dump(asdict(result), f, indent=2)
                
                # Remove from pending if it was there
                pending_file = status.pending_dir / f"{task_id}.json"
                if pending_file.exists():
                    pending_file.unlink()
                
                status.mark_completed(task_id)
                
                # Quick summary
                print(f"  ✅ Parsed: {result.parsed_answer}, Correct: {result.is_correct}")
            
            # Progress update every 10 tasks
            if (task_idx + 1) % 10 == 0:
                print(f"\n{status.get_progress_str()}\n")
            
            # Rate limiting
            time.sleep(2)
            
        except KeyboardInterrupt:
            print("\n\nExperiment interrupted by user")
            print(status.get_progress_str())
            break
            
        except Exception as e:
            print(f"  ❌ Unexpected error: {e}")
            status.mark_failed(task_id)
    
    # Final status
    print(f"\n{'='*60}")
    print("Experiment Complete")
    print(f"{'='*60}")
    print(status.get_progress_str())
    
    # Generate final output if all completed
    if status.completed == status.total_expected:
        generate_final_output(status)


def retry_pending_tasks(experiment_id: str, api_key: str):
    """Retry all pending tasks for an experiment"""
    
    status_dir = Path("v2_results") / experiment_id
    status_file = status_dir / "status.json"
    
    if not status_file.exists():
        print(f"No experiment found: {experiment_id}")
        return
    
    # Load config
    with open(status_file, 'r') as f:
        data = json.load(f)
        config_dict = data['config']
        config = ExperimentConfig(**config_dict)
    
    # Load status
    status = ExperimentStatus(config)
    
    print(f"\nRetrying {len(status.pending_retry)} pending tasks...")
    
    # Get pending tasks
    pending_files = list(status.pending_dir.glob("*.json"))
    
    for pending_file in pending_files:
        with open(pending_file, 'r') as f:
            task_data = json.load(f)
        
        task_id = task_data['task_id']
        q_idx = task_data['question_idx']
        perm = task_data['permutation']
        
        print(f"\nRetrying {task_id}...")
        
        result = run_single_experiment(
            model_name=config.model_name,
            api_key=api_key,
            subtask=config.subtask,
            question_idx=q_idx,
            permutation=perm,
            input_format=config.input_format,
            output_format=config.output_format,
            language=config.language
        )
        
        if not result.error:
            # Success! Move to completed
            completed_file = status.completed_dir / f"{task_id}.json"
            with open(completed_file, 'w') as f:
                json.dump(asdict(result), f, indent=2)
            
            pending_file.unlink()
            status.mark_completed(task_id)
            print(f"  ✅ Success!")
        else:
            # Still failing
            status.mark_failed(task_id)
            print(f"  ❌ Still failing: {result.error}")
        
        time.sleep(2)
    
    print(f"\nRetry complete. {status.get_progress_str()}")


def generate_final_output(status: ExperimentStatus):
    """Generate final JSONL output for HuggingFace"""
    
    print("\nGenerating final output...")
    
    # Collect all completed results
    all_results = []
    
    for completed_file in sorted(status.completed_dir.glob("*.json")):
        with open(completed_file, 'r') as f:
            result = json.load(f)
            all_results.append(result)
    
    # Sort by question and permutation
    all_results.sort(key=lambda x: (x['question_id'], str(x['permutation'])))
    
    # Write to final JSONL
    final_file = status.status_dir / "final.jsonl"
    with open(final_file, 'w') as f:
        for result in all_results:
            f.write(json.dumps(result) + '\n')
    
    print(f"Final results saved to: {final_file}")
    print(f"Total records: {len(all_results)}")


def reset_experiment(experiment_id: str):
    """Reset an experiment by clearing pending retries"""
    
    status_dir = Path("v2_results") / experiment_id
    status_file = status_dir / "status.json"
    
    if not status_file.exists():
        print(f"No experiment found: {experiment_id}")
        return
    
    # Load status
    with open(status_file, 'r') as f:
        data = json.load(f)
    
    # Clear pending retries
    data['pending_retry'] = {}
    
    # Save updated status
    with open(status_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Clear pending directory
    pending_dir = status_dir / "pending"
    if pending_dir.exists():
        for file in pending_dir.glob("*.json"):
            file.unlink()
    
    print(f"Reset experiment: {experiment_id}")
    print(f"Cleared all pending retries")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run batch experiments")
    parser.add_argument("action", choices=["run", "retry", "status", "reset"], 
                       help="Action to perform")
    parser.add_argument("--subtask", help="Subtask to run")
    parser.add_argument("--model", default="gemini-2.0-flash-lite", 
                       help="Model name")
    parser.add_argument("--language", default="en", choices=["en", "fr"],
                       help="Language")
    parser.add_argument("--input-format", default="base", 
                       choices=["base", "json", "xml"],
                       help="Input format")
    parser.add_argument("--output-format", default="base",
                       choices=["base", "json", "xml"], 
                       help="Output format")
    parser.add_argument("--permutation", default="circular",
                       choices=["circular", "factorial"],
                       help="Permutation type")
    parser.add_argument("--num-questions", type=int, default=5,
                       help="Number of questions to test")
    parser.add_argument("--start-question", type=int, default=0,
                       help="Starting question index")
    parser.add_argument("--experiment-id", help="Experiment ID for retry/status/reset")
    
    args = parser.parse_args()
    
    # Load API key
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    API_KEY = os.getenv("GOOGLE_API_KEY", "")
    if not API_KEY:
        print("Please set GOOGLE_API_KEY in .env file")
        return
    
    if args.action == "run":
        if not args.subtask:
            print("Please specify --subtask")
            return
            
        config = ExperimentConfig(
            subtask=args.subtask,
            model_name=args.model,
            language=args.language,
            input_format=args.input_format,
            output_format=args.output_format,
            permutation_type=args.permutation,
            num_questions=args.num_questions,
            start_question=args.start_question
        )
        
        run_batch_experiment(config, API_KEY)
        
    elif args.action == "retry":
        if not args.experiment_id:
            print("Please specify --experiment-id")
            return
        
        retry_pending_tasks(args.experiment_id, API_KEY)
    
    elif args.action == "reset":
        if not args.experiment_id:
            print("Please specify --experiment-id")
            return
        
        reset_experiment(args.experiment_id)
        
    elif args.action == "status":
        if not args.experiment_id:
            # Show all experiments
            results_dir = Path("v2_results")
            if results_dir.exists():
                print("\nAvailable experiments:")
                for exp_dir in results_dir.iterdir():
                    if exp_dir.is_dir() and (exp_dir / "status.json").exists():
                        with open(exp_dir / "status.json", 'r') as f:
                            data = json.load(f)
                            total = data['total_expected']
                            completed = data['completed']
                            pending = len(data['pending_retry'])
                            print(f"  {exp_dir.name}: {completed}/{total} ({pending} pending)")
        else:
            # Show specific experiment
            status_dir = Path("v2_results") / args.experiment_id
            status_file = status_dir / "status.json"
            
            if status_file.exists():
                with open(status_file, 'r') as f:
                    data = json.load(f)
                    print(f"\nExperiment: {args.experiment_id}")
                    print(f"Total: {data['total_expected']}")
                    print(f"Completed: {data['completed']}")
                    print(f"Pending: {len(data['pending_retry'])}")
                    print(f"Started: {data['start_time']}")
                    print(f"Updated: {data['last_updated']}")


if __name__ == "__main__":
    main()