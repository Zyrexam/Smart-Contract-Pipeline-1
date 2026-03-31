import json
from pathlib import Path

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent
SUMMARY_PATH = BASE_DIR / "result_04_summary.json"
PLOTS_DIR = BASE_DIR / "plots"


def load_summary():
    return json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))


def ensure_dirs():
    PLOTS_DIR.mkdir(exist_ok=True)


def save_bar_chart(labels, values, title, ylabel, output_path, color):
    plt.figure(figsize=(8, 5))
    bars = plt.bar(labels, values, color=color)
    plt.title(title)
    plt.ylabel(ylabel)
    plt.tight_layout()

    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height(),
            f"{value}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    plt.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close()


def generate_runtime_chart(summary):
    labels = ["Pipeline", "Manual LLM"]
    values = [
        summary["methods"]["pipeline"]["avg_runtime_seconds"],
        summary["methods"]["manual_llm"]["avg_runtime_seconds"],
    ]
    save_bar_chart(
        labels,
        values,
        "Average Runtime Comparison",
        "Seconds",
        PLOTS_DIR / "avg_runtime_comparison.png",
        ["#2E86AB", "#F18F01"],
    )


def generate_user_steps_chart(summary):
    labels = ["Pipeline", "Manual LLM"]
    values = [
        summary["methods"]["pipeline"]["user_steps"],
        summary["methods"]["manual_llm"]["user_steps"],
    ]
    save_bar_chart(
        labels,
        values,
        "User Steps Comparison",
        "Steps",
        PLOTS_DIR / "user_steps_comparison.png",
        ["#2E86AB", "#F18F01"],
    )


def generate_validation_success_chart(summary):
    labels = ["Pipeline", "Manual LLM"]
    values = [
        summary["methods"]["pipeline"]["validation_pass_count"],
        summary["methods"]["manual_llm"]["validation_pass_count"],
    ]
    save_bar_chart(
        labels,
        values,
        "Validation Success Comparison",
        "Valid Contracts",
        PLOTS_DIR / "validation_success_comparison.png",
        ["#2E86AB", "#F18F01"],
    )


def generate_high_low_security_chart(summary):
    categories = ["High", "Low"]
    pipeline_values = [
        summary["methods"]["pipeline"]["severity_totals"]["high"],
        summary["methods"]["pipeline"]["severity_totals"]["low"],
    ]
    manual_values = [
        summary["methods"]["manual_llm"]["severity_totals"]["high"],
        summary["methods"]["manual_llm"]["severity_totals"]["low"],
    ]

    x = range(len(categories))
    width = 0.35

    plt.figure(figsize=(8, 5))
    plt.bar([i - width / 2 for i in x], pipeline_values, width=width, label="Pipeline", color="#2E86AB")
    plt.bar([i + width / 2 for i in x], manual_values, width=width, label="Manual LLM", color="#F18F01")
    plt.xticks(list(x), categories)
    plt.ylabel("Findings")
    plt.title("High and Low Severity Comparison")
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "high_low_security_comparison.png", dpi=200, bbox_inches="tight")
    plt.close()


def generate_automation_runtime_tradeoff(summary):
    labels = ["Pipeline", "Manual LLM"]
    user_steps = [
        summary["methods"]["pipeline"]["user_steps"],
        summary["methods"]["manual_llm"]["user_steps"],
    ]
    runtimes = [
        summary["methods"]["pipeline"]["avg_runtime_seconds"],
        summary["methods"]["manual_llm"]["avg_runtime_seconds"],
    ]
    colors = ["#2E86AB", "#F18F01"]

    plt.figure(figsize=(8, 5))
    plt.scatter(user_steps, runtimes, s=220, c=colors)

    for label, x_val, y_val in zip(labels, user_steps, runtimes):
        plt.annotate(label, (x_val, y_val), textcoords="offset points", xytext=(8, 8))

    plt.xlabel("User Steps")
    plt.ylabel("Average Runtime (s)")
    plt.title("Automation vs Runtime Tradeoff")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "automation_vs_runtime_tradeoff.png", dpi=200, bbox_inches="tight")
    plt.close()


def generate_total_findings_chart(summary):
    labels = ["Pipeline", "Manual LLM"]
    values = [
        summary["methods"]["pipeline"]["severity_totals"]["total"],
        summary["methods"]["manual_llm"]["severity_totals"]["total"],
    ]
    save_bar_chart(
        labels,
        values,
        "Total Findings Comparison",
        "Findings",
        PLOTS_DIR / "total_findings_comparison.png",
        ["#2E86AB", "#F18F01"],
    )


def generate_severity_distribution_chart(summary):
    severities = ["high", "medium", "low", "info"]
    pipeline_values = [summary["methods"]["pipeline"]["severity_totals"][sev] for sev in severities]
    manual_values = [summary["methods"]["manual_llm"]["severity_totals"][sev] for sev in severities]

    x = range(len(severities))
    width = 0.35

    plt.figure(figsize=(9, 5))
    plt.bar([i - width / 2 for i in x], pipeline_values, width=width, label="Pipeline", color="#2E86AB")
    plt.bar([i + width / 2 for i in x], manual_values, width=width, label="Manual LLM", color="#F18F01")
    plt.xticks(list(x), [sev.capitalize() for sev in severities])
    plt.ylabel("Findings")
    plt.title("Severity Distribution")
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "severity_distribution.png", dpi=200, bbox_inches="tight")
    plt.close()


def generate_per_contract_chart(summary):
    contracts = [item["id"] for item in summary["per_contract"]]
    pipeline_values = [item["pipeline"]["severity"]["total"] for item in summary["per_contract"]]
    manual_values = [item["manual_llm"]["severity"]["total"] for item in summary["per_contract"]]

    x = range(len(contracts))
    width = 0.35

    plt.figure(figsize=(12, 5))
    plt.bar([i - width / 2 for i in x], pipeline_values, width=width, label="Pipeline", color="#2E86AB")
    plt.bar([i + width / 2 for i in x], manual_values, width=width, label="Manual LLM", color="#F18F01")
    plt.xticks(list(x), contracts, rotation=45, ha="right")
    plt.ylabel("Total Findings")
    plt.title("Per-Contract Findings Comparison")
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "per_contract_findings.png", dpi=200, bbox_inches="tight")
    plt.close()


def main():
    ensure_dirs()
    summary = load_summary()
    generate_runtime_chart(summary)
    generate_user_steps_chart(summary)
    generate_validation_success_chart(summary)
    generate_high_low_security_chart(summary)
    generate_automation_runtime_tradeoff(summary)
    generate_total_findings_chart(summary)
    generate_severity_distribution_chart(summary)
    generate_per_contract_chart(summary)
    print(f"Saved plots to {PLOTS_DIR}")


if __name__ == "__main__":
    main()
