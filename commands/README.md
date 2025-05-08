
# Code Structure
```plaintext
└── commands/ # example commands for running experiments, we may re-organize this folder
  ├── generate_constrained_combinations.py  # Python script to generate all valid experiments
  ├── param_set.json                        # Parameter configuration file specifying 
  ├── result.json                           # Output file containing all valid combinations
  ├── run_exp.sh                            # Main launcher script: parses CLI, reads JSON, dispatches experiments
  └── run_exp_entry.sh                      # Per-experiment runner: wraps Python script, handles defaults and dry-run
```

# Setup
Before start, install jq.
```bash
sudo apt install jq      # Ubuntu / Debian
brew install jq          # macOS
```

Then add 權限
```bash
chmod +x commands/run_exp.sh commands/run_exp_entry.sh
```

# Usage
To run script
```bash
commands/run_exp.sh
```
which runs a small experiment with parameters listed below:
```json
{
    "model_family": "gemini",
    "model_name": "gemini-2.0-flash-lite",
    "prompt_format": "base",
    "language": "en", 
    "subtask": "abstract_algebra",
    "num_questions": 1,
    "num_permutations": 1,
    "delay": 2,
  }
```
you can check it by 
```bash
commands/run_exp.sh --dry-run
```

For more information, see 
```bash
commands/run_exp.sh --help
# or
commands/run_exp.sh -h
```


# Develop Tools

To generate all possible experiments
```bash
python commands/gen_params.py commands/param_set.json -o commands/result.json --format json
```

# To-Do
- [ ] default output file_name do not work (in run_experiment.py)
- [ ] make --fr --en to execute both French and English experiments