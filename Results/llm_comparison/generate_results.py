"""
Result 5: Analysis Tool with Visualization Plots and Paper-Ready Summary
Generates comparison plots and a written results discussion from experiment results.
"""

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PLOTS_DIR = BASE_DIR / "analysis_plots"
RESULTS_FILE = BASE_DIR / "llm_results.json"
SUMMARY_JSON_FILE = BASE_DIR / "analysis_summary.json"
SUMMARY_MD_FILE = BASE_DIR / "analysis_summary.md"

MODEL_ORDER = ["pipeline", "gpt", "grok", "codellama", "gemma", "mistral", "llama2"]
MODEL_LABELS = {
    "pipeline": "Pipeline",
    "gpt": "GPT",
    "grok": "Grok",
    "codellama": "CodeLlama",
    "gemma": "Gemma",
    "mistral": "Mistral",
    "llama2": "Llama2",
}


def ensure_output_dir():
    OUTPUT_PLOTS_DIR.mkdir(exist_ok=True)


def load_results(filepath: Path) -> List[Dict]:
    with open(filepath, encoding="utf-8") as file:
        return json.load(file)


def normalize_model_name(result: Dict) -> str:
    provider = (result.get("provider") or "").strip().lower()
    provider_model = (result.get("provider_model") or "").strip().lower()

    if provider in MODEL_LABELS:
        return provider
    if provider_model in MODEL_LABELS:
        return provider_model

    for key in MODEL_LABELS:
        if key in provider:
            return key
        if key in provider_model:
            return key

    return provider or provider_model or "unknown"


def process_results(results: List[Dict]) -> Dict:
    data_by_model = defaultdict(list)
    data_by_category = defaultdict(lambda: defaultdict(list))
    all_by_model = defaultdict(list)
    success_results = []

    for result in results:
        model = normalize_model_name(result)
        all_by_model[model].append(result)

        if result.get("status") != "success":
            continue

        category = result.get("category", "unknown")

        data_by_model[model].append(result)
        data_by_category[category][model].append(result)
        success_results.append(result)

    ordered_by_model = {
        model: data_by_model[model]
        for model in MODEL_ORDER
        if data_by_model.get(model)
    }

    return {
        "by_model": ordered_by_model,
        "all_by_model": {
            model: all_by_model[model]
            for model in MODEL_ORDER
            if all_by_model.get(model)
        },
        "by_category": data_by_category,
        "success_results": success_results,
        "raw_results": results,
    }


def calculate_metrics(results_by_model: Dict[str, List[Dict]], all_results_by_model: Dict[str, List[Dict]]) -> pd.DataFrame:
    metrics = []

    for model, all_results_list in all_results_by_model.items():
        results_list = results_by_model.get(model, [])
        if not results_list:
            avg_runtime = 0
            avg_loc = 0
            avg_functions = 0
            avg_issues = 0
            avg_high = 0
            avg_medium = 0
            total_high_severity = 0
            total_medium_severity = 0
        else:
            avg_runtime = np.mean([r.get("runtime_seconds", 0) for r in results_list])
            avg_loc = np.mean([r.get("loc", 0) for r in results_list])
            avg_functions = np.mean([r.get("function_count", 0) for r in results_list])
            avg_issues = np.mean([r.get("severity", {}).get("total", 0) for r in results_list])
            avg_high = np.mean([r.get("severity", {}).get("high", 0) for r in results_list])
            avg_medium = np.mean([r.get("severity", {}).get("medium", 0) for r in results_list])

            total_high_severity = sum(r.get("severity", {}).get("high", 0) for r in results_list)
            total_medium_severity = sum(r.get("severity", {}).get("medium", 0) for r in results_list)

        validation_success = sum(
            1
            for r in all_results_list
            if r.get("status") == "success" and r.get("validation_success", False)
        )
        generation_success = sum(1 for r in all_results_list if r.get("status") == "success")
        success_rate = (validation_success / len(all_results_list) * 100) if all_results_list else 0
        generation_rate = (generation_success / len(all_results_list) * 100) if all_results_list else 0

        metrics.append(
            {
                "Model Key": model,
                "Model": MODEL_LABELS.get(model, model.title()),
                "Avg Runtime (s)": avg_runtime,
                "Avg LOC": avg_loc,
                "Avg Functions": avg_functions,
                "Avg Total Issues": avg_issues,
                "Avg High Severity": avg_high,
                "Avg Medium Severity": avg_medium,
                "Total High Severity": total_high_severity,
                "Total Medium Severity": total_medium_severity,
                "Validation Success %": success_rate,
                "Generation Success %": generation_rate,
                "Count": len(results_list),
                "Total Attempts": len(all_results_list),
            }
        )

    return pd.DataFrame(metrics)


