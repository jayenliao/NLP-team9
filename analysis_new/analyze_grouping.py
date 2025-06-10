import pandas as pd
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import math

def init_list(target, filter_cols, columns, merge_format):
    df = pd.read_csv('rsd_by_group.csv')
    pertask = []
    if len(filter_cols) != 0:
        for fi in filter_cols:
            # print(fi)
            df = df[df[fi[0]] == fi[1]]
    for subgroup_val, group_df in df.groupby(target):
        task = {}
        for i in range(0, len(target)):
            task[target[i]] = subgroup_val[i]
        for col in columns:
            task[col] = round(group_df[col].mean(), 3)
        pertask.append(task)
    return pertask

class Analyze:
    def __init__(self, target, split, filter_cols, columns, merge_format = False):
        self.target = target
        self.split = split
        self.columns = columns
        self.filter = filter_cols
        self.df = pd.DataFrame(init_list(target + split, filter_cols, columns, merge_format))
        # pass
    def draw_plot(self, plot_specs):
        # Check valid
        valid_specs = []
        df = self.df
        for spec in plot_specs:
            if spec[0] not in df.columns or spec[1] not in df.columns:
                print(f"Skipping plot '{spec[2]}' — column missing: {spec[0] if spec[0] not in df.columns else spec[1]}")
                continue
            valid_specs.append(spec)
        n = len(valid_specs)
        rows = 2  # or 3, depending on layout preference
        cols = math.ceil(n / rows)

        df["combined_label"] = df[self.target].apply(lambda row: "_".join(map(str, row)), axis=1)
        df["combined_split"] = df[self.split].apply(lambda row: "_".join(map(str, row)), axis=1)

        unique_labels = df["combined_label"].unique()
        color_seq = px.colors.qualitative.Alphabet  # or Set3, D3, etc.
        label2color = {label: color_seq[i % len(color_seq)] for i, label in enumerate(unique_labels)}

        unique_langs = df["combined_split"].unique()
        symbols = ["circle", "square", "diamond", "cross", "x", "triangle-up", "triangle-down"]
        lang2symbol = {lang: symbols[i % len(symbols)] for i, lang in enumerate(unique_langs)}

        df["color"] = df["combined_label"].map(label2color)
        df["symbol"] = df["combined_split"].map(lang2symbol)

        fig = make_subplots(rows=rows, cols=cols, subplot_titles=[t[2] for t in valid_specs])

        for i, (xkey, ykey, title, xmin, xmax, ymin, ymax) in enumerate(valid_specs):
            row = i // cols + 1
            col = i % cols + 1
            x = df[xkey]
            y = df[ykey]
            hover = df["combined_label"] + df["combined_split"]
            colors = df["combined_label"].map(label2color)

            fig.add_trace(
                go.Scatter(
                    x=df[xkey], y=df[ykey], mode="markers",
                    marker=dict(color=df["color"], symbol=df["symbol"], size=8),
                    text=df[self.target], textposition="top center", name=title,
                    showlegend=False
                ),
                row=row, col=col
            )
            fig.update_xaxes(range=[xmin, xmax], title_text=xkey, row=row, col=col)
            fig.update_yaxes(range=[ymin, ymax], title_text=ykey, row=row, col=col)

        for task, color in label2color.items():
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(color=color, size=8),
                name=f"task: {task}",
                showlegend=True
            ))

        # Legend for language (symbol)
        for lang, symbol in lang2symbol.items():
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode="markers",
                marker=dict(color="gray", symbol=symbol, size=8),
                name=f"split: {lang}",
                showlegend=True
            ))

        title_text = "_".join(self.target)
        for f in self.filter:
            title_text += "_" + f[0] + "_" + f[1]
        fig.update_layout(height=800, width=2000, title=title_text)
        fig.show()

# Replace 'filename.csv' with your actual file path
# df = pd.read_csv('rsd_by_group.csv')

