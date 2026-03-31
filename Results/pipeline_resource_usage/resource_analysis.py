import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR = Path(__file__).parent.resolve()
RESOURCE_RESULTS_FILE = SCRIPT_DIR / "resource_results.json"
RESOURCE_SUMMARY_FILE = SCRIPT_DIR / "resource_summary.json"
OUTPUT_DIR = SCRIPT_DIR / "resource_analysis"
REPORT_FILE = OUTPUT_DIR / "RESOURCE_ANALYSIS_REPORT.md"


def ensure_output_dir():
    """Create output directory"""
    OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================================
# DATA LOADING
# ============================================================================

def load_resource_results() -> List[Dict]:
    """Load detailed resource results"""
    with open(RESOURCE_RESULTS_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_resource_summary() -> Dict:
    """Load resource summary"""
    with open(RESOURCE_SUMMARY_FILE, encoding="utf-8") as f:
        return json.load(f)



def create_detailed_breakdown(results: List[Dict]) -> str:
    """Generate detailed contract breakdown"""
    text = "\n---\n\n## Detailed Contract Breakdown\n\n"
    text += "| Contract | Category | Runtime (s) | CPU (s) | Memory (MB) | LOC | Functions | Issues |\n"
    text += "|----------|----------|-------------|---------|-------------|-----|-----------|--------|\n"

    for r in results:
        text += "| {} | {} | {:.2f} | {:.4f} | {:.4f} | {} | {} | {} |\n".format(
            r["contract_name"],
            r["category"],
            r["runtime_seconds"],
            r["cpu_time_seconds"],
            r["memory_peak_mb"],
            r["loc"],
            r["function_count"],
            r["stage3_issue_count"],
        )

    return text



# ============================================================================
# PLOTTING FUNCTIONS
# ============================================================================

def plot_runtime_by_category(results: List[Dict], summary: Dict):
    """Plot runtime breakdown by category"""
    fig, ax = plt.subplots(figsize=(12, 6))

    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(r["runtime_seconds"])

    cat_names = list(categories.keys())
    avg_times = [np.mean(times) for times in categories.values()]

    colors = plt.cm.Set3(np.linspace(0, 1, len(cat_names)))
    bars = ax.bar(cat_names, avg_times, color=colors, alpha=0.7, edgecolor="black", linewidth=2)

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{height:.2f}s",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    ax.set_ylabel("Average Runtime (seconds)", fontsize=12, fontweight="bold")
    ax.set_title("Average Runtime by Contract Category", fontsize=14, fontweight="bold")
    ax.grid(axis="y", alpha=0.3)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    filepath = OUTPUT_DIR / "01_runtime_by_category.png"
    plt.savefig(filepath, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {filepath}")
    plt.close()


def plot_memory_usage(results: List[Dict]):
    """Plot memory usage across contracts"""
    fig, ax = plt.subplots(figsize=(14, 6))

    contracts = [r["contract_name"] for r in results]
    current_mem = [r["memory_current_mb"] for r in results]
    peak_mem = [r["memory_peak_mb"] for r in results]

    x = np.arange(len(contracts))
    width = 0.35

    bars1 = ax.bar(x - width / 2, current_mem, width, label="Current Memory", color="#2196F3", alpha=0.7)
    bars2 = ax.bar(x + width / 2, peak_mem, width, label="Peak Memory", color="#FF9800", alpha=0.7)

    ax.set_ylabel("Memory (MB)", fontsize=12, fontweight="bold")
    ax.set_title("Memory Usage: Current vs Peak", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(contracts, rotation=45, ha="right")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()
    filepath = OUTPUT_DIR / "02_memory_usage.png"
    plt.savefig(filepath, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {filepath}")
    plt.close()


def plot_cpu_efficiency(results: List[Dict]):
    """Plot CPU efficiency"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    contracts = [r["contract_name"] for r in results]
    runtimes = [r["runtime_seconds"] for r in results]
    cpu_times = [r["cpu_time_seconds"] for r in results]

    # CPU percentage
    cpu_percentages = [(cpu / runtime * 100) if runtime > 0 else 0 
                       for cpu, runtime in zip(cpu_times, runtimes)]

    colors = ["#4CAF50" if pct < 2 else "#FF9800" if pct < 5 else "#F44336" 
              for pct in cpu_percentages]

    ax1.bar(contracts, cpu_percentages, color=colors, alpha=0.7, edgecolor="black")
    ax1.set_ylabel("CPU Time % of Total Runtime", fontsize=11, fontweight="bold")
    ax1.set_title("CPU Efficiency", fontsize=12, fontweight="bold")
    ax1.set_ylim(0, max(cpu_percentages) * 1.2)
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha="right")
    ax1.grid(axis="y", alpha=0.3)

    # CPU vs Runtime scatter
    ax2.scatter(runtimes, cpu_times, s=200, alpha=0.6, edgecolors="black", linewidth=2, color="#2196F3")
    ax2.set_xlabel("Runtime (seconds)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("CPU Time (seconds)", fontsize=11, fontweight="bold")
    ax2.set_title("CPU Time vs Runtime", fontsize=12, fontweight="bold")
    ax2.grid(True, alpha=0.3)

    # Add labels to scatter points
    for i, contract in enumerate(contracts):
        ax2.annotate(
            contract.split()[0],
            (runtimes[i], cpu_times[i]),
            xytext=(5, 5),
            textcoords="offset points",
            fontsize=8,
        )

    plt.tight_layout()
    filepath = OUTPUT_DIR / "03_cpu_efficiency.png"
    plt.savefig(filepath, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {filepath}")
    plt.close()


def plot_complexity_vs_resources(results: List[Dict]):
    """Plot code complexity vs resource usage"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))

    locs = [r["loc"] for r in results]
    functions = [r["function_count"] for r in results]
    runtimes = [r["runtime_seconds"] for r in results]
    peak_mems = [r["memory_peak_mb"] for r in results]

    # LOC vs Runtime
    ax1.scatter(locs, runtimes, s=150, alpha=0.6, edgecolors="black", linewidth=2, color="#2196F3")
    ax1.set_xlabel("Lines of Code", fontsize=10, fontweight="bold")
    ax1.set_ylabel("Runtime (seconds)", fontsize=10, fontweight="bold")
    ax1.set_title("Code Complexity vs Runtime", fontsize=11, fontweight="bold")
    ax1.grid(True, alpha=0.3)

    # Functions vs Runtime
    ax2.scatter(functions, runtimes, s=150, alpha=0.6, edgecolors="black", linewidth=2, color="#FF9800")
    ax2.set_xlabel("Function Count", fontsize=10, fontweight="bold")
    ax2.set_ylabel("Runtime (seconds)", fontsize=10, fontweight="bold")
    ax2.set_title("Function Count vs Runtime", fontsize=11, fontweight="bold")
    ax2.grid(True, alpha=0.3)

    # LOC vs Memory
    ax3.scatter(locs, peak_mems, s=150, alpha=0.6, edgecolors="black", linewidth=2, color="#4CAF50")
    ax3.set_xlabel("Lines of Code", fontsize=10, fontweight="bold")
    ax3.set_ylabel("Peak Memory (MB)", fontsize=10, fontweight="bold")
    ax3.set_title("Code Complexity vs Memory", fontsize=11, fontweight="bold")
    ax3.grid(True, alpha=0.3)

    # Functions vs Memory
    ax4.scatter(functions, peak_mems, s=150, alpha=0.6, edgecolors="black", linewidth=2, color="#9C27B0")
    ax4.set_xlabel("Function Count", fontsize=10, fontweight="bold")
    ax4.set_ylabel("Peak Memory (MB)", fontsize=10, fontweight="bold")
    ax4.set_title("Function Count vs Memory", fontsize=11, fontweight="bold")
    ax4.grid(True, alpha=0.3)

    plt.tight_layout()
    filepath = OUTPUT_DIR / "04_complexity_vs_resources.png"
    plt.savefig(filepath, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {filepath}")
    plt.close()


def plot_scalability_analysis(results: List[Dict], summary: Dict):
    """Plot scalability projections"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    contract_counts = np.array([10, 50, 100, 500, 1000])
    avg_runtime = summary["avg_runtime_seconds"]
    avg_cpu = summary["avg_cpu_time_seconds"]

    total_times_hours = (contract_counts * avg_runtime) / 3600
    total_cpu_hours = (contract_counts * avg_cpu) / 3600

    # Total time needed
    ax1.plot(contract_counts, total_times_hours, marker="o", linewidth=3, markersize=10, color="#2196F3")
    ax1.fill_between(contract_counts, total_times_hours, alpha=0.3, color="#2196F3")
    ax1.set_xlabel("Number of Contracts", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Total Runtime (hours)", fontsize=11, fontweight="bold")
    ax1.set_title("Scalability: Total Runtime Needed", fontsize=12, fontweight="bold")
    ax1.set_xscale("log")
    ax1.grid(True, alpha=0.3)

    # Add annotations
    for i, count in enumerate(contract_counts):
        ax1.annotate(
            f"{total_times_hours[i]:.1f}h",
            (count, total_times_hours[i]),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            fontsize=9,
            fontweight="bold",
        )

    # CPU time
    ax2.plot(contract_counts, total_cpu_hours, marker="s", linewidth=3, markersize=10, color="#FF9800")
    ax2.fill_between(contract_counts, total_cpu_hours, alpha=0.3, color="#FF9800")
    ax2.set_xlabel("Number of Contracts", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Total CPU Time (hours)", fontsize=11, fontweight="bold")
    ax2.set_title("Scalability: CPU Time Needed", fontsize=12, fontweight="bold")
    ax2.set_xscale("log")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    filepath = OUTPUT_DIR / "05_scalability_analysis.png"
    plt.savefig(filepath, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {filepath}")
    plt.close()


def plot_security_issues_vs_resources(results: List[Dict]):
    """Plot security issues found vs resource usage"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    contracts = [r["contract_name"] for r in results]
    issues = [r["stage3_issue_count"] for r in results]
    runtimes = [r["runtime_seconds"] for r in results]

    # Issues by contract
    colors = ["#F44336" if issue > 15 else "#FF9800" if issue > 10 else "#4CAF50" 
              for issue in issues]
    bars = ax1.bar(contracts, issues, color=colors, alpha=0.7, edgecolor="black")
    ax1.set_ylabel("Security Issues Found", fontsize=11, fontweight="bold")
    ax1.set_title("Security Issues by Contract", fontsize=12, fontweight="bold")
    ax1.grid(axis="y", alpha=0.3)
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha="right")

    # Issues vs Runtime
    ax2.scatter(runtimes, issues, s=200, alpha=0.6, edgecolors="black", linewidth=2, color="#9C27B0")
    ax2.set_xlabel("Runtime (seconds)", fontsize=11, fontweight="bold")
    ax2.set_ylabel("Security Issues Found", fontsize=11, fontweight="bold")
    ax2.set_title("Runtime vs Issues Found", fontsize=12, fontweight="bold")
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    filepath = OUTPUT_DIR / "06_security_issues_vs_resources.png"
    plt.savefig(filepath, dpi=300, bbox_inches="tight")
    print(f"✅ Saved: {filepath}")
    plt.close()


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Main analysis function"""
    print("\n" + "="*100)
    print("RESOURCE ANALYSIS: CPU, Memory, Runtime Performance")
    print("="*100)

    # Load data
    if not RESOURCE_RESULTS_FILE.exists() or not RESOURCE_SUMMARY_FILE.exists():
        print(f"❌ Resource files not found")
        return

    print(f"\n📂 Loading resource data...")
    results = load_resource_results()
    summary = load_resource_summary()
    print(f"✅ Loaded {len(results)} contract results")

    # Create output directory
    ensure_output_dir()
    print(f"📁 Analysis will be saved to: {OUTPUT_DIR}")

    # Generate report
    print("\n📝 Generating report...")
    report += create_detailed_breakdown(results)

    # Save report
    REPORT_FILE.write_text(report, encoding="utf-8")
    print(f"✅ Saved report to: {REPORT_FILE}")

    # Generate plots
    print("\n📊 Generating visualizations...")
    plot_runtime_by_category(results, summary)
    plot_memory_usage(results)
    plot_cpu_efficiency(results)
    plot_complexity_vs_resources(results)
    plot_scalability_analysis(results, summary)
    plot_security_issues_vs_resources(results)

    print("\n" + "="*100)
    print("✅ ANALYSIS COMPLETE!")
    print("="*100)
    print(f"\n📊 Generated files:")
    print(f"   📄 {REPORT_FILE.name}")
    for plot_file in sorted(OUTPUT_DIR.glob("*.png")):
        print(f"   📈 {plot_file.name}")
    print("="*100 + "\n")


if __name__ == "__main__":
    main()