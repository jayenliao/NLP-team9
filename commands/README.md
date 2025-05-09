# 🔬 Experiment Runner

Here provides a flexible command-line interface to run predefined experiments stored in a JSON file, with support for language and format selection, parameter overrides, keyword search, and dry-run inspection.

---

## 📁 Directory Structure

```.
NLP-TEAM0/
├── Makefile              # for fast script
├── ...
└── commands/
  ├── params.json # Experiment configurations
  ├── run_exp.sh # Main runner script
  └── run_exp_entry.sh # Single experiment execution script

```


---

## 📌 Requirements
- Bash 4.0+
- `jq` installed (for JSON parsing)
### Setup
Before start, install jq.
```bash
sudo apt install jq      # Ubuntu / Debian
brew install jq          # macos
```
Then add 權限
```bash
chmod +x commands/run_exp.sh commands/run_exp_entry.sh
```

## 🚀 Usage

### Run by ID (from `result.json`)
```bash
./commands/run_exp.sh 0 1 --fr --json
```

### Run default experiment
```bash
./commands/run_exp.sh --en --base
```

### Run a pre-defined setup
```bash
./commands/run_exp.sh --full-gemini --fr --xml
```

### View available experiments
```bash
./commands/run_exp.sh --list          # Shows first 15
./commands/run_exp.sh --list all      # Shows all
```

### Preview command without running
```bash
./commands/run_exp.sh 0 --en --json --dry-run
```

## 🔧 Command-line Options
| Option                                                                    | Description                                                                |
| ------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| `-h, --help`                                                              | Show help message                                                          |
| `--en`, `--fr`                                                            | Set experiment language                                                    |
| `--base`, `--json`, `--xml`                                               | Set prompt format                                                          |
| `--key value`                                                             | Override any parameter passed to Python script (e.g. `--num_questions 10`) |
| `--dry-run`                                                               | Print command without execution                                            |
| `--list [all]`                                                            | Display experiments with metadata and ID                                   |
| `--full-gemini`, `--full-mistral`,<br>`--small-gemini`, `--small-mistral` | Execute predefined groups of experiments                                   |



## 🔍 Search Experiments
You can find experiments using keyword-based AND search:

```bash
./commands/run_exp.sh --search algebra
./commands/run_exp.sh --search gemini 24
./commands/run_exp.sh --search model_name:gemini delay:1
./commands/run_exp.sh --search difficulty:1 all
```
- Without `field:`, keywords are matched across:
    - `exp_name`, `model_name`, `subtask`, `num_questions`, `num_permutations`, `delay`
- Use `field:value` for field-specific search
- Add `all` at final to display more than 15 results

## 🧪 Example: result.json Entry
```json
{
  "model_name": "gemini-2.0-flash-lite",
  "subtask": "abstract_algebra",
  "num_questions": "5",
  "num_permutations": "3",
  "delay": "1"
}
```

## 🛠️ Generate `params.json` Automatically
You can quickly regenerate the `commands/params.json` using:

```bash
make generate-result
```
This runs:
```bash
python commands/gen_params.py commands/param_set.json -o commands/params.json --format json
```
### Example Input (params.json)
```json
{
  "model_family": ["gemini", "mistral"],
  "model_name": ["gemini-2.0-flash-lite", "mistral-small-latest"]
  "subtask": ["algebra", "logic"],
  "num_questions": { "range": [1, 4, 1] },
  "num_permutations": [1, 5],
  "delay": [1, 2],
  "concat_fields": ["model_family", "subtask", "num_questions"],
  "include_if": [
    {
      "if": { "model_family": "gemini" },
      "then": { "delay": [1] }
    }
  ],
  "exclude_if": [
    {
      "if": { "subtask": "logic" },
      "then": { "num_permutations": [5] }
    }
  ]
}
```
### Output
The script will generate all valid combinations respecting constraints and attach:
- "exp_name": auto-generated from specified concat_fields
- "id": numeric index for use in run_exp.sh

## ✅ Best Practices
- Use `--dry-run` when tuning overrides to verify correctness
- Reference experiment `id` from `--list`/`--search` output when launching
- Group common setups via `--full-*` or `--small-*` presets

## 📌 Requirements
- Bash 4.0+
- `jq` installed (for JSON parsing)

# To-Do
- [ ] default output file_name do not work (in run_experiment.py)
- [ ] make --fr --en to execute both French and English experiments