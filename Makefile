gen-params:
<<<<<<< HEAD
<<<<<<< HEAD
	python commands/gen_params.py commands/param_set.json -o commands/params.json --format json

filter-results:
	python ./experiments/fix_filter.py

rerun:
	python experiments/fix_rerun.py

check-failure:
	python experiments/fix_check_manual.py

concact:
	python experiments/fix_concact.py

print-to-filter:
	python experiments/fix_print_list.py filter
print-to-rerun:
	python experiments/fix_print_list.py rerun
print-to-manual-fix:
	python experiments/fix_print_list.py manual
print-to-concact:
	python experiments/fix_print_list.py concact
print-to-analyze:
	python experiments/fix_print_list.py analyze		
=======
	python commands/gen_params.py commands/param_set.json -o commands/params.json --format json
>>>>>>> c82644e (chore(all): rebasing main)
=======
	python commands/gen_params.py commands/param_set.json -o commands/params.json --format json

filter-results:
	python ./experiments/fix_1_filter.py

rerun:
	python experiments/fix_2_rerun.py

check-manual:
	python experiments/fix_3_check_manual.py

concact:
	python experiments/fix_4_concact.py
>>>>>>> f8f11c9 (chore(.gitignore): rebasing)
