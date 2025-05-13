gen-params:
	python commands/gen_params.py commands/param_set.json -o commands/params.json --format json

filter-results:
	python ./experiments/fix_1_filter.py

rerun:
	python experiments/fix_2_rerun.py

check-manual:
	python experiments/fix_3_check_manual.py

concact:
	python experiments/fix_4_concact.py