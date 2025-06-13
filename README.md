# NLP‑team9 · MMMLU Order Sensitivity Study

> Exploring how large language models react to answer‑option permutations across input/output formats and languages.

---

## 🎯 Overview

This project measures **order bias** in multiple‑choice question answering (MCQA) when we vary

* the **order** of answer options (circular shifts),
* the **input / output schema** (plain text ⇄ JSON / XML), and
* the **language** of the prompt (English vs French).

### Key research questions

| RQ | Question |
|----|-----------|
| 1  | Do structured formats reduce position bias compared with plain text? |
| 2  | Which knowledge domains are most / least robust to option permutations? |
| 3  | How do two public LLMs – Gemini‑2.0‑flash and Mistral‑small‑latest – compare? |

---

## 🚀 Quick start

### 1 · Install & configure
```bash
# Python 3.10+
pip install -r requirements.txt

# .env in the project root
GOOGLE_API_KEY="your‑gemini‑key"
MISTRAL_API_KEY="your‑mistral‑key"
```

### 2 · Run a small test
```bash
# Five English algebra questions, plain‑text format, circular shifts
a python cli.py run \
      --subtask abstract_algebra \
      --num-questions 5 --en
```

### 3 · Check progress
```bash
python cli.py status   # lists all running / finished experiments
```

*Experiments are resumable – rerun the same command to continue.*

---

## 📁 Project layout
```
NLP‑team9/
├── cli.py                 # unified command‑line entry‑point
├── data/
│   └── ds_selected.pkl    # 17‑subtask MMMLU slice (EN/FR)
├── src/
│   ├── single_question.py # single‑prompt pipeline
│   ├── batch_runner.py    # full grid with retry & logging
│   ├── format_handlers.py # 5 I/O schemas
│   └── tests/
│       ├── test_permutations.py
│       └── test_all_formats.py
└── v2_results/
    └── EXP_ID/
        ├── completed/     # successful calls (.json)
        ├── pending/       # to‑retry calls (.json)
        ├── status.json    # progress & statistics
        └── final.jsonl    # clean output for analysis
```

---

## 📊 Experiment design

| Component   | Setting |
|-------------|---------|
| **Models**  | *Gemini‑2.0‑flash* ([Gemini 2023](https://arxiv.org/abs/2312.11805)), *Mistral‑small‑latest* ([Mistral 7B](https://arxiv.org/abs/2310.06825)) |
| **Languages** | English (EN), French (FR) |
| **Subtasks** | 17 topics spanning STEM, humanities, social sciences, other |
| **Items** | 100 questions per subtask (test split) |
| **Permutations** | 4 circular shifts: `ABCD`, `DABC`, `CDAB`, `BCDA` |
| **I/O Schemas** | `base/base`, `base/json`, `base/xml`, `json/base`, `xml/base` |

Total calls per full grid: `2 models × 2 langs × 5 schemas × 17 tasks × 100 q × 4 shifts = 136 000`.

---

## 🔧 CLI cheatsheet

```bash
# Full EN+FR grid for a task (all five schemas)
python cli.py run --subtask abstract_algebra --format all --en --fr

# Multiple subtasks (comma‑sep)
python cli.py run --subtask anatomy,astronomy,econometrics --format base/base --fr

# Factorial (24‑perm) deep dive on one task
python cli.py run --subtask formal_logic --permutation factorial --num-questions 20

# Check / resume
python cli.py status                # list all grids
python cli.py status EXP_ID         # details of one grid
python cli.py retry  EXP_ID         # re‑issue failed calls
python cli.py reset  EXP_ID         # clear the pending queue
```

---

## 🧪 Testing utilities
```bash
# Verify permutation handling on a single question
python cli.py test --permutations --subtask abstract_algebra --question 0

# Smoke‑test all 5 schemas
python cli.py test --formats
```

---

## ⚙️ Implementation highlights

* **Retry & resume** – each prompt is stored on disk; interrupted runs pick up where they left off.
* **Format handlers** – central module converts a `Question` object to any of the five prompt schemas and parses the model response.
* **Metrics** – Fluctuation Rate (FR) and Relative Standard Deviation (RSD) computed per grid.

---

## 📈 Output schema (`final.jsonl`)
```json
{
  "question_id": "abstract_algebra_42",
  "subtask": "abstract_algebra",
  "model": "gemini-2.0-flash",
  "language": "fr",
  "input_format": "xml",
  "output_format": "base",
  "permutation": [1,2,3,0],
  "parsed_answer": "C",
  "is_correct": true,
  "timestamp": "2025-06-11 14:03:55"
}
```

---

## 🙋‍♂️ Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Max retries exceeded` | `python cli.py reset EXP_ID` then rerun the grid |
| Blank / malformed API key | ensure `.env` has `GOOGLE_API_KEY` and/or `MISTRAL_API_KEY` |
| Want to resume after crash | just run the identical `cli.py run …` command – state is persisted |

---

## 📚 Selected references

* Hendrycks et al. 2021 – Measuring Massive Multitask Language Understanding.
* Pezeshkpour & Hruschka 2024 – Option‑order sensitivity in LLMs.
* Wei et al. 2024 – Selection biases (order & token).
* Tam et al. 2024 – Format restrictions versus free‑form generation.

_BibTeX entries are in [`references.bib`](references.bib)._  

---

## 👥 Contributors

* 盧音孜 · R13922A09  
* 莊英博 (Ethan) · R13922A24  
* 廖傑恩 (Jay) · R13922210  


> NLP (Spring 2025) · National Taiwan University
