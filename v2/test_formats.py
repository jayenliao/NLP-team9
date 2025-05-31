#!/usr/bin/env python3
"""
Test all format combinations
"""

from format_handlers import FormatHandler

# Test data
question = "What is the capital of France?"
choices = ["London", "Paris", "Berlin", "Madrid"]

handler = FormatHandler()

formats = ["base", "json", "xml"]

print("Testing all 9 format combinations:\n")

for in_fmt in formats:
    for out_fmt in formats:
        print(f"\n{'='*60}")
        print(f"Format: {in_fmt} -> {out_fmt}")
        print(f"{'='*60}")
        
        try:
            prompt = handler.format_prompt(
                question, choices, in_fmt, out_fmt, "en"
            )
            print(prompt)
            
            # Test parsing too
            if out_fmt == "base":
                test_response = "The answer is B) Paris. Answer: B"
            elif out_fmt == "json":
                test_response = '```json\n{"answer": "B"}\n```'
            else:  # xml
                test_response = '```xml\n<answer>B</answer>\n```'
            
            parsed = handler.parse_response(test_response, out_fmt, "en")
            print(f"\nTest parse result: {parsed}")
            
        except Exception as e:
            print(f"Error: {e}")