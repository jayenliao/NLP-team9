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
    "en": "The last line of your response should be of the following format: 'Answer: $LETTER' (without quotes) where LETTER is one of ABCD. Think step by step before answering.",
    "fr": "La dernière ligne de votre réponse doit être au format suivant : « Réponse : $LETTRE » (sans les guillemets). Réfléchissez étape par étape avant de répondre."
}

CHOICE = {
    "en": "choices",
    "fr": "choix"
}

EXPLANATION = {
    "en": "Explain here.",
    "fr": "Expliquez ici."
}

ANSWER_XML = """
<answer format="xml">
  <template>
    <![CDATA[
<response>
  <answer>A | B | C | D</answer>
  <explanation>{Explaination}</explanation>
</response>
    ]]>
  </template>
</answer>
""".strip()

ANSWER_JSON = """
{
  "answer": {
    "format": "json",
    "template": {
      "response": {
        "answer": "A | B | C | D",
        "explanation": "{Explaination}"
      }
    }
  }
}
""".strip()
ANSWERFORMAT = {
    "base": {
        "en": "'Answer: $LETTER' (without quotes) where LETTER is one of ABCD",
        "fr": "« Réponse : $LETTRE » (sans les guillemets) où LETTRE est l'une des lettres ABCD"
    } 
}
# Template

QUERY_TEMPLATE_PLAIN = """
{Intro}
{Instruction}

{Question}

A) {A}
B) {B}
C) {C}
D) {D}

{Answer_format}
""".strip()

QUERY_TEMPLATE_XML = """
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
    <format>{AnswerFormat}</format>
  </answer_format>
</question>
""".strip()

QUERY_TEMPLATE_JSON = """
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
  "answer_format": "{AnswerFormat}"
 }}
""".strip()
