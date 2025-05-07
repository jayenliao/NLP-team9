# NLP-team9 Project: Order Sensitivity across Input-Output Formats

## Overview

This is the final project of NLP, a course at National Taiwan University (Spring 2025). We are team 9. Our project aims to investigate LLM's order sensitivity across input-output Formats and two languages, namely English and French.

### Team Members

- 盧音孜 / R13922A09 / r13922A09@csie.ntu.edu.tw
- 莊英博（Ethan）/ R13922A24 / ethan40125bard@gmail.com
- 廖傑恩（Jay）/ R13922210 / jay.chiehen@gmail.com

### Timeline

- Proposal: 19:20 on May 14 (online)
- Final Submission: June 13

## Methodology

### Dataset

- **[MMMLU (Multilingual MMLU)](https://huggingface.co/datasets/openai/MMMLU)**
  - 14 Languages (we only need 2.)
  - 57 subtasks across STEM, humanities, social sciences, and others (we only need 17 subtasks.)

### Prompt Template

- *我們規定使用OpenAI 所設計的 Prompt格式 (MMMLU是Open AI提出的資料集)*
- -*請參考 OpenAI 的 simple-evals 儲存庫中的 mmlu_eval.py、common.py檔案。主要要看Prompt Template 以及從回應中擷取答案的方式，不用指定System Prompt。*
- *https://github.com/openai/simple-evals*

### Research Questions

- How does changing the **input-output format** affect LLMs' sensitivity to the order of MCQ options?
- Are some **subtasks (e.g., math, ethics)** more robust under format perturbations?
- Do **structured formats** reduce ambiguity and improve consistency in model predictions?

## Usage

### Environment

- Create a conda virtual env and activate it.

    ```bash
    conda create --name nlp_team9 python=3.10 -y
    conda activate nlp_team9
    ```

- Install required python dependencies.

    ```bash
    pip3 install -r requirements.txt
    ```

### Source Code Structure

```plaintext
nlp-team9/
│
├── data/ # Dataset preparation and storage
│ ├── categories.py # MMMLU category mappings
│ ├── ds_selected.pkl # Processed dataset (17 subtasks, 2 langs, 100 Qs each)
│ ├── EDA.ipynb # Exploratory Data Analysis
│ └── save_datasets.py # Generates ds_selected.pkl
│
├── prompts/                # Prompt templates
│ └── prompt_templates.py    # Prompts templates for all formate and languages
│
├── commands/ # example commands for running experiments, we may re-organize this folder
│ ├── full_eval_en.sh  # running the full experiment (all subtasks) of mistral/en/json
│ ├── full_eval_fr.sh  # running the full experiment of mistral/fr/json
│ ├── small_test_en.sh  # running the experiment of a subtask of gemini/en/base
│ └── small_test_fr.sh  # running the experiment of a subtask of gemini/en/base
│
├── experiments/ # Core experiment logic
│ ├── core_runner.py # Prompt formatting, API calls, response parsing
│ ├── run_experiment.py # Main experiment script
│ ├── utils.py # Helper functions
│ ├── run_gemini.py # Gemini API test
│ └── run_mistral.py # Mistral API test
│
├── results/ # Output JSONL files
│ └── shared_output_format.py # Output structure
│
├── logs/ # Experiment logs
│ └── experiment.log # Default log file
│
├── analysis/ # (Planned) Result analysis scripts
│
├── .env # API keys
├── .gitignore # Git-ignored files
├── requirements.txt # Dependencies
└── README.md # Project overview
```

## Git Workflow Guideline

### Git Commit Types (Conventional Commits)

Follow the [Conventional Commits](https://www.conventionalcommits.org/) standard. Use this format:

```
<type>(scope): <short summary>
```

#### Common Commit Types:

| Type       | When to Use                                                                 |
|------------|------------------------------------------------------------------------------|
| `feat`     | New feature                                                                  |
| `fix`      | Bug fix                                                                      |
| `docs`     | Documentation changes                                                        |
| `style`    | Formatting only (e.g., spacing, semicolons), no code change                  |
| `refactor` | Code change that neither fixes a bug nor adds a feature                     |
| `perf`     | Performance improvement                                                      |
| `test`     | Adding or updating tests                                                     |
| `chore`    | Routine tasks (e.g., build scripts, package updates)                         |
| `ci`       | CI/CD pipeline or GitHub Actions changes                                     |
| `build`    | Build system or external dependencies updates                                |
| `revert`   | Revert a previous commit                                                     |

#### Examples:

```bash
feat(auth): add OAuth2 login flow
fix(api): correct 500 error on null input
docs(readme): update installation guide
style(linter): apply black formatting
refactor(utils): simplify date conversion function
```

---

### Git PR Workflow

#### 1. **Branch Naming**

Use descriptive branch names, following this convention:

```
<name>/<ticket-id-on-Notion>-<short-description>
```

Example:

```
ethan/17-gemini-api
jay/15-data_selection
```

#### 2. **Creating a PR**

How to compose a PR:

- Title: use the same format as your latest commit
- Body:
  - **Summary** (optional, recommended for a long PR)
  - **What**: What this PR does?
  - **Why**: Why this change is necessary?
  - **How to test**: (optional) Steps to test the PR.
  - **Linked Issues** (optional)
  - **Checklist** (optional)

```markdown
## Summary (optional)

### What
Implements OAuth2 login for user accounts

### Why
To allow third-party authentication and reduce sign-up friction

### How to test (optional)
- Go to XXX.
- Use command `python xxx.py --data xxx` to XXX.
- Ensure XXX / Confirm an output saved under XXX.

### Linked Issues (optional)
Closes #17

### Checklist (optional)
- [x] Unit tests
- [x] Lint passed
- [ ] Docs updated
```

### Review & Merge Process

1. **Open PR as Draft** if not finished
2. Add reviewers once ready
3. Address all comments and push changes
<!-- 4. **Rebase or squash** before merging (to keep history clean)
5. Merge with:
   - `Squash & merge` for single commit in `main`
   - `Rebase & merge` for linear history (if rebased manually)
   - Avoid `Create a merge commit` unless you need full history -->

### Tips

- Pull first, commit early, push often, but PR only when ready for review.
- Use `.gitignore` to avoid tracking heavy logs, datasets, credentials.
- Never commit secrets or large data.
<!-- - Use `git rebase -i` to clean up commits before final push. -->
