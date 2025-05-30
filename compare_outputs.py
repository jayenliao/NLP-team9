import json
import sys

def compare_jsonl_files(file1, file2):
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        lines1 = f1.readlines()
        lines2 = f2.readlines()
    
    if len(lines1) != len(lines2):
        print(f"Different number of lines: {len(lines1)} vs {len(lines2)}")
        return False
    
    for i, (line1, line2) in enumerate(zip(lines1, lines2)):
        obj1 = json.loads(line1)
        obj2 = json.loads(line2)
        
        # Compare key fields (ignore trial_id which is always different)
        for key in ['question_id', 'subtask', 'language', 'model_name', 
                    'input_format', 'output_format', 'option_permutation',
                    'ground_truth_answer']:
            if obj1.get(key) != obj2.get(key):
                print(f"Line {i}: Mismatch in {key}")
                print(f"  Old: {obj1.get(key)}")
                print(f"  New: {obj2.get(key)}")
                return False
    
    print("✅ Output formats match!")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_outputs.py file1.jsonl file2.jsonl")
        sys.exit(1)
    
    compare_jsonl_files(sys.argv[1], sys.argv[2])