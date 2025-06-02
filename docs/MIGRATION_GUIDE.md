# Migration Guide: v2 → Main Project

## Step 1: Backup Current State
```bash
# Create a backup branch
git checkout -b backup-old-system
git add .
git commit -m "backup: old experiment system before v2 migration"
git push origin backup-old-system
```

## Step 2: Restructure Files
```bash
# Go to project root
cd /path/to/NLP-team9

# 1. Move v2 source files to project root
mv v2/single_question.py ./
mv v2/batch_runner.py ./
mv v2/format_handlers.py ./
mv v2/cli.py ./

# 2. Create src directory and organize
mkdir -p src/tests
mv single_question.py batch_runner.py format_handlers.py src/
mv v2/test_*.py src/tests/

# 3. Update imports in all files
# In cli.py, change:
# from batch_runner import ... → from src.batch_runner import ...
# from single_question import ... → from src.single_question import ...

# 4. Move v2_results to results (after backing up old results)
mv results results_old
mv v2_results results

# 5. Update the new README
mv v2/README.md ./README.md

# 6. Clean up
rm -rf v2/
rm test_v2.sh  # No longer needed
```

## Step 3: Update Import Paths

### In `cli.py`:
```python
# Change from:
sys.path.append(str(Path(__file__).parent))
from batch_runner import ...

# To:
from src.batch_runner import ...
from src.single_question import ...
```

### In `src/batch_runner.py`:
```python
# Change from:
from single_question import ...

# To:
from .single_question import ...
```

### In test files:
```python
# Change from:
sys.path.append(str(Path(__file__).parent))
from single_question import ...

# To:
from ..single_question import ...
```

## Step 4: Update Path References

### In all files, update result paths:
```python
# Change from:
Path("v2_results")

# To:
Path("results")
```

## Step 5: Create Migration Script (Optional)

Save this as `migrate_v2.py`:
```python
#!/usr/bin/env python3
"""One-click migration from v2 to main structure"""

import os
import shutil
from pathlib import Path

def migrate():
    print("Starting v2 → main migration...")
    
    # Check we're in right place
    if not Path("v2").exists():
        print("Error: v2 directory not found")
        return
    
    # 1. Backup old results
    if Path("results").exists():
        print("Backing up old results...")
        shutil.move("results", "results_old")
    
    # 2. Create new structure
    print("Creating new structure...")
    os.makedirs("src/tests", exist_ok=True)
    
    # 3. Move files
    moves = [
        ("v2/single_question.py", "src/single_question.py"),
        ("v2/batch_runner.py", "src/batch_runner.py"),
        ("v2/format_handlers.py", "src/format_handlers.py"),
        ("v2/cli.py", "cli.py"),
        ("v2/test_permutations.py", "src/tests/test_permutations.py"),
        ("v2/test_all_formats.py", "src/tests/test_all_formats.py"),
        ("v2_results", "results"),
    ]
    
    for src, dst in moves:
        if Path(src).exists():
            print(f"Moving {src} → {dst}")
            shutil.move(src, dst)
    
    # 4. Update imports (simplified - you may need to do manually)
    print("\n⚠️  Remember to update imports in all files!")
    print("Change: from single_question import ...")
    print("To: from src.single_question import ...")
    
    print("\n✅ Migration complete!")

if __name__ == "__main__":
    migrate()
```

## Step 6: Test Everything
```bash
# Test basic functionality
python cli.py test --permutations
python cli.py test --formats

# Run a small experiment
python cli.py run --subtask abstract_algebra --num-questions 2

# Check it worked
python cli.py status
```

## Step 7: Commit Changes
```bash
git add .
git commit -m "refactor: migrate v2 system to main project structure"
```