gen-params:
	python commands/gen_params.py commands/param_set.json -o commands/params.json --format json

filter-results:
	python ./experiments/fix_filter.py

rerun:
	python experiments/fix_rerun.py

check-manual:
	python experiments/fix_check_manual.py

concact:
	python experiments/fix_concact.py