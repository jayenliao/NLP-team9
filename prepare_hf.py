import json
from pathlib import Path
from datetime import datetime

print("🚀 Starting dataset preparation...")

# Check if v2_results exists
v2_results = Path("v2_results")
if not v2_results.exists():
    print("❌ ERROR: v2_results directory not found!")
    print(f"   Looking in: {v2_results.absolute()}")
    exit(1)

# Count experiments
all_dirs = list(v2_results.iterdir())
print(f"📁 Found {len(all_dirs)} experiment directories")

# Process each one
all_results = []
for exp_dir in v2_results.iterdir():
    if exp_dir.is_dir():
        final_jsonl = exp_dir / "final.jsonl"
        if final_jsonl.exists():
            print(f"✓ Found: {exp_dir.name}")
            with open(final_jsonl) as f:
                for line in f:
                    result = json.loads(line)
                    # Fix question_id to string
                    result['question_id'] = str(result['question_id'])
                    all_results.append(result)
        else:
            print(f"✗ Missing: {exp_dir.name}")

print(f"\n📊 Total results: {len(all_results)}")

# Save the file
with open("dataset_for_huggingface.jsonl", "w") as f:
    for result in all_results:
        f.write(json.dumps(result) + "\n")

print("✅ Saved to dataset_for_huggingface.jsonl")

#huggingface-cli upload r13922a24/nlptestrun dataset_for_huggingface.jsonl data/results.jsonl --repo-type=dataset