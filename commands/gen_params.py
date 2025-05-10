import json
import itertools
import argparse

def match_constraint(combo, constraint):
    for key, value in constraint.items():
        if combo.get(key) != value:
            return False
    return True

def satisfies_constraints(combo, constraints):
    if not constraints:
        return True
    for constraint in constraints:
        # 如果 combo 中有觸發 constraint 條件的 key，就必須 match 全部
        if all(k in combo for k in constraint):
            if match_constraint(combo, constraint):
                continue
            else:
                return False
    return True

def expand_ranges(properties):
    expanded = {}
    for key, value in properties.items():
        if isinstance(value, dict) and "range" in value:
            start, stop, step = value["range"]
            expanded[key] = list(range(start, stop, step))
        else:
            expanded[key] = value
    return expanded

def matches_condition(combo, condition):
    return all(combo.get(k) == v for k, v in condition.items())

def satisfies_include_constraints(combo, include_rules):
    for rule in include_rules:
        if matches_condition(combo, rule["if"]):
            for key, allowed_values in rule["then"].items():
                if combo.get(key) not in allowed_values:
                    return False
    return True

def violates_exclude_constraints(combo, exclude_rules):
    for rule in exclude_rules:
        if matches_condition(combo, rule["if"]):
            for key, disallowed_values in rule["then"].items():
                if combo.get(key) in disallowed_values:
                    return True
    return False

def generate_combinations(properties, constraints):
    concat_fields = properties.get("concat_fields", [])
    properties = expand_ranges({k: v for k, v in properties.items() if k not in ("constraints", "include_if", "exclude_if", "concat_fields")})
    keys = list(properties.keys())
    all_products = itertools.product(*(properties[k] for k in keys))
    all_combos = [dict(zip(keys, prod)) for prod in all_products]

    include_rules = constraints.get("include_if", [])
    exclude_rules = constraints.get("exclude_if", [])
    constraint_rules = constraints.get("constraints", [])
    valid_combos = [
        c for c in all_combos
        if satisfies_include_constraints(c, include_rules)
        and not violates_exclude_constraints(c, exclude_rules)
        # and satisfies_constraints(c, constraint_rules)
    ]
    i = 0
    if concat_fields:
        for combo in valid_combos:
            if combo["subtask"] == "all" and combo["delay"] == 5:
                #if combo["num_questions"] == 100 or combo["num_questions"] == 1:
                basename = "default-" + "".join(["t17", "q" + str(combo["num_questions"]), "p" + str(combo["num_permutations"])])
                combo["exp_name"] =  basename + "-" + combo["model_family"]
                combo["output_file"] = combo["model_name"] + "_" + basename
                # print(combo)
            elif combo["subtask"] == "abstract_algebra" and combo["delay"] == 5:
                basename = "default-" + "".join([ "t1", "q" + str(combo["num_questions"]), "p" + str(combo["num_permutations"])])
                combo["exp_name"] = basename + "-" + combo["model_family"]
                combo["output_file"] = combo["model_name"] + "_" + basename
                # print(combo)
            else:         
                combo["exp_name"] = "_".join(str(combo[k]) for k in concat_fields)
                combo["output_file"] = combo["model_name"]
            for k in combo:
                combo[k] = str(combo[k])
            combo["id"] = i
            i += 1

    return valid_combos

def main():
    parser = argparse.ArgumentParser(description="Generate constrained property combinations.")
    parser.add_argument("input", help="Input JSON file with properties and constraints")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--format", choices=["json", "jsonl"], default="json", help="Output format")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    constraints = {
        "include_if": data.get("include_if", []),
        "exclude_if": data.get("exclude_if", []),
        "constraints": data.get("constraints", [])
    }
    combinations = generate_combinations(data, constraints)
    
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            if args.format == "json":
                json.dump(combinations, f, indent=2, ensure_ascii=False)
            else:
                for item in combinations:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
    else:
        for item in combinations:
            print(json.dumps(item, ensure_ascii=False))

    print("Total Experiment Params:", len(combinations))

if __name__ == "__main__":
    main()
