# Steps
0. At root dir install plotly `pip install plotly`, then `cd analysis_new`
1. Download datast by `python download_dataset.py`, results will save in `ds_saved/`
2. Complete dataset analysis (340 rows) by `python analyze.py`, it will output `rsd_by_group.csv`
3. To use plotly to see plots for results: `python plot.py`. Change the variable `targets` and `plot_spec` to revise the plot target and plot specs. It will results in `len(targets)` of pages with each page `len(plot_specs)` of plots.
    - `targets`: which group of data and how to split them
    - `plot_specs`: what values to be compared and plot as x and y.