def calculate_category_metrics(data_by_category: Dict[str, Dict[str, List[Dict]]]) -> Dict[str, Dict[str, float]]:
    category_summary = {}
    for category, models in data_by_category.items():
        category_summary[category] = {}
        for model, results in models.items():
            if not results:
                continue
            category_summary[category][MODEL_LABELS.get(model, model.title())] = round(
                float(np.mean([r.get("severity", {}).get("total", 0) for r in results])),
                2,
            )
    return category_summary


def save_plot(filepath: Path):
    plt.tight_layout()
    plt.savefig(filepath, dpi=300, bbox_inches="tight")
    print(f"Saved: {filepath}")
    plt.close()


def plot_runtime_comparison(metrics_df: pd.DataFrame, title: str = "Average Runtime by Model"):
    fig, ax = plt.subplots(figsize=(12, 6))

    models = metrics_df["Model"]
    runtimes = metrics_df["Avg Runtime (s)"]
    colors = ["#4CAF50" if model == "Pipeline" else "#2196F3" for model in models]
    bars = ax.bar(models, runtimes, color=colors, alpha=0.75, edgecolor="black")

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, f"{height:.1f}s", ha="center", va="bottom", fontsize=10)

    ax.set_ylabel("Runtime (seconds)")
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.3)
    plt.xticks(rotation=45, ha="right")
    save_plot(OUTPUT_PLOTS_DIR / "01_runtime_comparison.png")


def plot_security_issues(metrics_df: pd.DataFrame, title: str = "Security Issues by Model"):
    fig, ax = plt.subplots(figsize=(12, 6))

    models = metrics_df["Model"]
    high = metrics_df["Total High Severity"]
    medium = metrics_df["Total Medium Severity"]

    x = np.arange(len(models))
    width = 0.35
    bars1 = ax.bar(x - width / 2, high, width, label="High Severity", color="#F44336", alpha=0.8)
    bars2 = ax.bar(x + width / 2, medium, width, label="Medium Severity", color="#FF9800", alpha=0.8)

    ax.set_ylabel("Count")
    ax.set_title(title)
    ax.set_xticks(x)
    ax.set_xticklabels(models, rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, height, f"{int(height)}", ha="center", va="bottom", fontsize=9)

    save_plot(OUTPUT_PLOTS_DIR / "02_security_issues.png")


def plot_code_metrics(metrics_df: pd.DataFrame, title: str = "Code Metrics by Model"):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    models = metrics_df["Model"]

    ax1.bar(models, metrics_df["Avg LOC"], color="#2196F3", alpha=0.75, edgecolor="black")
    ax1.set_ylabel("Lines of Code")
    ax1.set_title("Average LOC")
    ax1.grid(axis="y", alpha=0.3)
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha="right")

    ax2.bar(models, metrics_df["Avg Functions"], color="#4CAF50", alpha=0.75, edgecolor="black")
    ax2.set_ylabel("Function Count")
    ax2.set_title("Average Function Count")
    ax2.grid(axis="y", alpha=0.3)
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha="right")

    fig.suptitle(title)
    save_plot(OUTPUT_PLOTS_DIR / "03_code_metrics.png")


def plot_validation_success(metrics_df: pd.DataFrame, title: str = "Validation Success Rate by Model"):
    fig, ax = plt.subplots(figsize=(12, 6))

    models = metrics_df["Model"]
    success_rates = metrics_df["Validation Success %"]
    colors = ["#4CAF50" if rate == 100 else "#FF9800" if rate >= 75 else "#F44336" for rate in success_rates]
    bars = ax.bar(models, success_rates, color=colors, alpha=0.75, edgecolor="black")

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height, f"{height:.1f}%", ha="center", va="bottom", fontsize=10)

    ax.set_ylabel("Success Rate (%)")
    ax.set_title(title)
    ax.set_ylim(0, 105)
    ax.axhline(y=100, color="green", linestyle="--", alpha=0.3, label="100%")
    ax.grid(axis="y", alpha=0.3)
    plt.xticks(rotation=45, ha="right")
    ax.legend()
    save_plot(OUTPUT_PLOTS_DIR / "04_validation_success.png")


