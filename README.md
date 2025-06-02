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
