#!/bin/bash

# Usage: ./retry.sh <subtask> <model> <format> <lang> [num_questions]
# Example: ./retry.sh task1 mymodel json en 10

if [ "$#" -lt 4 ] || [ "$#" -gt 5 ]; then
    echo "Usage: $0 <subtask> <model> <format> <lang> [num_questions]"
    exit 1
fi

subtask="$1"
model="$2"
format="$3"
lang="$4"

cmd="python ../../../v2/cli.py run --subtask \"$subtask\" --model \"$model\" --format \"$format\" --\"$lang\""

if [ "$#" -eq 5 ]; then
    num_questions="$5"
    cmd="$cmd --num-questions $num_questions"
fi

safe_format=$(echo "$format" | tr '/' '_')
filename="${subtask}_${model}_${safe_format}_${lang}"
mkdir "multiple_results"
cd "multiple_results"
echo "$filename"
mkdir "$filename"
cd $filename
# Not supported in `sh` — for Bash only:
for ((i=0; i<5; i++)); do
  mkdir $i
  cd $i
  eval $cmd
  cd ..
done

