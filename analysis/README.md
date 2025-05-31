# analysis

Here are tools for analyzing experiment results.

## `analyze_results.py`

### Examples of getting accuracy metrics

#### Use all default accuracy metrics

```bash
python3 analysis/analyze_results.py \
    "results/gemini-2.0-flash-lite_en_*/raw.jsonl" \
    --output_file_path results_summary/0_abstract_algebra_gemini-2.0-flash-lite_en.json
```

#### Specify accuracy metrics

```bash
python3 analysis/analyze_results.py \
    "results/gemini-2.0-flash-lite_en_*/raw.jsonl" \
    --accuracy_metrics overall_accuracy by_model_name by_input_format \
    --output_file_path results_summary/0_abstract_algebra_gemini-2.0-flash-lite_en.json
```

### Examples of getting confidence metrics

#### Use all default confidence metrics

```bash
python3 analysis/analyze_results.py \
    "results/gemini-2.0-flash-lite_en_*/raw.jsonl" \
    --output_file_path results_summary/0_abstract_algebra_gemini-2.0-flash-lite_en.json
```

#### Sepecify confidence metric(s)

```bash
python3 analysis/analyze_results.py \
    "results/gemini-2.0-flash-lite_en_*/raw.jsonl" \
    --confidence_metrics confidence_high \
    --output_file_path results_summary/0_abstract_algebra_gemini-2.0-flash-lite_en.json
```

#### Use `--confidence_to_csv` to save confidence scores as csv files

```bash
python3 analysis/analyze_results.py \
    "results/gemini-2.0-flash-lite_en_*/raw.jsonl" \
    --confidence_metrics confidence_high \
    --output_file_path results_summary/0_abstract_algebra_gemini-2.0-flash-lite_en.json
    --confidence_to_csv
```

## `get_failure_rate.py`: Model Prediction Error Analysis

- Automatically loads the result file based on model name, language, and format
- Summarizes statistics about:
  - API call success/failure
  - Presence of raw API responses and parsed answers
  - "Pure answer-parsing errors" (successful API call, but parsing failed)
- Interactive CLI inspection:
  - Optionally print samples with failed API calls
  - Optionally print samples with parsing failures

### Directory Structure

```
.
├── get_failure_rate.py        # Compute various failure rates for
├── results/                 # Directory containing .jsonl output files
│   ├── {model}_{lang}_{format}_*.jsonl

```

### How to Run

You can either specify a file name directly or allow the script to automatically select a file based on the model, language, and format arguments.

#### Basic Usage

```bash
python analysis/get_failure_rate.py --model_name gemini-2.0-flash-lite --lang en --format json
```

The script will automatically find the matching `.jsonl` file in the `results/` directory.

#### Specify Exact File

```bash
python analysis/get_failure_rate.py --fn results/gemini-2.0-flash-lite_en_json_20250509-110927.jsonl
```

### Arguments

| Argument          | Description                                               | Required | Default |
| ----------------- | --------------------------------------------------------- | -------- | ------- |
| `--fn`            | Exact path to the `.jsonl` file                           | No       | `None`  |
| `--model_name/-m` | Name of the model used (used for auto-matching filenames) | Yes\*    | `gemini-2.0-flash-lite` |
| `--lang/-l`       | Language of the data (`en` or `fr`)                       | Yes\*    | `en`    |
| `--format/-f`     | Format of the data (`base`, `json`, or `xml`)             | Yes\*    | `json`  |

\*Required if `--fn` is not provided.

### Output

The script prints:

* Total number of samples
* Number of successful API calls
* Number of samples with raw responses and parsed answers
* Failure rates for API calls and parsing

Example output:

```
Total number of samples: 100
Total number of successful API calls: 98
Total number of samples with raw response: 98
Total number of samples with parsed answer: 96
Total number of samples with no raw response: 2
Total number of samples with no parsed answer: 4
API Call Failure Rate: 2.00%
API No Raw Response Rate: 2.00%
API Parse Answer Failure Rate: 4.00%
```

### Expected JSONL Format

Each line in the `.jsonl` file should contain fields such as:

- `question_id`: ID of the question
- `option_permutation`: (optional) list of shuffled answer options
- `api_call_successful`: `true`/`false`
- `api_raw_response`: raw text returned from the model or API
- `extracted_answer`: the final parsed answer string

Only `api_call_successful`, `api_raw_response`, and `extracted_answer` are strictly required.


### Notes

* Only `.jsonl` files with names matching the pattern `<model_name>_<lang>_<format>_*.jsonl` will be auto-detected.
* If multiple matching files exist, you'll need to specify one using `--fn`.

## 🔧 Planned Improvements

[] Export failed samples to CSV or JSONL interactively
[] Deeper analysis
