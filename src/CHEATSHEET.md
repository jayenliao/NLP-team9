# Team Cheat Sheet – Legacy vs. New Experiment System

---

## 1. Command Mapping

| Task                  | Legacy Workflow                                                                                                                                                                    | New Workflow                                                |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| **Run an experiment** | `python experiments/run_experiment.py --model_family gemini --model_name gemini-2.0-flash-lite --language en --prompt_format base --subtasks abstract_algebra --num_questions 100` | `python cli.py run --subtask abstract_algebra`              |
| **Inspect failures**  | 1. `make filter-results`<br>2. Review files in `results/__logs__/`<br>3. Search several directories                                                                                | `python cli.py status`                                      |
| **Retry failures**    | 1. `make rerun`<br>2. Wait for completion<br>3. `make check-failure`<br>4. Manually edit JSON files<br>5. `make concact`                                                           | `python cli.py retry <experiment_id>`                       |
| **Run all formats**   | Five separate commands with different `--prompt_format` / `--output_format` flags                                                                                                  | `python cli.py run --subtask abstract_algebra --format all` |
| **Run French**        | Add `--language fr`                                                                                                                                                                | Add `--fr`                                                  |
| **Locate results**    | Browse nested folders                                                                                                                                                              | `results/<experiment_id>/final.jsonl`                       |

---

## 2. Illustrative Scenarios

### 2.1 Run *abstract\_algebra* (English, all formats)

<details>
<summary>Legacy</summary>

```bash
python experiments/run_experiment.py --subtasks abstract_algebra --prompt_format base --output_format base
python experiments/run_experiment.py --subtasks abstract_algebra --prompt_format base --output_format json
python experiments/run_experiment.py --subtasks abstract_algebra --prompt_format base --output_format xml
python experiments/run_experiment.py --subtasks abstract_algebra --prompt_format json --output_format base
python experiments/run_experiment.py --subtasks abstract_algebra --prompt_format xml --output_format base
```

</details>

**New**

```bash
python cli.py run --subtask abstract_algebra --format all --en
```

---

### 2.2 Interrupted Run

*Simply re-issue the original command; progress resumes automatically.*

```bash
python cli.py run --subtask abstract_algebra --format all --en
```

---

### 2.3 API Failures

```bash
python cli.py retry <experiment_id>
```

---

## 3. Directory Layout

### Legacy

```
results/
├── __logs__/
│   ├── 0-to-Filter
│   ├── 1-to-Rerun
│   ├── 2-to-Manual-Fix
│   ├── 3-to-Concact
│   └── 4-to-Analyze
└── experiment_name_timestamp/
    ├── raw.jsonl
    ├── api_failed.jsonl
    ├── other_failed.json
    ├── rerun.jsonl
    └── fix.jsonl
```

### New

```
results/
└── <experiment_id>/
    ├── completed/        # successful calls
    ├── pending/          # queued for retry
    ├── status.json       # progress tracker
    └── final.jsonl       # consolidated output
```

---

## 4. Recommended Daily Workflow

| Day                 | Action                                 | Command                                                                            |
| ------------------- | -------------------------------------- | ---------------------------------------------------------------------------------- |
| **Start**           | Verify assignments                     | `cat TEAM_ASSIGNMENTS.txt`                                                         |
|                     | Launch subtasks (all formats, English) | `python cli.py run --subtask abstract_algebra,anatomy,astronomy --format all --en` |
| **Progress check**  | View overall status                    | `python cli.py status`                                                             |
|                     | Retry if needed                        | `python cli.py retry <experiment_id>`                                              |
| **Language switch** | French runs                            | `python cli.py run --subtask abstract_algebra,anatomy,astronomy --format all --fr` |
| **Completion**      | Locate final output                    | `results/<experiment_id>/final.jsonl`                                              |

---

## 5. Troubleshooting

| Issue                  | Resolution                                                           |
| ---------------------- | -------------------------------------------------------------------- |
| *Max retries exceeded* | `python cli.py reset <experiment_id>`                                |
| *API key not found*    | Confirm keys in `.env` (project root)                                |
| Unclear error          | Remove the experiment folder and re-run, or contact the tooling team |

---

## 6. Efficiency Tips

1. **Test run** – use `--num-questions 5` before a full launch.
2. **Live monitoring** – in a second terminal: `watch python cli.py status`.
3. **Parallel subtasks** – run distinct subtasks in separate terminals.
4. **Safe resume** – rerunning the same `cli.py run` command never duplicates work.

The new system is resilient; most problems are fixed by simply retrying. Manual JSON edits are no longer necessary.
