# cli.py
#!/usr/bin/env python3
"""
Main CLI for MMMLU Order Sensitivity Experiments
"""

import argparse
import os
from pathlib import Path
import sys

# Add v2 directory to path
sys.path.append(str(Path(__file__).parent))

from src.batch_runner import ExperimentConfig, run_batch_experiment, retry_pending_tasks
from src.single_question import run_single_experiment
from src.test_permutations import test_permutations_on_question


def load_api_key(model_family: str) -> str:
    """Load API key for the specified model family"""
    from dotenv import load_dotenv
    
    project_root = Path(__file__).parent.parent
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
    
    if model_family == "gemini":
        key = os.getenv("GOOGLE_API_KEY", "")
        if not key:
            print("Error: GOOGLE_API_KEY not found in .env file")
            sys.exit(1)
    elif model_family == "mistral":
        key = os.getenv("MISTRAL_API_KEY", "")
        if not key:
            print("Error: MISTRAL_API_KEY not found in .env file")
            sys.exit(1)
    else:
        print(f"Error: Unknown model family '{model_family}'")
        sys.exit(1)
    
    return key


def run_subtask(args):
    """Run experiments for specified subtasks"""
    
    # Determine model family from model name
    model_family = "gemini" if "gemini" in args.model else "mistral"
    api_key = load_api_key(model_family)
    
    # Process subtasks
    subtasks = args.subtask.split(',') if ',' in args.subtask else [args.subtask]
    
    for subtask in subtasks:
        subtask = subtask.strip()
        print(f"\n{'='*60}")
        print(f"Running experiments for subtask: {subtask}")
        print(f"{'='*60}")
        
        # Process each input/output format combination
        if args.format == "all":
            format_pairs = [
                ("base", "base"),
                ("base", "json"),
                ("base", "xml"),
                ("json", "base"),
                ("xml", "base")
            ]
        else:
            # Parse single format
            if '/' in args.format:
                in_fmt, out_fmt = args.format.split('/')
            else:
                in_fmt = out_fmt = args.format
            format_pairs = [(in_fmt, out_fmt)]
        
        # Process each language
        languages = []
        if args.en:
            languages.append("en")
        if args.fr:
            languages.append("fr")
        if not languages:
            languages = ["en"]  # Default to English
        
        # Run experiments
        for language in languages:
            for in_fmt, out_fmt in format_pairs:
                config = ExperimentConfig(
                    subtask=subtask,
                    model_name=args.model,
                    language=language,
                    input_format=in_fmt,
                    output_format=out_fmt,
                    permutation_type=args.permutation,
                    num_questions=args.num_questions,
                    start_question=args.start_question
                )
                
                print(f"\nRunning: {config.get_experiment_id()}")
                
                if args.dry_run:
                    print("(Dry run - not executing)")
                else:
                    run_batch_experiment(config, api_key, max_retries=args.max_retries)


def status_command(args):
    """Show status of experiments"""
    from src.batch_runner import ExperimentStatus
    import json
    
    results_dir = Path("v2_results")
    
    if args.experiment_id:
        # Show specific experiment
        exp_dir = results_dir / args.experiment_id
        status_file = exp_dir / "status.json"
        
        if not status_file.exists():
            print(f"Experiment not found: {args.experiment_id}")
            return
        
        with open(status_file, 'r') as f:
            data = json.load(f)
        
        print(f"\nExperiment: {args.experiment_id}")
        print(f"{'='*60}")
        print(f"Total tasks: {data['total_expected']}")
        print(f"Completed: {data['completed']} ({data['completed']/data['total_expected']*100:.1f}%)")
        print(f"Pending retry: {len(data.get('pending_retry', {}))}")
        print(f"Started: {data['start_time']}")
        print(f"Last updated: {data['last_updated']}")
        
        if args.verbose and data.get('pending_retry'):
            print(f"\nPending tasks:")
            for task_id, retry_count in data['pending_retry'].items():
                print(f"  {task_id}: {retry_count} retries")
    
    else:
        # Show all experiments
        if not results_dir.exists():
            print("No experiments found")
            return
        
        experiments = []
        for exp_dir in results_dir.iterdir():
            if exp_dir.is_dir():
                status_file = exp_dir / "status.json"
                if status_file.exists():
                    with open(status_file, 'r') as f:
                        data = json.load(f)
                        experiments.append({
                            'id': exp_dir.name,
                            'total': data['total_expected'],
                            'completed': data['completed'],
                            'pending': len(data.get('pending_retry', {}))
                        })
        
        if not experiments:
            print("No experiments found")
            return
        
        print(f"\n{'Experiment ID':<60} {'Progress':<20} {'Status'}")
        print(f"{'-'*100}")
        
        for exp in sorted(experiments, key=lambda x: x['id']):
            progress = f"{exp['completed']}/{exp['total']}"
            percent = exp['completed'] / exp['total'] * 100
            
            if exp['completed'] == exp['total']:
                status = "✅ Complete"
            elif exp['pending'] > 0:
                status = f"⚠️  {exp['pending']} pending"
            else:
                status = "🔄 In progress"
            
            print(f"{exp['id']:<60} {progress:<20} {status} ({percent:.1f}%)")


