
import os
import csv
import tkinter as tk
from tkinter import ttk, messagebox

import matplotlib
matplotlib.use("TkAgg")

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# ==========================================================
# 1. PROJECT PATHS
# ==========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")

SUMMARY_FILE = os.path.join(
    RESULTS_DIR, "benchmark_summary.csv"
)

DETAILS_FILE = os.path.join(
    RESULTS_DIR, "benchmark_details.csv"
)

DASHBOARD_FILE = os.path.join(
    RESULTS_DIR, "dashboard_results.csv"
)

ALGORITHMS = ["BFS", "DFS", "A*"]

METRICS = [
    "Path Length",
    "Nodes Explored",
    "Execution Time",
    "Replanning",
    "Success Rate"
]


# ==========================================================
# 2. CSV READING
# ==========================================================

def read_csv(filename):

    if not os.path.exists(filename):
        return []

    try:
        with open(
            filename,
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as file:

            return list(csv.DictReader(file))

    except (OSError, csv.Error) as error:

        print("CSV reading error:", error)
        return []


def normalize(value):

    return "".join(
        character.lower()
        for character in str(value)
        if character.isalnum()
    )


def get_value(row, aliases):

    normalized_row = {
        normalize(key): value
        for key, value in row.items()
        if key is not None
    }

    # First try exact header matches
    for alias in aliases:

        key = normalize(alias)

        if key in normalized_row:
            return normalized_row[key]

    # Then try partial header matches
    for alias in aliases:

        key = normalize(alias)

        if not key:
            continue

        for column, value in normalized_row.items():

            if key in column:
                return value

    return None


def to_number(value):

    if value is None:
        return None

    try:

        value = str(value).strip()
        value = value.replace(",", "")
        value = value.replace("%", "")
        value = value.replace("seconds", "")
        value = value.replace("sec", "")
        value = value.strip()

        if value == "":
            return None

        return float(value)

    except (ValueError, TypeError):

        return None


def get_algorithm(row):

    value = get_value(
        row,
        ["Algorithm", "Algorithm Name", "Method"]
    )

    if value is None:
        return None

    value = str(value).strip().upper()

    if value in ["A*", "ASTAR", "A STAR"]:
        return "A*"

    if value in ["BFS", "DFS"]:
        return value

    return None


# ==========================================================
# 3. METRIC EXTRACTION
# ==========================================================

ALIASES = {

    "Path Length": [
        "Average Movements",
        "Avg Movements",
        "Actual Robot Movements",
        "Movements",
        "Path Length",
        "Average Path Length"
    ],

    "Nodes Explored": [
        "Average Nodes",
        "Avg Nodes",
        "Nodes Explored",
        "Total Nodes",
        "Nodes"
    ],

    "Execution Time": [
        "Average Time",
        "Avg Time",
        "Average Execution Time",
        "Execution Time Seconds",
        "Execution Time",
        "Search Time",
        "Time"
    ],

    "Replanning": [
        "Average Replanning",
        "Avg Replans",
        "Replanning Operations",
        "Replanning",
        "Replans"
    ],

    "Success Rate": [
        "Success Rate",
        "Success Rate Percent",
        "Success Percentage",
        "Success"
    ]
}


def get_metric(row, metric):

    value = get_value(row, ALIASES[metric])

    number = to_number(value)

    if number is None:
        return None

    if metric == "Success Rate":

        text = str(value).strip().lower()

        if text in ["yes", "true", "success", "successful"]:
            return 100.0

        if text in ["no", "false", "failed", "failure"]:
            return 0.0

        if 0 <= number <= 1:
            return number * 100

    return number


# ==========================================================
# 4. AGGREGATE BENCHMARK RESULTS
# ==========================================================

def aggregate_results(rows):

    grouped = {
        algorithm: {
            metric: []
            for metric in METRICS
        }
        for algorithm in ALGORITHMS
    }

    for row in rows:

        algorithm = get_algorithm(row)

        if algorithm not in ALGORITHMS:
            continue

        for metric in METRICS:

            value = get_metric(row, metric)

            if value is not None:

                grouped[algorithm][metric].append(
                    value
                )

    result = {}

    for algorithm in ALGORITHMS:

        result[algorithm] = {}

        for metric in METRICS:

            values = grouped[algorithm][metric]

            if values:

                result[algorithm][metric] = (
                    sum(values) / len(values)
                )

            else:

                result[algorithm][metric] = None

    return result


def has_benchmark_data(data):

    return any(
        data[algorithm][metric] is not None
        for algorithm in ALGORITHMS
        for metric in METRICS
    )


def load_benchmark_results():

    # Prefer pre-calculated summary
    summary_rows = read_csv(SUMMARY_FILE)

    summary_data = aggregate_results(summary_rows)

    if has_benchmark_data(summary_data):

        return summary_data, "Benchmark Summary"

    # Otherwise calculate averages from scenario details
    details_rows = read_csv(DETAILS_FILE)

    details_data = aggregate_results(details_rows)

    if has_benchmark_data(details_data):

        return details_data, "Benchmark Details (calculated averages)"

    # Last fallback: individual dashboard runs
    dashboard_rows = read_csv(DASHBOARD_FILE)

    dashboard_data = aggregate_results(dashboard_rows)

    if has_benchmark_data(dashboard_data):

        return dashboard_data, "Dashboard Runs (fallback only)"

    return {}, "No benchmark data found"


# ==========================================================
# 5. APPLICATION WINDOW
# ==========================================================

root = tk.Tk()

root.title(
    "Autonomous Robot - AI Comparative Analysis Dashboard"
)

root.geometry("1250x850")
root.minsize(950, 650)

root.configure(bg="#202636")


# ==========================================================
# 6. COLORS AND STYLES
# ==========================================================

BG = "#202636"
PANEL = "#293449"
BUTTON = "#405778"
WHITE = "#FFFFFF"
ACCENT = "#16B8C4"
GREEN = "#24C875"
YELLOW = "#F4C542"

style = ttk.Style()

style.theme_use("clam")

style.configure(
    "Treeview",
    background="#F2F4F8",
    foreground="#202636",
    rowheight=30,
    fieldbackground="#F2F4F8",
    font=("Arial", 10)
)

style.configure(
    "Treeview.Heading",
    background="#405778",
    foreground="white",
    font=("Arial", 10, "bold")
)


# ==========================================================
# 7. HEADER
# ==========================================================

header = tk.Frame(
    root,
    bg=BG,
    height=85
)

header.pack(fill="x")

tk.Label(
    header,
    text="ROBOT AI - PERFORMANCE ANALYSIS",
    bg=BG,
    fg=WHITE,
    font=("Arial", 23, "bold")
).pack(pady=(18, 3))

tk.Label(
    header,
    text="BFS  |  DFS  |  A*  |  Dynamic Obstacle Avoidance",
    bg=BG,
    fg=ACCENT,
    font=("Arial", 11)
).pack()


# ==========================================================
# 8. SUMMARY CARDS
# ==========================================================

cards_frame = tk.Frame(
    root,
    bg=BG
)

cards_frame.pack(
    fill="x",
    padx=15,
    pady=12
)

card_labels = {}

card_names = [
    "Best Algorithm",
    "Fastest Algorithm",
    "Minimum Nodes",
    "Success Rate"
]

for index, name in enumerate(card_names):

    card = tk.Frame(
        cards_frame,
        bg=PANEL,
        padx=10,
        pady=10
    )

    card.grid(
        row=0,
        column=index,
        padx=6,
        sticky="nsew"
    )

    cards_frame.grid_columnconfigure(
        index,
        weight=1
    )

    tk.Label(
        card,
        text=name,
        bg=PANEL,
        fg="#C5D0E0",
        font=("Arial", 10)
    ).pack()

    value_label = tk.Label(
        card,
        text="--",
        bg=PANEL,
        fg=GREEN,
        font=("Arial", 17, "bold")
    )

    value_label.pack(pady=6)

    card_labels[name] = value_label


# ==========================================================
# 9. SOURCE INFORMATION
# ==========================================================

source_label = tk.Label(
    root,
    text="Loading results...",
    bg=BG,
    fg=YELLOW,
    font=("Arial", 10)
)

source_label.pack(pady=3)


# ==========================================================
# 10. COMPARISON TABLE
# ==========================================================

table_frame = tk.Frame(
    root,
    bg=BG
)

table_frame.pack(
    fill="x",
    padx=20,
    pady=8
)

tk.Label(
    table_frame,
    text="ALGORITHM COMPARISON",
    bg=BG,
    fg=WHITE,
    font=("Arial", 15, "bold")
).pack(anchor="w", pady=5)

columns = (
    "Algorithm",
    "Path Length",
    "Nodes Explored",
    "Execution Time",
    "Replanning",
    "Success Rate"
)

tree = ttk.Treeview(
    table_frame,
    columns=columns,
    show="headings",
    height=3
)

for column in columns:

    tree.heading(
        column,
        text=column
    )

    tree.column(
        column,
        width=175,
        anchor="center"
    )

tree.pack(fill="x")


# ==========================================================
# 11. GRAPH AREA
# ==========================================================

graph_frame = tk.Frame(
    root,
    bg=BG
)

graph_frame.pack(
    fill="both",
    expand=True,
    padx=15,
    pady=10
)

figure = Figure(
    figsize=(11, 5.5),
    dpi=100,
    facecolor="white"
)

axes = figure.subplots(2, 2)

figure.tight_layout(pad=3.0)

canvas = FigureCanvasTkAgg(
    figure,
    master=graph_frame
)

canvas.get_tk_widget().pack(
    fill="both",
    expand=True
)


# ==========================================================
# 12. INDIVIDUAL DASHBOARD RUN HISTORY
# ==========================================================

history_window = None


def show_dashboard_history():

    global history_window

    if (
        history_window is not None
        and history_window.winfo_exists()
    ):

        history_window.lift()
        return

    history_window = tk.Toplevel(root)

    history_window.title(
        "Individual Dashboard Run History"
    )

    history_window.geometry("1050x450")

    history_window.configure(bg=BG)

    tk.Label(
        history_window,
        text="INDIVIDUAL ROBOT RUN HISTORY",
        bg=BG,
        fg=WHITE,
        font=("Arial", 17, "bold")
    ).pack(pady=12)

    rows = read_csv(DASHBOARD_FILE)

    history_columns = (
        "Date_Time",
        "Algorithm",
        "Success",
        "Initial_Path_Length",
        "Actual_Robot_Movements",
        "Nodes_Explored",
        "Execution_Time_Seconds",
        "Replanning_Operations"
    )

    history_table = ttk.Treeview(
        history_window,
        columns=history_columns,
        show="headings"
    )

    for column in history_columns:

        history_table.heading(
            column,
            text=column.replace("_", " ")
        )

        history_table.column(
            column,
            width=125,
            anchor="center"
        )

    for row in rows:

        history_table.insert(
            "",
            "end",
            values=[
                row.get(column, "")
                for column in history_columns
            ]
        )

    history_table.pack(
        fill="both",
        expand=True,
        padx=12,
        pady=12
    )

    if not rows:

        tk.Label(
            history_window,
            text="No dashboard runs found.",
            bg=BG,
            fg=YELLOW
        ).pack()


# ==========================================================
# 13. DRAW COMPARISON GRAPHS
# ==========================================================

def draw_graphs(data):

    graph_metrics = [
        "Path Length",
        "Nodes Explored",
        "Execution Time",
        "Replanning"
    ]

    for axis, metric in zip(
        axes.flatten(),
        graph_metrics
    ):

        axis.clear()

        values = [
            data[algorithm][metric]
            for algorithm in ALGORITHMS
        ]

        valid = [
            (algorithm, value)
            for algorithm, value in zip(
                ALGORITHMS,
                values
            )
            if value is not None
        ]

        if not valid:

            axis.text(
                0.5,
                0.5,
                "No data available",
                ha="center",
                va="center",
                transform=axis.transAxes
            )

            axis.set_title(metric)

            continue

        names = [
            item[0]
            for item in valid
        ]

        numbers = [
            item[1]
            for item in valid
        ]

        bars = axis.bar(
            names,
            numbers
        )

        axis.set_title(
            metric,
            fontsize=11,
            fontweight="bold"
        )

        axis.set_ylabel(metric)

        axis.grid(
            axis="y",
            alpha=0.25
        )

        for bar, value in zip(
            bars,
            numbers
        ):

            axis.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{value:.3f}",
                ha="center",
                va="bottom",
                fontsize=8
            )

    figure.tight_layout(pad=3)

    canvas.draw()