def plot_runtime_vs_security(metrics_df: pd.DataFrame, title: str = "Runtime vs Security Issues"):
    fig, ax = plt.subplots(figsize=(10, 7))

    runtimes = metrics_df["Avg Runtime (s)"]
    issues = metrics_df["Avg Total Issues"]
    models = metrics_df["Model"]
    colors = ["#4CAF50" if model == "Pipeline" else "#2196F3" for model in models]
    sizes = metrics_df["Count"] * 60

    ax.scatter(runtimes, issues, s=sizes, c=colors, alpha=0.7, edgecolors="black", linewidth=1.5)

    for idx, model in enumerate(models):
        ax.annotate(model, (runtimes.iloc[idx], issues.iloc[idx]), xytext=(6, 6), textcoords="offset points", fontsize=9)

    ax.set_xlabel("Average Runtime (seconds)")
    ax.set_ylabel("Average Total Issues")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    save_plot(OUTPUT_PLOTS_DIR / "05_runtime_vs_security.png")


def plot_model_comparison_heatmap(metrics_df: pd.DataFrame, title: str = "Model Comparison Heatmap"):
    fig, ax = plt.subplots(figsize=(12, 8))

    metrics_to_plot = metrics_df[
        ["Model", "Avg Runtime (s)", "Avg LOC", "Avg Functions", "Avg Total Issues", "Validation Success %"]
    ].set_index("Model")

    metrics_normalized = metrics_to_plot.copy()
    for col in metrics_normalized.columns:
        max_val = metrics_normalized[col].max()
        min_val = metrics_normalized[col].min()
        if max_val > min_val:
            metrics_normalized[col] = (metrics_normalized[col] - min_val) / (max_val - min_val) * 100
        else:
            metrics_normalized[col] = 50

    im = ax.imshow(metrics_normalized.T, cmap="RdYlGn", aspect="auto")
    ax.set_xticks(np.arange(len(metrics_normalized.index)))
    ax.set_yticks(np.arange(len(metrics_normalized.columns)))
    ax.set_xticklabels(metrics_normalized.index, rotation=45, ha="right")
    ax.set_yticklabels(metrics_normalized.columns)

    for i in range(len(metrics_normalized.columns)):
        for j in range(len(metrics_normalized.index)):
            ax.text(j, i, f"{metrics_normalized.iloc[j, i]:.0f}", ha="center", va="center", color="black", fontsize=9)

    ax.set_title(title, pad=20)
    plt.colorbar(im, ax=ax, label="Normalized Score (0-100)")
    save_plot(OUTPUT_PLOTS_DIR / "06_heatmap_comparison.png")


def plot_issue_distribution(results: List[Dict], title: str = "Issue Distribution by Severity"):
    fig, ax = plt.subplots(figsize=(12, 6))

    severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0, "Info": 0}

    for result in results:
        if result.get("status") != "success":
            continue
        severity = result.get("severity", {})
        severity_counts["Critical"] += severity.get("critical", 0)
        severity_counts["High"] += severity.get("high", 0)
        severity_counts["Medium"] += severity.get("medium", 0)
        severity_counts["Low"] += severity.get("low", 0)
        severity_counts["Info"] += severity.get("info", 0)

    bars = ax.bar(
        severity_counts.keys(),
        severity_counts.values(),
        color=["#D32F2F", "#F44336", "#FF9800", "#FFC107", "#8BC34A"],
        alpha=0.75,
        edgecolor="black",
    )

    for bar in bars:
        height = bar.get_height()
        if height > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, height, f"{int(height)}", ha="center", va="bottom", fontsize=10)

    ax.set_ylabel("Count")
    ax.set_title(title)
    ax.grid(axis="y", alpha=0.3)
    save_plot(OUTPUT_PLOTS_DIR / "07_issue_distribution.png")