def retry_command(args):
    """Retry failed tasks"""
    model_family = "gemini" if "gemini" in args.experiment_id else "mistral"
    api_key = load_api_key(model_family)
    
    retry_pending_tasks(args.experiment_id, api_key)


def reset_command(args):
    """Reset an experiment"""
    from src.batch_runner import reset_experiment
    reset_experiment(args.experiment_id)


def test_command(args):
    """Run tests"""
    if args.permutations:
        # Test permutation logic
        test_permutations_on_question(
            subtask=args.subtask or "abstract_algebra",
            question_idx=args.question or 0
        )
    elif args.formats:
        # Test format handling
        import subprocess
        subprocess.run([sys.executable, "test_all_formats.py", "--all"])
    else:
        print("Please specify --permutations or --formats")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="MMMLU Order Sensitivity Experiments",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run experiments for one subtask
  python cli.py run --subtask abstract_algebra
  
  # Run multiple subtasks
  python cli.py run --subtask abstract_algebra,anatomy,astronomy
  
  # Run with specific format
  python cli.py run --subtask formal_logic --format json/base
  
  # Run all formats in French
  python cli.py run --subtask anatomy --format all --fr
  
  # Run deep dive with factorial permutations
  python cli.py run --subtask formal_logic --permutation factorial --num-questions 5
  
  # Check status
  python cli.py status
  
  # Retry failed tasks
  python cli.py retry abstract_algebra_gemini-2.0-flash-lite_en_ibase_obase_circular
  
  # Reset an experiment (clear pending retries)
  python cli.py reset formal_logic_gemini-2.0-flash-lite_en_ijson_obase_circular
"""
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Run command
    run_parser = subparsers.add_parser('run', help='Run experiments')
    run_parser.add_argument('--subtask', required=True, 
                          help='Subtask(s) to run (comma-separated)')
    run_parser.add_argument('--model', default='gemini-2.0-flash',
                          help='Model name')
    run_parser.add_argument('--en', action='store_true', help='Run English')
    run_parser.add_argument('--fr', action='store_true', help='Run French')
    run_parser.add_argument('--format', default='base/base',
                          help='Format: base/base, json/base, xml/base, all, etc.')
    run_parser.add_argument('--permutation', default='circular',
                          choices=['circular', 'factorial'],
                          help='Permutation type')
    run_parser.add_argument('--num-questions', type=int, default=100,
                          help='Number of questions')
    run_parser.add_argument('--start-question', type=int, default=0,
                          help='Starting question index')
    run_parser.add_argument('--max-retries', type=int, default=3,
                          help='Maximum retry attempts')
    run_parser.add_argument('--dry-run', action='store_true',
                          help='Show what would be run without executing')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show experiment status')
    status_parser.add_argument('experiment_id', nargs='?', 
                             help='Specific experiment ID')
    status_parser.add_argument('--verbose', '-v', action='store_true',
                             help='Show detailed information')
    
    # Retry command
    retry_parser = subparsers.add_parser('retry', help='Retry failed tasks')
    retry_parser.add_argument('experiment_id', help='Experiment ID')
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset failed experiment')
    reset_parser.add_argument('experiment_id', help='Experiment ID')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Run tests')
    test_parser.add_argument('--permutations', action='store_true',
                           help='Test permutation logic')
    test_parser.add_argument('--formats', action='store_true',
                           help='Test all format combinations')
    test_parser.add_argument('--subtask', help='Subtask for testing')
    test_parser.add_argument('--question', type=int, help='Question index')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    if args.command == 'run':
        run_subtask(args)
    elif args.command == 'status':
        status_command(args)
    elif args.command == 'retry':
        retry_command(args)
    elif args.command == 'reset':
        reset_command(args)
    elif args.command == 'test':
        test_command(args)


if __name__ == "__main__":
    main()