# ==========================================================
# 14. REFRESH COMPARISON
# ==========================================================

def refresh_dashboard():

    data, source = load_benchmark_results()

    source_label.config(
        text="Data Source: " + source
    )

    for item in tree.get_children():

        tree.delete(item)

    if not data:

        for name in card_names:

            card_labels[name].config(
                text="No data"
            )

        messagebox.showwarning(
            "No Results",
            "No readable benchmark data was found.\n"
            "Check the CSV files inside the results folder."
        )

        return

    for algorithm in ALGORITHMS:

        metrics = data[algorithm]

        def display(metric):

            value = metrics.get(metric)

            if value is None:
                return "N/A"

            if metric == "Success Rate":

                return f"{value:.2f}%"

            if metric == "Execution Time":

                return f"{value:.6f} sec"

            return f"{value:.2f}"

        tree.insert(
            "",
            "end",
            values=(
                algorithm,
                display("Path Length"),
                display("Nodes Explored"),
                display("Execution Time"),
                display("Replanning"),
                display("Success Rate")
            )
        )

    # Fastest algorithm
    times = {
        algorithm: data[algorithm]["Execution Time"]
        for algorithm in ALGORITHMS
        if data[algorithm]["Execution Time"] is not None
    }

    if times:

        fastest = min(
            times,
            key=times.get
        )

        card_labels["Fastest Algorithm"].config(
            text=fastest
        )

    else:

        card_labels["Fastest Algorithm"].config(
            text="N/A"
        )

    # Minimum nodes
    nodes = {
        algorithm: data[algorithm]["Nodes Explored"]
        for algorithm in ALGORITHMS
        if data[algorithm]["Nodes Explored"] is not None
    }

    if nodes:

        minimum = min(
            nodes,
            key=nodes.get
        )

        card_labels["Minimum Nodes"].config(
            text=minimum
        )

    else:

        card_labels["Minimum Nodes"].config(
            text="N/A"
        )

    # Success rate
    success_values = {
        algorithm: data[algorithm]["Success Rate"]
        for algorithm in ALGORITHMS
        if data[algorithm]["Success Rate"] is not None
    }

    if success_values:

        best_success = max(
            success_values,
            key=success_values.get
        )

        card_labels["Success Rate"].config(
            text=f"{success_values[best_success]:.1f}% ({best_success})"
        )

    else:

        card_labels["Success Rate"].config(
            text="N/A"
        )

    # Overall best based on multiple metrics.
    # Lower path length, nodes and time are better.
    # Higher success rate is better.
    metrics_for_ranking = [
        "Path Length",
        "Nodes Explored",
        "Execution Time"
    ]

    scores = {
        algorithm: 0
        for algorithm in ALGORITHMS
    }

    for metric in metrics_for_ranking:

        available = {
            algorithm: data[algorithm][metric]
            for algorithm in ALGORITHMS
            if data[algorithm][metric] is not None
        }

        if available:

            winner = min(
                available,
                key=available.get
            )

            scores[winner] += 1

    if success_values:

        winner = max(
            success_values,
            key=success_values.get
        )

        scores[winner] += 1

    best = max(
        scores,
        key=scores.get
    )

    card_labels["Best Algorithm"].config(
        text=best
    )

    draw_graphs(data)

    print("\nAnalysis dashboard refreshed.")
    print("Source:", source)
    print("Algorithm scores:", scores)


# ==========================================================
# 15. BUTTONS
# ==========================================================

button_frame = tk.Frame(
    root,
    bg=BG
)

button_frame.pack(
    fill="x",
    pady=12
)


def make_button(text, command):

    return tk.Button(
        button_frame,
        text=text,
        command=command,
        bg=BUTTON,
        fg=WHITE,
        activebackground=ACCENT,
        activeforeground=WHITE,
        font=("Arial", 10, "bold"),
        padx=15,
        pady=9,
        relief="flat",
        cursor="hand2"
    )


make_button(
    "REFRESH ANALYSIS",
    refresh_dashboard
).pack(side="left", padx=20)

make_button(
    "VIEW DASHBOARD RUNS",
    show_dashboard_history
).pack(side="left", padx=10)

make_button(
    "EXIT",
    root.destroy
).pack(side="right", padx=20)


# ==========================================================
# 16. START APPLICATION
# ==========================================================

refresh_dashboard()

root.mainloop()
