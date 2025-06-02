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

### Test the System
```bash
# Test with 1 question across all settings (80 API calls)
python test_single_question_all_settings.py

# Test failure handling (no API calls)
python smart_cli.py test --type failures
```

### Run Your First Experiment
```bash
# Small test (5 questions)
python smart_cli.py run --subtask abstract_algebra --num-questions 5

# Check progress
python smart_cli.py status
```

## 📊 Project Overview

We're investigating **Topic B: Order Sensitivity across Input-Output Formats** to understand how different formatting affects LLMs' sensitivity to multiple-choice option ordering.

### Research Questions
- How does order sensitivity vary across languages (English vs French)?
- Do structured formats (JSON/XML) reduce position bias?
- Which subtasks are most sensitive to option reordering?
- Is there a correlation between model confidence and order sensitivity?

## 🔧 System Architecture

### Core Components
- **`smart_runner.py`**: Main experiment runner with automatic retry
- **`smart_cli.py`**: Command-line interface
- **`format_handlers.py`**: Handles 5 format combinations
- **`single_question.py`**: Core API logic

### Key Features
- **Single JSON per experiment**: Clean, simple data storage
- **Automatic retry**: Failed tasks get one retry after 30 seconds
- **Non-blocking**: Abandons persistent failures, continues experiment
- **Resumable**: Can stop/restart anytime

## 📁 Project Structure

```
NLP-team9/
├── smart_cli.py              # Main CLI
├── smart_runner.py           # Experiment runner
├── single_question.py        # Core question runner
├── format_handlers.py        # Format handling
├── data/
│   └── ds_selected.pkl       # MMMLU dataset (17 subtasks)
├── results/                  # Experiment results (JSON files)
├── test_*.py                 # Test scripts
└── .env                      # API keys (create this)
```

## 🎯 Running Full Experiments

### Experiment Parameters
- **17 subtasks** (one from each MMMLU category)
- **2 models**: Gemini and Mistral
- **2 languages**: English and French
- **5 format combinations**: base/base, base/json, base/xml, json/base, xml/base
- **4 circular permutations**: ABCD, DABC, CDAB, BCDA
- **100 questions per subtask**

### Total Scale
- 17 subtasks × 2 models × 2 languages × 5 formats = **340 experiments**
- Each experiment: 100 questions × 4 permutations = **400 API calls**
- Grand total: **136,000 API calls**

### Running Everything
```bash
# Run all subtasks for one model/language/format
python smart_cli.py run --subtask abstract_algebra,anatomy,astronomy,business_ethics,college_biology,college_chemistry,college_computer_science,econometrics,electrical_engineering,formal_logic,global_facts,high_school_european_history,high_school_geography,high_school_government_and_politics,high_school_psychology,human_sexuality,international_law --format all --en --fr

# Or use the provided script
bash scripts/run_full_experiment.sh
```

## 📈 Monitoring Progress

```bash
# Check all experiments
python smart_cli.py status

# Watch progress live
watch -n 60 'python smart_cli.py status'

# Check specific experiment
python smart_cli.py status --experiment abstract_algebra_gemini-2.0-flash-lite_en_ibase_obase

# Analyze results
python analyze_results_example.py results/*.jsonl
```

## 🔬 Data Format

Each experiment produces two files:

1. **`{experiment_id}.jsonl`** - Complete data (one JSON per line, one per API call)
```json
{
  "trial_id": "550e8400-e29b-41d4-a716-446655440000",
  "question_id": "abstract_algebra_0", 
  "prompt_used": "Full prompt text sent to API...",
  "api_raw_response": "Complete raw API response object...",
  "api_response_text": "Model's actual response text...",
  "parsed_answer": "B",
  "model_choice_original_label": "B",
  "ground_truth_answer": "B",
  "is_correct": true,
  "response_time_ms": 1250,
  "question_text": "Find the degree for the given field extension...",
  "original_choices": ["0", "1", "2", "4"],
  "permuted_choices": ["0", "1", "2", "4"],
  "permutation_string": "ABCD",
  ...
}
```

2. **`{experiment_id}_summary.json`** - Quick overview
```json
{
  "experiment_id": "abstract_algebra_gemini-2.0-flash-lite_en_ibase_obase",
  "total_expected": 400,
  "completed": 398,
  "abandoned": 2,
  "status": "completed"
}
```

## 👥 Team

- 盧音孜 / R13922A09
- 莊英博 (Ethan) / R13922A24
- 廖傑恩 (Jay) / R13922210

## 📝 Notes

- Start with small tests (5-10 questions) before full runs
- Expect 99%+ success rate (some API calls may fail)
- Results are in `results/` directory as JSON files
- See `CHEATSHEET.md` for quick command reference

---

For questions or issues, check the test scripts first:
- `test_single_question_all_settings.py` - Test all format combinations
- `test_failure_handling.py` - Test error handling