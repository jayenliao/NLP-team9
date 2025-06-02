#!/usr/bin/env python3
"""
Progress Monitor for MMMLU Experiments
"""

import json
import os
from pathlib import Path
from datetime import datetime
import time

def get_experiment_stats():
    """Get statistics for all experiments"""
    results_dir = Path("results")
    if not results_dir.exists():
        return []
    
    experiments = []
    
    for exp_dir in results_dir.iterdir():
        if exp_dir.is_dir():
            status_file = exp_dir / "status.json"
            if status_file.exists():
                with open(status_file, 'r') as f:
                    data = json.load(f)
                    
                # Parse experiment ID
                parts = exp_dir.name.split('_')
                subtask = parts[0]
                model = '_'.join(parts[1:-4])
                lang = parts[-4]
                formats = f"{parts[-3][1:]}/{parts[-2][1:]}"
                
                experiments.append({
                    'id': exp_dir.name,
                    'subtask': subtask,
                    'model': model,
                    'language': lang,
                    'formats': formats,
                    'total': data['total_expected'],
                    'completed': data['completed'],
                    'pending': len(data.get('pending_retry', {})),
                    'percent': data['completed'] / data['total_expected'] * 100
                })
    
    return experiments

def print_summary():
    """Print experiment summary"""
    experiments = get_experiment_stats()
    
    if not experiments:
        print("No experiments found. Start with: python cli.py run --subtask abstract_algebra --num-questions 5")
        return
    
    print("\n" + "="*80)
    print(f"MMMLU Experiment Progress - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Overall stats
    total_completed = sum(exp['completed'] for exp in experiments)
    total_expected = sum(exp['total'] for exp in experiments)
    overall_percent = total_completed / total_expected * 100 if total_expected > 0 else 0
    
    print(f"\n📊 Overall: {total_completed}/{total_expected} ({overall_percent:.1f}%)")
    
    # Group by model
    by_model = {}
    for exp in experiments:
        if exp['model'] not in by_model:
            by_model[exp['model']] = []
        by_model[exp['model']].append(exp)
    
    for model, exps in by_model.items():
        print(f"\n🤖 {model}")
        print("-" * 60)
        
        # Sort by progress
        for exp in sorted(exps, key=lambda x: x['percent'], reverse=True):
            status = "✅" if exp['percent'] == 100 else "🔄" if exp['percent'] > 0 else "⏳"
            print(f"{status} {exp['subtask']:<25} {exp['language']:<3} {exp['formats']:<10} "
                  f"{exp['completed']:>4}/{exp['total']:<4} ({exp['percent']:>5.1f}%)")

def monitor_loop(interval=30):
    """Auto-refresh monitor"""
    try:
        while True:
            os.system('clear' if os.name == 'posix' else 'cls')
            print_summary()
            print(f"\n🔄 Refreshing every {interval}s (Ctrl+C to exit)")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitor stopped.")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor experiment progress")
    parser.add_argument("--watch", action="store_true", help="Auto-refresh mode")
    parser.add_argument("--interval", type=int, default=30, help="Refresh interval")
    
    args = parser.parse_args()
    
    if args.watch:
        monitor_loop(args.interval)
    else:
        print_summary()