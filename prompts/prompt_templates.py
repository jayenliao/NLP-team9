# Wording for different language

'''
Problem:
- Should type name in structured prompts in different languages? (Currently all English)
'''

INTRO = {
    "en": "Answer the following multiple choice question.",
    "fr": "Répondez à la question à choix multiples suivante."
}

INSTRUCTION = {
    "en": "The last line of your response should be your answer of the following format: 'Answer: $LETTER' (without quotes) where LETTER is one of ABCD. Think step by step before answering.",
    "fr": "La dernière ligne de votre réponse doit être au format suivant : « Réponse : $LETTRE » (sans les guillemets). Réfléchissez étape par étape avant de répondre."
}

INSTRUCTION_FORMATTED = {
    "en": "The last line of your response should be your answer in the format specified below. Think step by step before answering.",
    "fr": "La dernière ligne de votre réponse doit être votre réponse au format spécifié ci-dessous. Réfléchissez étape par étape avant de répondre."
}

CHOICE = {
    "en": "choices",
    "fr": "choix"
}

EXPLANATION = {
    "en": "Explain here.",
    "fr": "Expliquez ici."
}

ANSWER_FORMAT_PROMPT = {
    "en": "Answer format",
    "fr": "Format de réponse"
}

ANSWER_XML = """
<answer>A | B | C | D</answer>
""".strip()

ANSWER_JSON = """
  {
    "answer": "A | B | C | D",
  }
""".strip()

ANSWER_BASE = {
    "base": {
        "en": "'Answer: $LETTER' (without quotes) where LETTER is one of ABCD",
        "fr": "« Réponse : $LETTRE » (sans les guillemets) où LETTRE est l'une des lettres ABCD"
    } 
}
# Template

QUERY_TEMPLATE_BASE_BASE_EN = """
{Intro}
{Instruction}

{Question}

A) {A}
B) {B}
C) {C}
D) {D}

Answer format: 'Answer: $LETTER' (without quotes) where LETTER is one of ABCD.
""".strip()

QUERY_TEMPLATE_BASE_BASE_FR = """
{Intro}
{Instruction}

{Question}

A) {A}
B) {B}
C) {C}
D) {D}

Format de réponse: « Réponse : $LETTRE » (sans les guillemets) où LETTRE est l'une des lettres ABCD
""".strip()

QUERY_TEMPLATE_BASE_JSON = """
{Intro}
{Instruction}

{Question}

A) {A}
B) {B}
C) {C}
D) {D}

{AnswerFormat}: 
```json
  {{
    "step_by_step_reasoning": ...,
    "answer": "A | B | C | D",
  }}
```
""".strip()

QUERY_TEMPLATE_BASE_XML = """
{Intro}
{Instruction}

{Question}

A) {A}
B) {B}
C) {C}
D) {D}

{AnswerFormat}: 
```xml
  <response>
    <step_by_step_reasoning>...</step_by_step_reasoning>
    <answer>A | B | C | D</answer>
  </response>
```
""".strip()

QUERY_TEMPLATE_XML_BASE_EN = """
<!--
{Intro}
{Instruction}
-->

<question>
  <text>{Question}</text>
  <choices>
    <A>{A}</A>
    <B>{B}</B>
    <C>{C}</C>
    <D>{D}</D>
  </choices>
  <answer_format>
    <format>
      'Answer: $LETTER' (without quotes) where LETTER is one of ABCD
    </format>
  </answer_format>
</question>
""".strip()

QUERY_TEMPLATE_XML_JSON = """
<!--
{Intro}
{Instruction}
-->

<question>
  <text>{Question}</text>
  <choices>
    <A>{A}</A>
    <B>{B}</B>
    <C>{C}</C>
    <D>{D}</D>
  </choices>
  <answer_format>
    <format>
      {{
        "answer": "A | B | C | D",
      }}
    </format>
  </answer_format>
</question>
""".strip()

QUERY_TEMPLATE_XML_XML = """
<!--
{Intro}
{Instruction}
-->

<question>
  <text>{Question}</text>
  <choices>
    <A>{A}</A>
    <B>{B}</B>
    <C>{C}</C>
    <D>{D}</D>
  </choices>
  <answer_format>
    <format>
      <answer>A | B | C | D</answer>
    </format>
  </answer_format>
</question>
""".strip()


QUERY_TEMPLATE_XML_BASE_FR = """
<!--
{Intro}
{Instruction}
-->

<question>
  <text>{Question}</text>
  <choices>
    <A>{A}</A>
    <B>{B}</B>
    <C>{C}</C>
    <D>{D}</D>
  </choices>
  <answer_format>
    <format>
      « Réponse : $LETTRE » (sans les guillemets) où LETTRE est l'une des lettres ABCD
    </format>
  </answer_format>
</question>
""".strip()


QUERY_TEMPLATE_JSON_BASE_EN = """
// "{Intro}"
// "{Instruction}"

{{
  "question": "{Question}",
  "choices": {{
    "A": "{A}",
    "B": "{B}",
    "C": "{C}",
    "D": "{D}"
  }},
  "answer_format": "'Answer: $LETTER' (without quotes) where LETTER is one of ABCD."
 }}
""".strip()

QUERY_TEMPLATE_JSON_BASE_FR = """
// "{Intro}"
// "{Instruction}"

{{
  "question": "{Question}",
  "choices": {{
    "A": "{A}",
    "B": "{B}",
    "C": "{C}",
    "D": "{D}"
  }},
  "answer_format": "« Réponse : $LETTRE » (sans les guillemets) où LETTRE est l'une des lettres ABCD."
 }}
""".strip()

QUERY_TEMPLATE_JSON_JSON = """
// "{Intro}"
// "{Instruction}"

{{
  "question": "{Question}",
  "choices": {{
    "A": "{A}",
    "B": "{B}",
    "C": "{C}",
    "D": "{D}"
  }},
  "answer_format": {{
    "answer": "A | B | C | D",
  }}
 }}
""".strip()

QUERY_TEMPLATE_JSON_XML = """
// "{Intro}"
// "{Instruction}"

{{
  "question": "{Question}",
  "choices": {{
    "A": "{A}",
    "B": "{B}",
    "C": "{C}",
    "D": "{D}"
  }},
  "answer_format": <answer>A | B | C | D</answer>
 }}
""".strip()