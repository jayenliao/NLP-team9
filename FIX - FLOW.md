# Experiment Flow
## Run Experiment
1. Search the experiment id with `./commands/run_exp.sh --search [requirements]`. For example, `./commands/run_exp.sh --search gemini history`. See `./commands/run_exp.sh -h` for more information.
2. Run the experiment by `./commands/run_exp.sh {id} --{lang} --{format}`
3. Results would be save at `./results/{model_name}_{lang}_{format}_{time_stamp}/raw.jsonl`

## Fix Experiment Results
0. Before {commit}'s result: 
    1. For each experiment result file `{name}.jsonl`, save it in `results/{name}` and rename it into `raw.jsonl`. 
    2. Add `To-Fix` at `results/`
    3. Add each experiment name into `results/To-Fix`. Example look of `results/To-Fix`:
    ```plain
    mistral-small-latest_fr_base_20250512-225608
    mistral-small-latest_en_base_20250512-225559
    ```
1. Filter out failure case
```bash
make filter-results
```
2. Rerun api-failed case
```bash
make rerun
```
3. Manual revise failed case in other-failed. After revised, run this command to check if all cases are correctly revised. Since rerunned cases might need manual revisement, please revise while `make rerun` isn't running for the experiment.
```bash
make check-manual
```
4. Concact all results
```bash
make concact
```