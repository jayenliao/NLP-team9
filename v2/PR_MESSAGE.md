# Refactor: Experiment System (v2)

## Overview

This pull request delivers a **complete rewrite of the MMMLU order-sensitivity experiment framework**, cutting the codebase from more than 2,000 lines to roughly 1,000 and streamlining every step of the workflow.

---

## Why replace the old system?

| Pain Point (old)                                | Improvement (new)                             |
| ----------------------------------------------- | --------------------------------------------- |
| Experiments tracked in five separate text files | One self-contained status file per experiment |
| Manual JSON edits after API failures            | Automatic retry queue and back-off logic      |
| Hard to resume an interrupted run               | Idempotent “resume on re-run”                 |
| Several `fix_*.py` scripts for retries          | Single `retry` command                        |
| Results scattered across many folders           | Predictable directory layout under `results/` |

---

## Key Features

### 1. Unified CLI

```bash
# Old workflow (simplified)
python experiments/run_experiment.py …
python experiments/fix_filter.py
python experiments/fix_rerun.py
# …manual JSON edits…
python experiments/fix_concat.py

# New workflow
python cli.py run   --subtask abstract_algebra --format all --en
python cli.py retry <experiment_id>   # only when needed
```

### 2. Automatic Resuming

Running the same command again continues an interrupted experiment without duplication:

```bash
python cli.py run --subtask anatomy --format all --en
```

### 3. Robust Retry Logic

* Failed API calls are queued automatically.
* Exponential back-off limits rate-limit errors.
* No manual JSON editing.

### 4. Full Format Coverage

Supported input/output pairs (5 total):

| Input → Output | Example                 |
| -------------- | ----------------------- |
| base → base    | plain text → plain text |
| base → json    | plain text → JSON       |
| base → xml     | plain text → XML        |
| json → base    | JSON → plain text       |
| xml  → base    | XML  → plain text       |

### 5. Cleaner Result Layout

```
results/
└── abstract_algebra_gemini-2.0-flash-lite_en_ibase_obase_circular/
    ├── completed/      # successful runs
    ├── pending/        # queued for retry
    ├── status.json     # progress tracker
    └── final.jsonl     # upload-ready output
```

---

## Migration Guide

### New Experiments

```bash
python cli.py run --subtask YOUR_SUBTASKS --format all --en --fr
```

### Ongoing Experiments (old system)

1. Finish the current subtask with the old scripts.
2. Use the new CLI for everything else.
3. If partial results need migration, contact the tooling team.

---

## Frequently Used Commands

| Goal                                   | Command                                                                            |
| -------------------------------------- | ---------------------------------------------------------------------------------- |
| Run one subtask (all formats, English) | `python cli.py run --subtask abstract_algebra --format all --en`                   |
| Run multiple subtasks                  | `python cli.py run --subtask abstract_algebra,anatomy,astronomy --format all --en` |
| Run a single format                    | `python cli.py run --subtask formal_logic --format json/base --en`                 |
| View all experiments                   | `python cli.py status`                                                             |
| View one experiment                    | `python cli.py status <experiment_id>`                                             |
| Retry failed calls                     | `python cli.py retry <experiment_id>`                                              |
| Hard reset                             | `python cli.py reset <experiment_id>`                                              |

---

## Output Specification (`final.jsonl`)

Each line remains identical to the previous system:

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

---

## Troubleshooting

| Symptom                | Resolution                            |
| ---------------------- | ------------------------------------- |
| `command not found`    | Run from the project root             |
| `API key not found`    | Confirm keys in `.env`                |
| `max retries exceeded` | `python cli.py reset <experiment_id>` |

For anything else, consult `README.md`, ping on Slack/Discord, or schedule a quick call.

---

## Summary

*The new experiment system replaces a fragile, manual workflow with a single, resilient CLI. Expect faster setup, automatic recovery, and a tidy results directory—so you can spend time on research, not infrastructure.*

---

## Checklist

* [x] All tests pass
* [x] Backward-compatible outputs
* [x] Updated documentation
* [x] Migration instructions included
* [ ] Ready for review

---

## Quick Test Suite

```bash
python cli.py test --formats         # validate format handlers
python cli.py test --permutations    # validate permutation logic
python cli.py run --subtask abstract_algebra --num-questions 2
```