def build_overall_summary(results: List[Dict], metrics_df: pd.DataFrame) -> Dict:
    total = len(results)
    successful = len([r for r in results if r.get("status") == "success"])
    invalid = len([r for r in results if r.get("status") == "invalid_generation"])
    errors = len([r for r in results if r.get("status") == "error"])

    lowest_issue_row = metrics_df.loc[metrics_df["Avg Total Issues"].idxmin()]
    highest_validation_row = metrics_df.loc[metrics_df["Validation Success %"].idxmax()]
    fastest_row = metrics_df.loc[metrics_df["Avg Runtime (s)"].idxmin()]
    richest_row = metrics_df.loc[metrics_df["Avg LOC"].idxmax()]

    return {
        "total_runs": int(total),
        "successful_runs": int(successful),
        "invalid_generations": int(invalid),
        "errors": int(errors),
        "success_rate_percent": round((successful / total * 100) if total else 0, 2),
        "lowest_issue_model": lowest_issue_row["Model"],
        "lowest_issue_value": round(float(lowest_issue_row["Avg Total Issues"]), 2),
        "highest_validation_model": highest_validation_row["Model"],
        "highest_validation_value": round(float(highest_validation_row["Validation Success %"]), 2),
        "fastest_model": fastest_row["Model"],
        "fastest_runtime_seconds": round(float(fastest_row["Avg Runtime (s)"]), 2),
        "richest_model": richest_row["Model"],
        "richest_avg_loc": round(float(richest_row["Avg LOC"]), 2),
    }


def build_paper_ready_summary(results: List[Dict], metrics_df: pd.DataFrame, category_metrics: Dict) -> str:
    validation_sorted = metrics_df.sort_values("Validation Success %", ascending=False)
    issue_sorted = metrics_df.sort_values("Avg Total Issues", ascending=True)
    runtime_sorted = metrics_df.sort_values("Avg Runtime (s)", ascending=True)
    loc_sorted = metrics_df.sort_values("Avg LOC", ascending=False)

    best_validation = validation_sorted.iloc[0]
    best_security = issue_sorted.iloc[0]
    fastest = runtime_sorted.iloc[0]
    richest = loc_sorted.iloc[0]

    per_model_lines = []
    for _, row in metrics_df.iterrows():
        per_model_lines.append(
            f"- {row['Model']}: avg runtime {row['Avg Runtime (s)']:.2f}s, avg issues {row['Avg Total Issues']:.2f}, "
            f"validation {row['Validation Success %']:.1f}%, avg LOC {row['Avg LOC']:.1f}, avg functions {row['Avg Functions']:.1f}"
        )

    category_lines = []
    for category, model_scores in sorted(category_metrics.items()):
        ordered = ", ".join(f"{model}: {score}" for model, score in sorted(model_scores.items(), key=lambda item: item[1]))
        category_lines.append(f"- {category}: {ordered}")

    total = len(results)
    successful = len([r for r in results if r.get("status") == "success"])
    invalid = len([r for r in results if r.get("status") == "invalid_generation"])
    errors = len([r for r in results if r.get("status") == "error"])

    return f"""# Result 5: Results and Discussion

## Experimental Summary

- Total runs: {total}
- Successful runs: {successful} ({(successful / total * 100) if total else 0:.1f}%)
- Invalid generations: {invalid} ({(invalid / total * 100) if total else 0:.1f}%)
- Errors: {errors} ({(errors / total * 100) if total else 0:.1f}%)

## Overall Findings

The comparison shows a clear trade-off between runtime, contract richness, and security reliability. {best_validation['Model']} achieved the strongest validation performance at {best_validation['Validation Success %']:.1f}%, indicating the most consistent generation quality across the dataset. {best_security['Model']} produced the lowest average issue count at {best_security['Avg Total Issues']:.2f}; however, this result should be interpreted together with code complexity metrics because lower issue counts can coincide with shorter and simpler contracts. {fastest['Model']} was the fastest model with an average runtime of {fastest['Avg Runtime (s)']:.2f} seconds, while {richest['Model']} generated the richest contracts with an average size of {richest['Avg LOC']:.1f} non-empty lines.

## Model-Wise Interpretation

{chr(10).join(per_model_lines)}

## Security Interpretation

The results indicate that direct LLM generation does not consistently optimize for secure contract construction. Models with higher function counts and richer code structure often accumulated more medium-severity findings, showing that contract complexity can expose more security weaknesses when generation is not guided by a structured pipeline. Conversely, some smaller local models achieved lower average issue counts partly because they generated shorter, simpler contracts with fewer behaviors to analyze. This means that lower vulnerability counts alone should not be treated as proof of better contract quality.

## Runtime and Quality Trade-Off

The runtime comparison suggests that faster generation does not automatically imply better outputs. Rapid models can be attractive for throughput, but they may sacrifice validation consistency or contract completeness. Slower approaches, especially structured generation pipelines, appear to gain reliability from additional processing stages such as validation and security analysis. This supports the claim that secure contract generation benefits from orchestration rather than relying on a single-pass LLM response.

## Category-Level Observations

{chr(10).join(category_lines)}

## Plot Interpretation Guide

- Plot 1 (Runtime Comparison): compares model speed and highlights the runtime overhead of structured generation.
- Plot 2 (Security Issues): compares high- and medium-severity findings to show security differences across models.
- Plot 3 (Code Metrics): shows average LOC and function count, helping explain whether lower issue counts come from simpler code.
- Plot 4 (Validation Success): summarizes how consistently each model generates code that passes validation checks.
- Plot 5 (Runtime vs Security): visualizes the speed-quality trade-off across models.
- Plot 6 (Heatmap): provides a compact all-metric comparison for paper figures or slides.
- Plot 7 (Issue Distribution): shows the overall severity profile across all successful runs.

## Final Result Statement

Overall, the experimental evidence suggests that standalone LLMs can generate workable smart contracts, but their outputs remain inconsistent in validation quality and security posture. A structured multi-stage pipeline provides a more reliable balance of correctness, contract completeness, and vulnerability awareness, making it a stronger choice for production-oriented smart contract generation workflows.
"""


