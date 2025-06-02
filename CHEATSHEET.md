# MMMLU Order Sensitivity - Team Cheatsheet

## 🚀 Quick Start Guide

### Setup (One Time)
```bash
# 1. Create .env file with API keys
GOOGLE_API_KEY=your-gemini-api-key
MISTRAL_API_KEY=your-mistral-api-key

# 2. Install dependencies
pip install -r requirements.txt
```

### Common Commands

#### 1. Test Everything Works
```bash
# Test single question across all settings (80 API calls)
python test_single_question_all_settings.py --subtask abstract_algebra

# Test failure handling (no API calls)
python smart_cli.py test --type failures
```

#### 2. Run Small Experiments
```bash
# Single subtask, 5 questions, base format, English only
python smart_cli.py run --subtask abstract_algebra --num-questions 5

# Multiple subtasks
python smart_cli.py run --subtask abstract_algebra,anatomy,formal_logic --num-questions 10

# French + English
python smart_cli.py run --subtask formal_logic --en --fr --num-questions 5
```

#### 3. Run Full Experiments
```bash
# All formats for one subtask (5 format combinations)
python smart_cli.py run --subtask abstract_algebra --format all --en

# Specific format combination
python smart_cli.py run --subtask anatomy --format base/json --en --fr

# Multiple subtasks with all formats
python smart_cli.py run --subtask abstract_algebra,anatomy,astronomy --format all --en --fr
```

#### 4. Check Progress
```bash
# See all experiments
python smart_cli.py status

# See specific experiment details
python smart_cli.py status --experiment abstract_algebra_gemini-2.0-flash-lite_en_ibase_obase
```

## 📊 Full Experiment Settings

### 17 Subtasks (One from each category)
```
abstract_algebra        anatomy               astronomy
business_ethics        college_biology       college_chemistry
college_computer_science   econometrics      electrical_engineering
formal_logic           global_facts          high_school_european_history
high_school_geography  high_school_government_and_politics
high_school_psychology human_sexuality      international_law
```

### Models
- `gemini-2.0-flash-lite` (default)
- `mistral-small-latest`

### Languages
- `--en` (English)
- `--fr` (French)

### Format Combinations
1. `base/base` - Traditional text input/output
2. `base/json` - Text input, JSON output
3. `base/xml` - Text input, XML output
4. `json/base` - JSON input, text output
5. `xml/base` - XML input, text output

## 🔄 How the System Works

1. **Single JSON per experiment**: Each combination creates one file
   - Example: `results/abstract_algebra_gemini-2.0-flash-lite_en_ibase_ojson.json`

2. **Automatic retry**: Failed tasks get ONE retry after 30 seconds

3. **Non-blocking**: Persistent failures are abandoned, experiment continues

4. **Progress tracking**: Check anytime with `status` command

## 📁 File Organization

```
results/
├── abstract_algebra_gemini-2.0-flash-lite_en_ibase_obase.json
├── abstract_algebra_gemini-2.0-flash-lite_en_ibase_ojson.json
├── abstract_algebra_gemini-2.0-flash-lite_fr_ixml_obase.json
└── ... (one file per experiment)
```

Each JSON contains:
- `metadata`: Experiment configuration and progress
- `results`: Successful completions
- `retry_queue`: Current failures (cleared after retry)
- `abandoned`: Tasks that failed twice

## 🎯 Running the Full Experiment

For Topic B requirements:
```bash
# Create a script to run all combinations
#!/bin/bash

SUBTASKS="abstract_algebra anatomy astronomy business_ethics college_biology college_chemistry college_computer_science econometrics electrical_engineering formal_logic global_facts high_school_european_history high_school_geography high_school_government_and_politics high_school_psychology human_sexuality international_law"

# Gemini experiments
for subtask in $SUBTASKS; do
    echo "Running Gemini experiments for $subtask"
    python smart_cli.py run --subtask $subtask --model gemini-2.0-flash-lite --format all --en --fr
done

# Mistral experiments  
for subtask in $SUBTASKS; do
    echo "Running Mistral experiments for $subtask"
    python smart_cli.py run --subtask $subtask --model mistral-small-latest --format all --en --fr
done
```

## 💡 Tips

1. **Start small**: Test with 5-10 questions before running 100
2. **Monitor progress**: Use `watch -n 60 'python smart_cli.py status'`
3. **Check abandoned tasks**: Look in the JSON files for patterns
4. **Rate limits**: Add delays between experiments if needed

## 🐛 Troubleshooting

- **API errors**: Check your .env file and API credits
- **Parse errors**: Check the specific format - XML/JSON might need tweaking
- **Abandoned tasks**: Normal! 99%+ success rate is fine for analysis

## 📈 After Experiments

Results are in clean JSON format, ready for analysis:
```python
import json
import glob

# Load all results
all_results = []
for result_file in glob.glob("results/*.json"):
    with open(result_file) as f:
        data = json.load(f)
        all_results.append(data)

# Now analyze for order sensitivity...
```