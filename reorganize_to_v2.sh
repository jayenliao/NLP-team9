#!/bin/bash
# Script to reorganize project structure with v2 as main

echo "🔄 Reorganizing project to use v2 as main system..."

# 1. Create legacy folder for old code
echo "📁 Creating legacy folder..."
mkdir -p legacy

# 2. Move old experiment system to legacy
echo "📦 Moving old experiment system to legacy..."
mv experiments legacy/
mv commands legacy/
mv analysis legacy/
mv Makefile legacy/

# 3. Move v2 files to root
echo "🚀 Promoting v2 to main system..."
mv v2/cli.py .
mv v2/batch_runner.py .
mv v2/format_handlers.py .
mv v2/single_question.py .

# 4. Create new organized structure
echo "🏗️ Creating new structure..."
mkdir -p src
mkdir -p tests
mkdir -p scripts
mkdir -p docs

# 5. Move test files
mv v2/test_*.py tests/

# 6. Move documentation
mv v2/*.md docs/
mv README.md docs/README_legacy.md

# 7. Create new main README
cat > README.md << 'EOF'
# NLP-team9: MMMLU Order Sensitivity Study

> Investigating how Large Language Models' responses change when multiple-choice question options are reordered across different input/output formats and languages.

## 🚀 Quick Start

### Prerequisites
```bash
# Python 3.10+
pip install -r requirements.txt

# Create .env file with your API keys
GOOGLE_API_KEY=your-gemini-api-key
MISTRAL_API_KEY=your-mistral-api-key
```

### Run Your First Experiment
```bash
# Test with 5 questions
python cli.py run --subtask abstract_algebra --num-questions 5

# Check status
python cli.py status

# Run full experiment (100 questions, all formats)
python cli.py run --subtask abstract_algebra --format all --en
```

## 📊 Full Experiment

Run all 17 subtasks with both models and languages:
```bash
bash scripts/run_full_experiment.sh
```

Monitor progress:
```bash
python scripts/monitor_progress.py --watch
```

## 📁 Project Structure

```
NLP-team9/
├── cli.py                  # Main command-line interface
├── single_question.py      # Core single question runner
├── batch_runner.py         # Batch execution with retry logic
├── format_handlers.py      # Input/output format handling
├── data/
│   └── ds_selected.pkl     # Preprocessed MMMLU dataset
├── scripts/
│   ├── run_full_experiment.sh
│   └── monitor_progress.py
├── tests/
│   ├── test_permutations.py
│   └── test_all_formats.py
└── results/
    └── {experiment_id}/
        ├── completed/      # Successful API calls
        ├── pending/        # Failed calls awaiting retry
        ├── status.json     # Progress tracking
        └── final.jsonl     # Clean output for analysis
```

## 🔧 CLI Commands

```bash
# Run experiments
python cli.py run --subtask abstract_algebra --format all --en --fr

# Check status
python cli.py status

# Retry failed calls
python cli.py retry {experiment_id}

# Run tests
python cli.py test --formats
python cli.py test --permutations
```

## 👥 Team

- 盧音孜 / R13922A09
- 莊英博 (Ethan) / R13922A24
- 廖傑恩 (Jay) / R13922210

---
*NLP Spring 2025 - National Taiwan University*
EOF

# 8. Create the full experiment runner script
mkdir -p scripts
cat > scripts/run_full_experiment.sh << 'EOF'
#!/bin/bash
# Full Experiment Runner for NLP Team 9

SUBTASKS=(
    "abstract_algebra" "anatomy" "astronomy" "business_ethics"
    "college_biology" "college_chemistry" "college_computer_science"
    "econometrics" "electrical_engineering" "formal_logic"
    "global_facts" "high_school_european_history"
    "high_school_geography" "high_school_government_and_politics"
    "high_school_psychology" "human_sexuality" "international_law"
)

MODELS=("gemini-2.0-flash-lite" "mistral-small-latest")

echo "Starting Full MMMLU Order Sensitivity Experiment"
echo "==============================================="

for model in "${MODELS[@]}"; do
    for subtask in "${SUBTASKS[@]}"; do
        echo "Running $subtask with $model..."
        
        # English
        python cli.py run --subtask "$subtask" --model "$model" --format all --en
        
        # French
        python cli.py run --subtask "$subtask" --model "$model" --format all --fr
        
        sleep 2
    done
done

echo "All experiments submitted!"
EOF

chmod +x scripts/run_full_experiment.sh

# 9. Clean up empty v2 directory
rmdir v2 2>/dev/null || true

# 10. Update .gitignore
cat >> .gitignore << 'EOF'

# Legacy code
legacy/

# Experiment results
results/

# Environment
.env
__pycache__/
*.pyc

# Logs
*.log
EOF

echo "✅ Reorganization complete!"
echo ""
echo "New structure:"
echo "- Main CLI: cli.py"
echo "- Legacy code: legacy/"
echo "- Scripts: scripts/"
echo "- Tests: tests/"
echo ""
echo "Next steps:"
echo "1. Test the new structure: python cli.py test --formats"
echo "2. Commit changes: git add -A && git commit -m 'Reorganize: v2 as main system'"
echo "3. Run experiment: python cli.py run --subtask abstract_algebra --num-questions 5"