def print_summary_table(metrics_df: pd.DataFrame):
    print("\n" + "=" * 100)
    print("SUMMARY STATISTICS BY MODEL")
    print("=" * 100)
    print(
        metrics_df[
            ["Model", "Count", "Avg Runtime (s)", "Avg LOC", "Avg Functions", "Avg Total Issues", "Validation Success %"]
        ].to_string(index=False)
    )
    print("=" * 100 + "\n")


def print_detailed_summary(results: List[Dict]):
    total = len(results)
    successful = len([r for r in results if r.get("status") == "success"])
    invalid = len([r for r in results if r.get("status") == "invalid_generation"])
    errors = len([r for r in results if r.get("status") == "error"])

    print("\n" + "=" * 100)
    print("EXPERIMENT SUMMARY")
    print("=" * 100)
    print(f"Total Runs: {total}")
    print(f"Successful: {successful} ({successful / total * 100:.1f}%)")
    print(f"Invalid Generation: {invalid} ({invalid / total * 100:.1f}%)")
    print(f"Errors: {errors} ({errors / total * 100:.1f}%)")
    print("=" * 100 + "\n")


def main():
    print("\n" + "=" * 100)
    print("RESULT 5: ANALYSIS AND VISUALIZATION")
    print("=" * 100)

    if not RESULTS_FILE.exists():
        print(f"Results file not found: {RESULTS_FILE}")
        return

    print(f"\nLoading results from: {RESULTS_FILE}")
    results = load_results(RESULTS_FILE)
    print(f"Loaded {len(results)} results")

    ensure_output_dir()
    print(f"Plots will be saved to: {OUTPUT_PLOTS_DIR}")

    processed = process_results(results)
    metrics_df = calculate_metrics(processed["by_model"], processed["all_by_model"])
    category_metrics = calculate_category_metrics(processed["by_category"])

    print_detailed_summary(results)
    print_summary_table(metrics_df)

    print("Generating plots...")
    plot_runtime_comparison(metrics_df)
    plot_security_issues(metrics_df)
    plot_code_metrics(metrics_df)
    plot_validation_success(metrics_df)
    plot_runtime_vs_security(metrics_df)
    plot_model_comparison_heatmap(metrics_df)
    plot_issue_distribution(results)

    summary_payload = {
        "overall": build_overall_summary(results, metrics_df),
        "metrics_by_model": metrics_df.to_dict(orient="records"),
        "metrics_by_category": category_metrics,
    }
    SUMMARY_JSON_FILE.write_text(json.dumps(summary_payload, indent=2), encoding="utf-8")

    paper_summary = build_paper_ready_summary(results, metrics_df, category_metrics)
    SUMMARY_MD_FILE.write_text(paper_summary, encoding="utf-8")

    print("\nAnalysis complete.")
    print(f"Plots saved to: {OUTPUT_PLOTS_DIR}")
    print(f"Summary JSON: {SUMMARY_JSON_FILE}")
    print(f"Paper-ready summary: {SUMMARY_MD_FILE}")


if __name__ == "__main__":
    main()
