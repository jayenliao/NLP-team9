# MMMLU Order Sensitivity Experiments

## Table of Contents

1. Quick Start
2. User Guide
3. Essential Rules
4. System Overview
5. Running Experiments
6. Troubleshooting
7. Reviewer Notes

---

## 1  Quick Start

### 1.1  Environment

```bash
cd NLP-team9
pip install -r requirements.txt

# API keys
echo "GOOGLE_API_KEY=<your‑gemini‑key>"  >> .env
echo "MISTRAL_API_KEY=<your‑mistral‑key>" >> .env
```

### 1.2  Sanity Checks

```bash
python smart_cli.py test --type data      # end‑to‑end: 1 API call
python smart_cli.py test --type failures  # mock retry path
```

### 1.3  Example Run (5 questions ⇒ 20 API calls)

```bash
python smart_cli.py run \
       --subtask abstract_algebra \
       --num-questions 5
```

---

## 2  User Guide

### 2.1  Purpose

Evaluate how option order affects LLM answers across prompt/response formats and languages.

### 2.2  Key Files

```
smart_cli.py      # CLI entry
smart_runner.py   # experiment scheduler & retry
single_question.py# single‑question pipeline
format_handlers.py# prompt / parse helpers
data/ds_selected.pkl
results/          # output (JSONL + summary)
```

### 2.3  CLI Short Reference

```bash
# Default (English, base↔base)
python smart_cli.py run --subtask SUBTASK

# Multiple subtasks, all formats
python smart_cli.py run --subtask a1,a2 --format all

# Bilingual
python smart_cli.py run --subtask SUBTASK --en --fr

# Progress
python smart_cli.py status
python smart_cli.py status --experiment EXP_ID
```

---

## 3  Essential Rules

1. **Clean before rerun** – delete prior `results/{experiment}*` to avoid mixing data.
2. **Watch API usage** – one full experiment = 400 calls; full grid ≈ 136 k calls.
3. **Interrupt wisely** – stop during phase 1, not during 30‑s retry loop.
4. **Monitor long runs** – e.g. `watch -n 60 "python smart_cli.py status"`.

---

## 4  System Overview

* Four circular permutations: ABCD, DABC, CDAB, BCDA.
* Five format pairs: base/base, base/json, base/xml, json/base, xml/base.
* Two phases per experiment: initial pass, then single retry of failures.
* Every API call saved as a JSON object in a `.jsonl` file; summary JSON tracks progress.

---

## 5  Running Experiments

### 5.1  Small‑scale Tests

```bash
python smart_cli.py run --subtask formal_logic --num-questions 5
```

### 5.2  Full Grid (example script)

```bash
#!/usr/bin/env bash
SUBTASKS=(abstract_algebra anatomy ...)
for s in "${SUBTASKS[@]}"; do
  python smart_cli.py run --subtask "$s" --format all --en --fr
done
```

---

## 6  Troubleshooting

| Symptom                            | Fix                                                                                    |
| ---------------------------------- | -------------------------------------------------------------------------------------- |
| Attribute errors after code change | `find . -name "*.pyc" -delete && find . -name "__pycache__" -type d -exec rm -rf {} +` |
| Mismatched progress counts         | Remove corresponding `*_summary.json` and rerun                                        |
| Need full reset                    | `rm -rf results/*` and clear `*.pyc` files                                             |
| API failures                       | Verify keys, quota, add delay (`--dry-run` to preview)                                 |

---

## 7  Reviewer Notes

* **New JSONL runner** saves full prompt, raw response, latency, parse outcome.
* Automatic single retry of failed calls (30 s delay).
* Experiments are resumable; summary file stores completed task IDs.
* Removed unused legacy scripts (`batch_runner.py`, `cli.py`).

**Test suite**

```bash
python smart_cli.py test --type data      # data integrity
python smart_cli.py test --type failures  # retry logic
python smart_cli.py test --type single    # 80 prompt/format pairs
```

---

### Team

* 盧音孜  R13922A09
* 莊英博 (Ethan)  R13922A24
* 廖傑恩 (Jay)    R13922210

For questions: see Troubleshooting section first, then contact the team.
