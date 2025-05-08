Before start, install jq.
```bash
sudo apt install jq      # Ubuntu / Debian
brew install jq          # macOS
```

Then add 權限
```bash
chmod +x commands/run_exp.sh commands/run_exp_entry.sh
```

To run script
```bash
commands/run_exp.sh
```

See 
```bash
commands/run_exp.sh --help
# or
commands/run_exp.sh -h
```
for more information

Develop Tools

generate all possible experiments
```bash
python generate_constrained_combinations.py input.json -o result.json --format json
```

# To-Do
- [ ] default output file_name do not work (in run_experiment.py)