import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
RESULTS_PATH = BASE_DIR / "resource_results.json"
SUMMARY_PATH = BASE_DIR / "resource_summary.json"
OUTPUT_JSON_PATH = BASE_DIR / "resource_result_metrics.json"
PLOTS_DIR = BASE_DIR / "plots"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def ensure_dirs():
    PLOTS_DIR.mkdir(exist_ok=True)


def save_bar_chart(labels, values, title, ylabel, output_path, color):
    plt.figure(figsize=(10, 5))
    bars = plt.bar(labels, values, color=color)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.tight_layout()

    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value:.2f}" if isinstance(value, float) else f"{value}",
            ha="center",
            va="bottom",
            fontsize=9,
        )

    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()


def save_scatter(x_values, y_values, labels, title, xlabel, ylabel, output_path, color):
    plt.figure(figsize=(8, 5))
    plt.scatter(x_values, y_values, s=130, c=color, alpha=0.75, edgecolors="black")

    for x_val, y_val, label in zip(x_values, y_values, labels):
        plt.annotate(label, (x_val, y_val), textcoords="offset points", xytext=(6, 6), fontsize=8)

    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()


def aggregate_by_category(results):
    successful = [item for item in results if item.get("status") == "success"]
    df = pd.DataFrame(successful)
    grouped = (
        df.groupby("category")
        .agg(
            {
                "runtime_seconds": "mean",
                "cpu_time_seconds": "mean",
                "memory_peak_mb": "mean",
                "loc": "mean",
                "function_count": "mean",
                "stage3_issue_count": "mean",
            }
        )
        .reset_index()
    )
    grouped["issue_density"] = grouped["stage3_issue_count"] / grouped["loc"]
    grouped["runtime_per_loc"] = grouped["runtime_seconds"] / grouped["loc"]
    return grouped


def build_result_metrics(results, summary):
    successful = [item for item in results if item.get("status") == "success"]
    category_df = aggregate_by_category(results)

    metrics = {
        "dataset_size": len(results),
        "success_count": len(successful),
        "success_rate": round((len(successful) / len(results)) * 100, 2) if results else 0,
        "overall": {
            "avg_runtime_seconds": summary.get("avg_runtime_seconds", 0),
            "avg_cpu_time_seconds": summary.get("avg_cpu_time_seconds", 0),
            "avg_memory_peak_mb": summary.get("avg_memory_peak_mb", 0),
            "avg_loc": summary.get("avg_loc", 0),
            "avg_function_count": summary.get("avg_function_count", 0),
        },
        "category_comparison": category_df.round(4).to_dict(orient="records"),
    }

    return metrics


def generate_plots(results, summary, metrics):
    category_df = pd.DataFrame(metrics["category_comparison"])
    categories = category_df["category"].tolist()

    save_bar_chart(
        categories,
        category_df["runtime_seconds"].tolist(),
        "Category vs Average Runtime",
        "Seconds",
        PLOTS_DIR / "category_avg_runtime.png",
        "#F18F01",
    )

    save_bar_chart(
        categories,
        category_df["stage3_issue_count"].tolist(),
        "Category vs Average Issues",
        "Issues",
        PLOTS_DIR / "category_avg_issues.png",
        "#C73E1D",
    )

    save_bar_chart(
        categories,
        category_df["issue_density"].tolist(),
        "Issue Density by Category",
        "Issues / LOC",
        PLOTS_DIR / "category_issue_density.png",
        "#6A994E",
    )

    save_bar_chart(
        categories,
        category_df["loc"].tolist(),
        "Average LOC by Category",
        "Lines of Code",
        PLOTS_DIR / "category_avg_loc.png",
        "#7B2CBF",
    )

    save_bar_chart(
        categories,
        category_df["runtime_per_loc"].tolist(),
        "Runtime Efficiency by Category",
        "Runtime / LOC",
        PLOTS_DIR / "category_runtime_efficiency.png",
        "#0081A7",
    )

    save_bar_chart(
        categories,
        category_df["memory_peak_mb"].tolist(),
        "Average Peak Memory by Category",
        "Peak Memory (MB)",
        PLOTS_DIR / "category_avg_memory.png",
        "#F4A261",
    )


def main():
    ensure_dirs()
    results = load_json(RESULTS_PATH)
    summary = load_json(SUMMARY_PATH)
    metrics = build_result_metrics(results, summary)
    OUTPUT_JSON_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    generate_plots(results, summary, metrics)
    print(f"Saved metrics to {OUTPUT_JSON_PATH}")
    print(f"Saved plots to {PLOTS_DIR}")


if __name__ == "__main__":
    main()
