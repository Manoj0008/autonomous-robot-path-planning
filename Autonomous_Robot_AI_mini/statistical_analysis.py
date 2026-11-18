
import os
import itertools
import warnings

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from scipy.stats import t, wilcoxon

warnings.filterwarnings("ignore")

# ==================================================
# CONFIGURATION
# ==================================================

INPUT_FILE = os.path.join("results", "benchmark_details.csv")
OUTPUT_DIR = os.path.join("results", "statistical_analysis")

ALGORITHMS = ["BFS", "DFS", "A*"]

METRICS = [
    "movements",
    "nodes",
    "time",
    "replans"
]

CONFIDENCE_LEVEL = 0.95
ALPHA = 0.05

os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==================================================
# LOAD DATA
# ==================================================

def load_data():

    if not os.path.exists(INPUT_FILE):
        raise FileNotFoundError(
            f"Benchmark file not found: {INPUT_FILE}"
        )

    data = pd.read_csv(INPUT_FILE)

    required_columns = [
        "scenario",
        "algorithm",
        "success",
        "movements",
        "nodes",
        "time",
        "replans"
    ]

    missing = [
        col for col in required_columns
        if col not in data.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    data["algorithm"] = (
        data["algorithm"].astype(str).str.strip()
    )

    data["scenario"] = pd.to_numeric(
        data["scenario"], errors="coerce"
    )

    for metric in METRICS:
        data[metric] = pd.to_numeric(
            data[metric], errors="coerce"
        )

    if data["success"].dtype == object:
        data["success"] = (
            data["success"]
            .astype(str)
            .str.strip()
            .str.lower()
            .map({
                "true": True,
                "false": False,
                "1": True,
                "0": False,
                "yes": True,
                "no": False
            })
        )

    data["success"] = (
        data["success"].fillna(False).astype(bool)
    )

    data = data[
        data["algorithm"].isin(ALGORITHMS)
    ].copy()

    if data.duplicated(
        subset=["scenario", "algorithm"]
    ).any():
        raise ValueError(
            "Duplicate scenario-algorithm records found. "
            "Check benchmark_details.csv."
        )

    print("\nData loaded successfully.")
    print("Total records:", len(data))
    print(
        "Algorithms:",
        data["algorithm"].unique()
    )

    return data


# ==================================================
# CONFIDENCE INTERVAL CALCULATION
# ==================================================

def calculate_confidence_interval(values):

    values = pd.Series(values).dropna()

    count = len(values)
    mean_value = values.mean()
    std_value = values.std()

    if count < 2:
        return mean_value, mean_value

    standard_error = std_value / np.sqrt(count)

    degrees_of_freedom = count - 1

    critical_value = t.ppf(
        1 - (1 - CONFIDENCE_LEVEL) / 2,
        degrees_of_freedom
    )

    margin = critical_value * standard_error

    lower = mean_value - margin
    upper = mean_value + margin

    return lower, upper


# ==================================================
# DESCRIPTIVE STATISTICS
# ==================================================

def descriptive_statistics(data):

    records = []

    for algorithm in ALGORITHMS:

        algorithm_data = data[
            data["algorithm"] == algorithm
        ]

        for metric in METRICS:

            values = (
                algorithm_data[metric].dropna()
            )

            if values.empty:
                continue

            count = len(values)

            mean_value = values.mean()
            std_value = values.std()

            ci_low, ci_high = (
                calculate_confidence_interval(values)
            )

            records.append({
                "algorithm": algorithm,
                "metric": metric,
                "count": count,
                "mean": mean_value,
                "median": values.median(),
                "std_dev": std_value,
                "minimum": values.min(),
                "maximum": values.max(),
                "ci95_low": ci_low,
                "ci95_high": ci_high
            })

    summary = pd.DataFrame(records)

    output_file = os.path.join(
        OUTPUT_DIR,
        "descriptive_statistics.csv"
    )

    summary.to_csv(output_file, index=False)

    print("\nDescriptive statistics saved.")

    return summary


# ==================================================
# SUCCESS RATE
# ==================================================

def calculate_success_rate(data):

    success = (
        data.groupby("algorithm")["success"]
        .agg(["sum", "count"])
        .reset_index()
    )

    success["success_rate_percent"] = (
        success["sum"] / success["count"]
    ) * 100

    success.rename(
        columns={
            "sum": "successful_runs",
            "count": "total_runs"
        },
        inplace=True
    )

    success["algorithm"] = pd.Categorical(
        success["algorithm"],
        categories=ALGORITHMS,
        ordered=True
    )

    success = (
        success.sort_values("algorithm")
        .reset_index(drop=True)
    )

    success["algorithm"] = (
        success["algorithm"].astype(str)
    )

    output_file = os.path.join(
        OUTPUT_DIR,
        "success_rate.csv"
    )

    success.to_csv(output_file, index=False)

    print("\nSuccess rate:")
    print(success.to_string(index=False))

    return success


# ==================================================
# HOLM-BONFERRONI CORRECTION
# ==================================================

def holm_bonferroni(p_values):

    p_values = np.asarray(
        p_values, dtype=float
    )

    adjusted = np.full(
        len(p_values), np.nan
    )

    valid_indices = np.where(
        np.isfinite(p_values)
    )[0]

    if len(valid_indices) == 0:
        return adjusted

    valid_p = p_values[valid_indices]

    order = np.argsort(valid_p)

    sorted_p = valid_p[order]

    number_of_tests = len(sorted_p)

    adjusted_sorted = np.zeros(
        number_of_tests
    )

    running_max = 0.0

    for i, p_value in enumerate(sorted_p):

        corrected = (
            number_of_tests - i
        ) * p_value

        running_max = max(
            running_max, corrected
        )

        adjusted_sorted[i] = min(
            running_max, 1.0
        )

    adjusted_valid = np.empty(
        number_of_tests
    )

    adjusted_valid[order] = adjusted_sorted

    adjusted[valid_indices] = adjusted_valid

    return adjusted


# ==================================================
# PAIRED STATISTICAL COMPARISONS
# ==================================================

def paired_comparisons(data):

    records = []

    for metric in METRICS:

        for first, second in itertools.combinations(
            ALGORITHMS, 2
        ):

            first_data = data[
                data["algorithm"] == first
            ][["scenario", metric]]

            second_data = data[
                data["algorithm"] == second
            ][["scenario", metric]]

            paired = pd.merge(
                first_data,
                second_data,
                on="scenario",
                suffixes=("_first", "_second"),
                validate="one_to_one"
            ).dropna()

            first_values = paired[
                f"{metric}_first"
            ].to_numpy()

            second_values = paired[
                f"{metric}_second"
            ].to_numpy()

            p_value = np.nan
            statistic = np.nan

            if len(paired) >= 2:

                differences = (
                    first_values - second_values
                )

                if np.allclose(differences, 0):

                    statistic = 0.0
                    p_value = 1.0

                else:

                    try:
                        result = wilcoxon(
                            first_values,
                            second_values,
                            alternative="two-sided",
                            zero_method="wilcox",
                            method="auto"
                        )

                        statistic = result.statistic
                        p_value = result.pvalue

                    except ValueError:
                        pass

            records.append({
                "metric": metric,
                "comparison": f"{first} vs {second}",
                "paired_scenarios": len(paired),
                f"{first}_mean": (
                    np.mean(first_values)
                    if len(first_values) else np.nan
                ),
                f"{second}_mean": (
                    np.mean(second_values)
                    if len(second_values) else np.nan
                ),
                "wilcoxon_statistic": statistic,
                "p_value": p_value
            })

    comparison_df = pd.DataFrame(records)

    # Correct all available p-values together
    comparison_df["holm_adjusted_p_value"] = (
        holm_bonferroni(
            comparison_df["p_value"].to_numpy()
        )
    )

    comparison_df["significant_at_0_05"] = (
        comparison_df["holm_adjusted_p_value"] < ALPHA
    )

    output_file = os.path.join(
        OUTPUT_DIR,
        "paired_comparisons.csv"
    )

    comparison_df.to_csv(
        output_file,
        index=False
    )

    print("\nPaired comparisons saved.")
    print("\nHolm-Bonferroni corrected comparisons:")
    print(
        comparison_df[
            [
                "metric",
                "comparison",
                "p_value",
                "holm_adjusted_p_value",
                "significant_at_0_05"
            ]
        ].to_string(index=False)
    )

    return comparison_df


# ==================================================
# METRIC COMPARISON GRAPHS
# ==================================================

def plot_metric_comparison(data, metric):

    grouped = (
        data.groupby("algorithm")[metric]
        .agg(["mean", "std"])
        .reindex(ALGORITHMS)
    )

    grouped = grouped.dropna(
        subset=["mean"]
    )

    if grouped.empty:
        return

    plt.figure(figsize=(8, 5))

    plt.bar(
        grouped.index,
        grouped["mean"],
        yerr=grouped["std"].fillna(0),
        capsize=5
    )

    plt.title(
        f"Algorithm Comparison - {metric.capitalize()}"
    )

    plt.xlabel("Algorithm")
    plt.ylabel(
        f"Average {metric.capitalize()}"
    )

    plt.grid(axis="y", alpha=0.3)

    plt.tight_layout()

    filename = os.path.join(
        OUTPUT_DIR,
        f"{metric}_comparison.png"
    )

    plt.savefig(filename, dpi=300)
    plt.close()

    print("Saved:", filename)


# ==================================================
# SUCCESS RATE GRAPH
# ==================================================

def plot_success_rate(success):

    if success.empty:
        return

    plt.figure(figsize=(8, 5))

    plt.bar(
        success["algorithm"],
        success["success_rate_percent"]
    )

    plt.title("Algorithm Success Rate")
    plt.xlabel("Algorithm")
    plt.ylabel("Success Rate (%)")

    plt.ylim(0, 105)
    plt.grid(axis="y", alpha=0.3)

    plt.tight_layout()

    filename = os.path.join(
        OUTPUT_DIR,
        "success_rate.png"
    )

    plt.savefig(filename, dpi=300)
    plt.close()

    print("Saved:", filename)


# ==================================================
# CONFIDENCE INTERVAL GRAPHS
# ==================================================

def plot_confidence_intervals(summary):

    for metric in METRICS:

        metric_data = summary[
            summary["metric"] == metric
        ].copy()

        if metric_data.empty:
            continue

        metric_data = (
            metric_data.set_index("algorithm")
            .reindex(ALGORITHMS)
            .dropna(subset=["mean"])
        )

        if metric_data.empty:
            continue

        lower_error = (
            metric_data["mean"]
            - metric_data["ci95_low"]
        )

        upper_error = (
            metric_data["ci95_high"]
            - metric_data["mean"]
        )

        plt.figure(figsize=(8, 5))

        plt.errorbar(
            metric_data.index,
            metric_data["mean"],
            yerr=[
                lower_error,
                upper_error
            ],
            fmt="o",
            capsize=6
        )

        plt.title(
            f"95% Confidence Interval - {metric.capitalize()}"
        )

        plt.xlabel("Algorithm")
        plt.ylabel(
            f"Average {metric.capitalize()}"
        )

        plt.grid(axis="y", alpha=0.3)

        plt.tight_layout()

        filename = os.path.join(
            OUTPUT_DIR,
            f"{metric}_confidence_interval.png"
        )

        plt.savefig(filename, dpi=300)
        plt.close()

        print("Saved:", filename)


# ==================================================
# FINAL SUMMARY
# ==================================================

def print_summary(summary, success, comparisons):

    print("\n")
    print("=" * 70)
    print("       ROBOT PATH PLANNING - STATISTICAL ANALYSIS")
    print("=" * 70)

    print("\nAVERAGE PERFORMANCE")

    for metric in METRICS:

        print(f"\n{metric.upper()}")

        metric_data = summary[
            summary["metric"] == metric
        ]

        if metric_data.empty:
            print("No data available.")
            continue

        print(
            metric_data[
                [
                    "algorithm",
                    "mean",
                    "std_dev",
                    "ci95_low",
                    "ci95_high"
                ]
            ].to_string(index=False)
        )

    print("\nSUCCESS RATE")
    print(success.to_string(index=False))

    print("\nSTATISTICAL SIGNIFICANCE")
    print(
        "Holm-Bonferroni correction applied."
    )

    print(
        comparisons[
            [
                "metric",
                "comparison",
                "p_value",
                "holm_adjusted_p_value",
                "significant_at_0_05"
            ]
        ].to_string(index=False)
    )

    print("\n")
    print("=" * 70)
    print("Analysis completed.")
    print("Output folder:", OUTPUT_DIR)
    print("=" * 70)


# ==================================================
# MAIN FUNCTION
# ==================================================

def main():

    print("\nStarting Statistical Analysis...")

    data = load_data()

    summary = descriptive_statistics(data)

    success = calculate_success_rate(data)

    comparisons = paired_comparisons(data)

    for metric in METRICS:
        plot_metric_comparison(data, metric)

    plot_success_rate(success)

    plot_confidence_intervals(summary)

    print_summary(
        summary,
        success,
        comparisons
    )

    print("\nAll files saved in:")
    print(os.path.abspath(OUTPUT_DIR))


# ==================================================
# PROGRAM ENTRY POINT
# ==================================================

if __name__ == "__main__":
    main()
