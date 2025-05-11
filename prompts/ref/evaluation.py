import pickle
from . import common
from .common import (
    HTML_JINJA,
    MULTILINGUAL_ANSWER_PATTERN_TEMPLATE,
    MULTILINGUAL_ANSWER_REGEXES,
    format_multichoice_question,
    normalize_extracted_answer,
    normalize_response,
)

with open("../data/ds_selected.pkl", "rb") as f:
    dataset = pickle.load(f)

style = "json"  # "plain", "json", "xml"
results = []

for (lang, category), samples in dataset.items():
    for row in samples:
        prompt = format_multichoice_question(row, style=style)
        convo = [dict(role="user", content=prompt)]
        
        # 呼叫你原本的評測方法，這裡是假設
        response = sampler(convo)  # 或你的 evaluator 方法
        extracted_answer = extract_answer(response)
        correct = normalize_extracted_answer(row["Answer"])
        score = float(extracted_answer.strip() == correct.strip())

        results.append({
            "lang": lang,
            "category": category,
            "prompt": prompt,
            "response": response,
            "correct_answer": correct,
            "extracted_answer": extracted_answer,
            "score": score
        })

