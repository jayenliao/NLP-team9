#!/usr/bin/env python
"""verify_migration.py - Verify the migration was successful"""

import os
import sys
import importlib

def check_file_exists(filepath, description):
    if os.path.exists(filepath):
        print(f"✓ {description} exists")
        return True
    else:
        print(f"✗ {description} missing: {filepath}")
        return False

def check_import(module_name, description):
    try:
        importlib.import_module(module_name)
        print(f"✓ {description} imports correctly")
        return True
    except ImportError as e:
        print(f"✗ {description} import failed: {e}")
        return False

def main():
    print("Verifying migration...\n")
    
    all_good = True
    
    # Check new files exist
    print("Checking new files:")
    all_good &= check_file_exists("experiments/formatters.py", "Formatters module")
    all_good &= check_file_exists("experiments/parsers.py", "Parsers module")
    all_good &= check_file_exists("experiments/permutations.py", "Permutations module")
    all_good &= check_file_exists("experiments/api_clients.py", "API clients module")
    all_good &= check_file_exists("experiments/core_runner_refactored.py", "Refactored runner")
    
    print("\nChecking backups:")
    all_good &= check_file_exists("experiments/run_experiment_old_backup.py", "Old backup")
    
    print("\nChecking imports:")
    all_good &= check_import("experiments.formatters", "Formatters")
    all_good &= check_import("experiments.parsers", "Parsers")
    all_good &= check_import("experiments.permutations", "Permutations")
    all_good &= check_import("experiments.api_clients", "API clients")
    all_good &= check_import("experiments.core_runner_refactored", "Refactored runner")
    
    print("\nChecking dependencies:")
    all_good &= check_import("google.genai", "Google GenAI")
    all_good &= check_import("mistralai", "Mistral AI")
    all_good &= check_import("tqdm", "tqdm")
    
    if all_good:
        print("\n✅ Migration completed successfully!")
        print("\nYou can now run experiments with the same commands as before:")
        print("python experiments/run_experiment.py --model_family gemini ...")
    else:
        print("\n❌ Some issues found. Please check the errors above.")
        print("\nTo rollback:")
        print("cp experiments/run_experiment_old_backup.py experiments/run_experiment.py")

if __name__ == "__main__":
    main()