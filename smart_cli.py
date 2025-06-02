#!/usr/bin/env python3
"""
Smart CLI for MMMLU Order Sensitivity Experiments
Uses the new single JSON approach
"""

import argparse
import os
import json
from pathlib import Path
import sys
from datetime import datetime

# Add project directory to path
sys.path.append(str(Path(__file__).parent))

from smart_runner import run_smart_experiment
from test_single_question_all_settings import test_all_settings


def run_command(args):
    """Run experiments with the smart runner"""
    from dotenv import load_dotenv
    
    # Load API keys
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    # Get API key based on model
    if "gemini" in args.model:
        api_key = os.getenv("GOOGLE_API_KEY", "")
        if not api_key:
            print("Error: GOOGLE_API_KEY not found in .env file")
            sys.exit(1)
    else:
        api_key = os.getenv("MISTRAL_API_KEY", "")
        if not api_key:
            print("Error: MISTRAL_API_KEY not found in .env file")
            sys.exit(1)
    
    # Parse subtasks
    subtasks = args.subtask.split(',') if ',' in args.subtask else [args.subtask]
    
    # Parse languages
    languages = []
    if args.en:
        languages.append("en")
    if args.fr:
        languages.append("fr")
    if not languages:
        languages = ["en"]  # Default to English
    
    # Parse formats
    if args.format == "all":
        format_pairs = [
            ("base", "base"),
            ("base", "json"),
            ("base", "xml"),
            ("json", "base"),
            ("xml", "base")
        ]
    else:
        if '/' in args.format:
            in_fmt, out_fmt = args.format.split('/')
        else:
            in_fmt = out_fmt = args.format
        format_pairs = [(in_fmt, out_fmt)]
    
    # Calculate total experiments
    total_experiments = len(subtasks) * len(languages) * len(format_pairs)
    print(f"\n🚀 Starting {total_experiments} experiments")
    print(f"Subtasks: {', '.join(subtasks)}")
    print(f"Languages: {', '.join(languages)}")
    print(f"Formats: {', '.join([f'{i}/{o}' for i, o in format_pairs])}")
    print(f"Questions per experiment: {args.num_questions}")
    
    if args.dry_run:
        print("\n(Dry run - not executing)")
        return
    
    # Run experiments
    experiment_count = 0
    for subtask in subtasks:
        for language in languages:
            for in_fmt, out_fmt in format_pairs:
                experiment_count += 1
                print(f"\n[{experiment_count}/{total_experiments}] "
                      f"{subtask} - {args.model} - {language} - {in_fmt}/{out_fmt}")
                
                run_smart_experiment(
                    subtask=subtask.strip(),
                    model_name=args.model,
                    api_key=api_key,
                    language=language,
                    input_format=in_fmt,
                    output_format=out_fmt,
                    num_questions=args.num_questions,
                    start_question=args.start_question
                )


