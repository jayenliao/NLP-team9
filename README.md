# NLP-team9 Project: Order Sensitivity across Input-Output Formats

## Overview

This is the final project of NLP, a course at National Taiwan University (Spring 2025). We are team 9. Our project aims to investigate LLM's order sensitivity across input-output Formats and two languages, namely English and French.

### Team Members

- 盧音孜 / R13922A09 / r13922A09@csie.ntu.edu.tw
- 莊英博（Ethan）/ R13922A24 / ethan40125bard@gmail.com
- 廖傑恩（Jay）/ R13922210 / jay.chiehen@gmail.com

### Timeline

- Proposal: 09:45 on May 15
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
    conda create --name nlp_team9 python3
    conda activate nlp_team9
    ```

- Install required python dependencies.

    ```bash
    pip3 install -r requirements.txt
    ```

### Source Code Structure (Draft)

```plaintext
├──nlp-team9/      # The repo root
│   ├── prompts/                # 存放不同 input/output 格式的 prompt templates
│   │   ├── base_prompt.txt        # Free-text 格式 prompt
│   │   ├── json_prompt.txt        # JSON 格式 prompt
│   │   └── xml_prompt.txt         # XML 格式 prompt
│
│   ├── experiments/            # Scripts for running experiments
│   │   ├── run_mistral.py         # Main program for calling Mistral API
│   │   ├── run_gemini.py          # Main program for calling Gemini API
│   │   └── utils.py               # Utils for dealing with dataset loading, format transformation, logging, etc.
│
│   ├── results/               # 儲存所有實驗結果（**TODO**用 JSON or CSV or ????）
│   │   ├── base_en_mistral.json   # Results of Free-text format / English / Mistral
│   │   ├── json_ja_gemini.json    # Results of JSON format / Japanese / Gemini
│   │   └── ...                    # 依模型、語言、格式命名
│
│   ├── analysis/                # Scripts for doing analysis and visualization
│   │   ├── compute_ckld.py           # 計算 CKLD（Choice KL Divergence）
│   │   ├── fluctuation_rate.py       # 計算 Fluctuation Rate
│   │   └── summarize_results.ipynb   # 不同語言/格式的視覺化分析
│
│   ├── .gitignore
│   ├── requirements.txt  # Required dependencies
└────── README.md         # This file
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
<type>/<ticket-id-on-Notion>-<short-description>
```

Example:

```
feat/17-user-auth
fix/21-button-click-bug
docs/29-update-usage-intructions
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
