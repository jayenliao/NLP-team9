import sys
import os

def main():
    # Mapping of arguments to file names
    file_mapping = {
        "filter": "0-to-Filter",
        "rerun": "1-to-Rerun",
        "manual": "2-to-Manual-Fix",
        "concact": "3-to-Concact",
        "analyze": "4-to-Analyze"
    }

    # Check if the user provided an argument
    if len(sys.argv) != 2:
        print("Usage: python fix_print_list.py <filter|rerun|manual|concact|analyze>")
        sys.exit(1)

    # Get the argument and map it to the corresponding file
    argument = sys.argv[1]
    if argument not in file_mapping:
        print(f"Invalid argument: {argument}")
        print("Valid arguments are: filter, rerun, manual, concact, analyze")
        sys.exit(1)

    # Construct the file path
    file_name = file_mapping[argument]
    file_path = os.path.join("results", "__logs__", file_name)

    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        sys.exit(1)

    # Read and print the file content
    total_lines = 0
    with open(file_path, "r") as file:
        for line in file:
            print(line.strip())
            total_lines += 1

    # Print the total number of experiments
    print(f"\nTotal {total_lines} of experiments to {argument}.")

if __name__ == "__main__":
    main()