# # Display the first few rows
# # print(df.head())
# # columns = ["accuracy", "avg_word_count", "accuracy_A", "accuracy_B", "accuracy_C", "accuracy_D", "FR", "RSD"]
# pertask = []
# for subtask, group_df in df.groupby("subtask"):
#     acc = round(group_df["accuracy"].mean(), 3)
#     word = round(group_df["avg_word_count"].mean(), 3)
#     acc_a = round(group_df["accuracy_A"].mean(), 3)
#     acc_b = round(group_df["accuracy_B"].mean(), 3)
#     acc_c = round(group_df["accuracy_C"].mean(), 3)
#     acc_d = round(group_df[columns[5]].mean(), 3)
#     fr = round(group_df["FR"].mean(), 3)
#     RSD = round(group_df["RSD"].mean(), 3)
#     task = {
#         "subtask": subtask,
#         "acc": acc,
#         "acc_A": acc_a,
#         "acc_B": acc_b,
#         "acc_C": acc_c,
#         "acc_D": acc_d,
#         "word": word,
#         "fr": fr,
#         "RSD": RSD,
#     }
#     pertask.append(task)

# # print(f"{'subtask':<35} {'accuracy':<9} {'avg_word':<9} {'FR':<9} {'RSD':<9}")
# # print("-" * 90)

# # for task in pertask:
# #     subtask = task["subtask"]
# #     acc = task["acc"]
# #     word = task["word"]
# #     FR = task["fr"]
# #     RSD = task["RSD"]
# #     print(f"{subtask:<35} {acc:<9} {word:<9} {FR:<9} {RSD:<9}")
#     # print(subtask, group_df["accuracy"].mean(), group_df["avg_word_count"].mean())

# # drawing = pd.DataFrame(pertask)


# df = pd.DataFrame(pertask)

# # Define (x, y, x_label, y_label, title)
# plot_specs = [
#     ("acc", "word", "acc", "word", "acc vs word_count"),
#     ("acc", "RSD", "acc", "RSD", "acc vs RSD"),
#     ("acc", "fr", "acc", "fr", "acc vs Fluctuation Rate"),
#     ("fr", "word", "fr", "word", "Fluctuation Rate vs word_count"),
#     ("acc", "acc_A", "acc", "acc_A", "acc vs acc_A"),
#     ("acc", "acc_B", "acc", "acc_B", "acc vs acc_B"),
#     ("acc", "acc_C", "acc", "acc_C", "acc vs acc_C"),
#     ("acc", "acc_D", "acc", "acc_D", "acc vs acc_D")
# ]

# n = len(plot_specs)
# rows = 2  # or 3, depending on layout preference
# cols = math.ceil(n / rows)

# unique_labels = df["subtask"].unique()
# color_seq = px.colors.qualitative.Set2  # or Set3, D3, etc.
# label2color = {label: color_seq[i % len(color_seq)] for i, label in enumerate(unique_labels)}

# fig = make_subplots(rows=rows, cols=cols, subplot_titles=[t[4] for t in plot_specs])

# for i, (xkey, ykey, xlabel, ylabel, title) in enumerate(plot_specs):
#     row = i // cols + 1
#     col = i % cols + 1

#     x = df[xkey]
#     y = df[ykey]
#     hover = df["subtask"]
#     colors = df["subtask"].map(label2color)

#     fig.add_trace(
#         go.Scatter(
#             x=df[xkey], y=df[ykey], mode="markers",
#             marker=dict(color=colors, size=8),
#             text=df["subtask"], textposition="top center", name=title,
#             showlegend=False
#         ),
#         row=row, col=col
#     )
#     fig.update_xaxes(title_text=xlabel, row=row, col=col)
#     fig.update_yaxes(title_text=ylabel, row=row, col=col)

# for label, color in label2color.items():
#     fig.add_trace(
#         go.Scatter(
#             x=[None], y=[None],  # no visible point
#             mode='markers',
#             marker=dict(color=color, size=8),
#             name=label,
#             showlegend=True
#         )
#     )

# fig.update_layout(height=800, width=1600, title="Subtask Scatter Plots")
# fig.show()