def status_command(args):
    """Show status of experiments"""
    results_dir = Path("results")
    
    if not results_dir.exists():
        print("No experiments found")
        return
    
    # Get all summary files
    summary_files = list(results_dir.glob("*_summary.json"))
    
    if not summary_files:
        print("No experiments found")
        return
    
    print(f"\n{'='*80}")
    print(f"{'Experiment':<50} {'Status':<12} {'Progress':<18}")
    print(f"{'='*80}")
    
    total_stats = {"running": 0, "completed": 0, "total_tasks": 0, "completed_tasks": 0}
    
    for summary_file in sorted(summary_files):
        try:
            with open(summary_file, 'r') as f:
                data = json.load(f)
            
            exp_name = summary_file.stem.replace("_summary", "")
            status = data.get("status", "unknown")
            completed = data.get("completed", 0)
            total = data.get("total_expected", 0)
            abandoned = data.get("abandoned", 0)
            
            # Calculate progress
            progress_pct = (completed / total * 100) if total > 0 else 0
            progress_str = f"{completed}/{total} ({progress_pct:.1f}%)"
            
            # Add abandoned info if any
            if abandoned > 0:
                progress_str += f" [{abandoned} abandoned]"
            
            # Status emoji
            status_emoji = "✅" if status == "completed" else "🔄"
            
            print(f"{exp_name:<50} {status_emoji} {status:<10} {progress_str:<18}")
            
            # Update totals
            if status == "running":
                total_stats["running"] += 1
            else:
                total_stats["completed"] += 1
            total_stats["total_tasks"] += total
            total_stats["completed_tasks"] += completed
            
        except Exception as e:
            print(f"{summary_file.stem:<50} ❌ Error reading file")
    
    # Print summary
    print(f"{'='*80}")
    print(f"Summary: {total_stats['completed']} completed, {total_stats['running']} running")
    print(f"Total progress: {total_stats['completed_tasks']}/{total_stats['total_tasks']} tasks")
    
    # If specific experiment requested, show details
    if args.experiment:
        summary_file = results_dir / f"{args.experiment}_summary.json"
        data_file = results_dir / f"{args.experiment}.jsonl"
        
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                data = json.load(f)
            
            print(f"\n{'='*60}")
            print(f"Details for: {args.experiment}")
            print(f"{'='*60}")
            
            # Show configuration
            for key in ["subtask", "model", "language", "input_format", "output_format", 
                       "num_questions", "total_expected", "completed", "abandoned"]:
                if key in data:
                    print(f"{key}: {data[key]}")
            
            # Show file sizes
            if data_file.exists():
                size_mb = data_file.stat().st_size / (1024 * 1024)
                print(f"\nData file size: {size_mb:.2f} MB")
                
                # Count lines
                with open(data_file, 'r') as f:
                    line_count = sum(1 for _ in f)
                print(f"Total records: {line_count}")
            
            # Show abandoned tasks
            if data.get("abandoned_tasks"):
                print(f"\nAbandoned tasks ({len(data['abandoned_tasks'])}):")
                for task_id, info in list(data["abandoned_tasks"].items())[:5]:
                    print(f"  {task_id}: {info['final_error']}")
                if len(data["abandoned_tasks"]) > 5:
                    print(f"  ... and {len(data['abandoned_tasks']) - 5} more")


def test_command(args):
    """Run tests"""
    if args.type == "single":
        # Test single question across all settings
        from test_single_question_all_settings import test_all_settings
        test_all_settings(args.subtask, args.question)
    elif args.type == "failures":
        # Test failure handling
        from test_failure_handling import test_failure_handling
        test_failure_handling()
    elif args.type == "data":
        # Test complete data saving
        from single_question import test_single_question
        test_single_question()
    else:
        print("Please specify test type: --type single, --type failures, or --type data")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Smart CLI for MMMLU Order Sensitivity Experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run single subtask with 5 questions
  python smart_cli.py run --subtask abstract_algebra --num-questions 5
  
  # Run multiple subtasks with all formats
  python smart_cli.py run --subtask abstract_algebra,anatomy --format all
  
  # Run French experiments
  python smart_cli.py run --subtask formal_logic --fr --format base/json
  
  # Check status
  python smart_cli.py status
  
  # Check specific experiment
  python smart_cli.py status --experiment abstract_algebra_gemini-2.0-flash-lite_en_ibase_obase
  
  # Test single question across all settings
  python smart_cli.py test --type single --subtask anatomy
  
  # Test failure handling
  python smart_cli.py test --type failures
  
  # Test complete data saving
  python smart_cli.py test --type data

Output Files:
  - {experiment_id}.jsonl: Complete data (one line per API call)
  - {experiment_id}_summary.json: Summary and progress tracking
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run experiments')
    run_parser.add_argument('--subtask', required=True,
                          help='Subtask(s) to run (comma-separated)')
    run_parser.add_argument('--model', default='gemini-2.0-flash-lite',
                          help='Model name')
    run_parser.add_argument('--en', action='store_true', help='Run English')
    run_parser.add_argument('--fr', action='store_true', help='Run French')
    run_parser.add_argument('--format', default='base/base',
                          help='Format: base/base, json/base, all, etc.')
    run_parser.add_argument('--num-questions', type=int, default=100,
                          help='Number of questions')
    run_parser.add_argument('--start-question', type=int, default=0,
                          help='Starting question index')
    run_parser.add_argument('--dry-run', action='store_true',
                          help='Show what would run without executing')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show experiment status')
    status_parser.add_argument('--experiment', help='Show details for specific experiment')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run tests')
    test_parser.add_argument('--type', choices=['single', 'failures', 'data'],
                           help='Test type')
    test_parser.add_argument('--subtask', default='abstract_algebra',
                           help='Subtask for testing')
    test_parser.add_argument('--question', type=int, default=0,
                           help='Question index for testing')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    if args.command == 'run':
        run_command(args)
    elif args.command == 'status':
        status_command(args)
    elif args.command == 'test':
        test_command(args)


if __name__ == "__main__":
    main()