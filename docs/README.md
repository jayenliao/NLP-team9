# NLP-team9: MMMLU Order Sensitivity Study

> Investigating how Large Language Models' responses change when multiple-choice question options are reordered across different input/output formats and languages.

## 🎯 Project Overview

This project examines whether LLMs exhibit **order bias** in multiple-choice questions when:
- Answer options are shuffled (e.g., correct answer moves from A to D)
- Input/output formats change (plain text vs JSON vs XML)
- Questions are presented in different languages (English vs French)

**Research Questions:**
1. Do structured formats (JSON/XML) reduce position bias compared to plain text?
2. Are certain domains (e.g., math vs logic) more robust to order changes?
3. How do different models (Gemini vs Mistral) compare in handling permutations?

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

## 📁 Project Structure

```
NLP-team9/
├── cli.py                  # Main command-line interface
├── data/
│   └── ds_selected.pkl     # Preprocessed MMMLU dataset (17 subtasks)
├── src/
│   ├── single_question.py  # Core single question runner
│   ├── batch_runner.py     # Batch execution with retry logic
│   ├── format_handlers.py  # Input/output format handling
│   └── tests/
│       ├── test_permutations.py
│       └── test_all_formats.py
└── results/
    └── {experiment_id}/
        ├── completed/      # Successful API calls
        ├── pending/        # Failed calls awaiting retry
        ├── status.json     # Progress tracking
        └── final.jsonl     # Clean output for analysis
```

## 📊 Experiment Design

### Dataset
- **17 MMMLU subtasks** covering STEM, humanities, social sciences
- **100 questions per subtask** (configurable)
- **2 languages**: English, French

### Format Combinations (5 total)
1. `base/base` - Plain text input → Plain text output
2. `base/json` - Plain text input → JSON output
3. `base/xml` - Plain text input → XML output
4. `json/base` - JSON input → Plain text output
5. `xml/base` - XML input → Plain text output

### Permutations
- **Circular** (default): 4 rotations - ABCD, DABC, CDAB, BCDA
- **Factorial**: All 24 possible orderings

## 🔧 CLI Commands

### Running Experiments
```bash
# Single subtask, default settings
python cli.py run --subtask abstract_algebra

# Multiple subtasks
python cli.py run --subtask abstract_algebra,anatomy,astronomy

# Specific format
python cli.py run --subtask formal_logic --format json/base

# All formats
python cli.py run --subtask anatomy --format all

# Both languages
python cli.py run --subtask abstract_algebra --en --fr

# Deep dive with factorial permutations
python cli.py run --subtask formal_logic --permutation factorial --num-questions 5
```

### Monitoring & Recovery
```bash
# Check all experiments
python cli.py status

# Check specific experiment
python cli.py status {experiment_id}

# Retry failed API calls
python cli.py retry {experiment_id}

# Reset an experiment (clear pending retries)
python cli.py reset {experiment_id}
```

### Testing
```bash
# Test permutation logic
python cli.py test --permutations

# Test all format handlers
python cli.py test --formats
```

## 👥 Team Workflow

### 1. Assign Subtasks
Each team member takes ~5-6 subtasks from:
```
abstract_algebra, anatomy, astronomy, business_ethics,
college_biology, college_chemistry, college_computer_science,
econometrics, electrical_engineering, formal_logic,
global_facts, high_school_european_history, high_school_geography,
high_school_government_and_politics, high_school_psychology,
human_sexuality, international_law
```

### 2. Run Your Experiments
```bash
# Example: If assigned algebra, anatomy, astronomy
python cli.py run --subtask abstract_algebra,anatomy,astronomy --format all --en --fr
```

### 3. Monitor Progress
Experiments are **automatically resumable** - if interrupted, just run the same command again.

### 4. Upload to HuggingFace
Final results are in `results/{experiment_id}/final.jsonl`

## 🔄 Key Improvements Over v1

| Feature | Old System | New v2 System |
|---------|------------|---------------|
| **Tracking** | 5 manual text files | Single `status.json` per experiment |
| **Failure Handling** | Manual JSON editing | Automatic retry with exponential backoff |
| **Resume** | Complex state management | Automatic - just rerun command |
| **Organization** | Scattered results | Organized by subtask |
| **Code** | 2000+ lines, complex | ~1000 lines, modular |

## 📈 Output Format

Each result in `final.jsonl`:
```json
{
  "question_id": "abstract_algebra_0",
  "subtask": "abstract_algebra",
  "model": "gemini-2.0-flash-lite",
  "language": "en",
  "input_format": "base",
  "output_format": "base",
  "permutation": [0, 1, 2, 3],
  "parsed_answer": "B",
  "is_correct": true,
  "timestamp": "2024-05-31 10:30:45"
}
```

## 🐛 Troubleshooting

### "Max retries exceeded"
```bash
python cli.py reset {experiment_id}
```

### API Key Issues
Ensure `.env` file exists in project root with:
```
GOOGLE_API_KEY=your-key
MISTRAL_API_KEY=your-key
```

### Resume After Interruption
Just run the same command again - progress is saved automatically.

## 📚 References

- Dataset: [OpenAI MMMLU](https://huggingface.co/datasets/openai/MMMLU)
- Related Papers:
  - "LLMs Are Not Robust Multiple Choice Selectors" (ICLR 2024)
  - "Mitigating Selection Bias" (ACL 2024)

## 👨‍💻 Contributors

- 盧音孜 / R13922A09
- 莊英博 (Ethan) / R13922A24
- 廖傑恩 (Jay) / R13922210

---
*NLP Spring 2025 - National Taiwan University*