# Wording for different language

'''
Problem:
- Should type name in structured prompts in different languages? (Currently all English)
'''

INTRO = {
    "EN-US": "Answer the following multiple choice question.",
    "FR-FR": "Répondez à la question à choix multiples suivante."
}

INSTRUCTION = {
    "EN-US": "The last line of your response should be of the following format: 'Answer: $LETTER' (without quotes) where LETTER is one of ABCD. Think step by step before answering.",
    "FR-FR": "La dernière ligne de votre réponse doit être au format suivant : « Réponse : $LETTRE » (sans les guillemets). Réfléchissez étape par étape avant de répondre."
}

CHOICE = {
    "EN-US": "choices",
    "FR-FR": "choix"
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
</question>
""".strip()

QUERY_TEMPLATE_JSON = """
// {Intro}
// {Instruction}

{
  "question": "{Question}",
  "choices": {
    "A": "{A}",
    "B": "{B}",
    "C": "{C}",
    "D": "{D}"
  }
}
""".strip()
