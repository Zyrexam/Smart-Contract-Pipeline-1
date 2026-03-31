import json
from collections import Counter, defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parents[1]
PIPELINE_OUTPUTS_DIR = ROOT_DIR / "pipeline_outputs"

RESULTS_PATH = BASE_DIR / "security_results.json"
SUMMARY_PATH = BASE_DIR / "security_summary.json"
MARKDOWN_PATH = BASE_DIR / "security_summary.md"

SEVERITY_KEYS = ["critical", "high", "medium", "low", "info"]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def safe_load_json(path: Path):
    try:
        return load_json(path)
    except Exception:
        return None


def get_contract_path(run_dir: Path):
    final_contracts = sorted(run_dir.glob("final_*.sol"))
    if final_contracts:
        return final_contracts[0]

    contracts = sorted(
        path
        for path in run_dir.glob("*.sol")
        if not path.name.startswith("final_")
    )
    return contracts[0] if contracts else None


def count_loc(path: Path):
    if not path or not path.exists():
        return 0

    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return sum(1 for line in lines if line.strip())


def normalize_title(issue):
    title = (issue.get("title") or "unknown").strip().lower()
    return title or "unknown"


def build_run_record(run_dir: Path):
    report_path = run_dir / "stage3_report.json"
    if not report_path.exists():
        return None

    report = safe_load_json(report_path)
    if not report:
        return None

    metadata = safe_load_json(run_dir / "metadata.json") or {}
    initial = report.get("initial_analysis") or {}
    final = report.get("final_analysis") or {}

    analysis = final if final else initial
    issues = analysis.get("issues", [])
    category = metadata.get("category") or metadata.get("base_standard") or "Unknown"
    contract_name = (
        analysis.get("contract_name")
        or initial.get("contract_name")
        or run_dir.name
    )

    severity = {
        key: int(analysis.get(key, 0) or 0)
        for key in SEVERITY_KEYS
    }
    severity["total"] = int(analysis.get("total_issues", sum(severity.values())) or 0)

    tool_counts = Counter()
    title_counts = Counter()
    for issue in issues:
        tool_counts[issue.get("tool") or "unknown"] += 1
        title_counts[normalize_title(issue)] += 1

    contract_path = get_contract_path(run_dir)

    return {
        "run_id": run_dir.name,
        "contract_name": contract_name,
        "category": category,
        "analysis_success": bool(analysis.get("success", False)),
        "tools_used": analysis.get("tools_used", []),
        "loc": count_loc(contract_path),
        "iterations": int(report.get("iterations", 0) or 0),
        "issues_resolved": int(report.get("issues_resolved", 0) or 0),
        "initial_total_issues": int(initial.get("total_issues", 0) or 0),
        "final_total_issues": int(final.get("total_issues", initial.get("total_issues", 0)) or 0),
        "severity": severity,
        "tool_issue_counts": dict(sorted(tool_counts.items())),
        "top_issue_titles": [
            {"title": title, "count": count}
            for title, count in title_counts.most_common(5)
        ],
        "report_path": str(report_path.relative_to(ROOT_DIR)),
    }


def gather_runs():
    records = []
    for run_dir in sorted(PIPELINE_OUTPUTS_DIR.iterdir()):
        if not run_dir.is_dir():
            continue
        record = build_run_record(run_dir)
        if record:
            records.append(record)
    return records


def build_summary(records):
    analyzed = [record for record in records if record["analysis_success"]]
    total_runs = len(records)
    analyzed_runs = len(analyzed)

    severity_totals = {key: 0 for key in SEVERITY_KEYS + ["total"]}
    category_stats = defaultdict(lambda: {"contracts": 0, "issues": 0, "high": 0, "medium": 0})
    tool_totals = Counter()
    title_totals = Counter()

    contracts_with_findings = 0
    contracts_improved = 0
    total_resolved = 0

    for record in analyzed:
        total_resolved += record["issues_resolved"]
        if record["severity"]["total"] > 0:
            contracts_with_findings += 1
        if record["issues_resolved"] > 0 or record["final_total_issues"] < record["initial_total_issues"]:
            contracts_improved += 1

        for key, value in record["severity"].items():
            severity_totals[key] += value

        category = category_stats[record["category"]]
        category["contracts"] += 1
        category["issues"] += record["severity"]["total"]
        category["high"] += record["severity"]["high"]
        category["medium"] += record["severity"]["medium"]

        for tool, count in record["tool_issue_counts"].items():
            tool_totals[tool] += count
        for issue in record["top_issue_titles"]:
            title_totals[issue["title"]] += issue["count"]

    avg_initial_issues = round(sum(item["initial_total_issues"] for item in analyzed) / analyzed_runs, 2) if analyzed_runs else 0.0
    avg_total_issues = round(severity_totals["total"] / analyzed_runs, 2) if analyzed_runs else 0.0
    avg_final_issues = round(sum(item["final_total_issues"] for item in analyzed) / analyzed_runs, 2) if analyzed_runs else 0.0
    total_initial_issues = sum(item["initial_total_issues"] for item in analyzed)
    fix_rate = round((total_resolved / total_initial_issues) * 100, 2) if total_initial_issues else 0.0

    category_summary = []
    for name, stats in sorted(category_stats.items()):
        contracts = stats["contracts"]
        category_summary.append(
            {
                "category": name,
                "contracts": contracts,
                "avg_total_issues": round(stats["issues"] / contracts, 2) if contracts else 0.0,
                "avg_high": round(stats["high"] / contracts, 2) if contracts else 0.0,
                "avg_medium": round(stats["medium"] / contracts, 2) if contracts else 0.0,
            }
        )

    return {
        "total_runs_with_reports": total_runs,
        "successful_analyses": analyzed_runs,
        "contracts_with_findings": contracts_with_findings,
        "contracts_with_findings_percentage": round((contracts_with_findings / analyzed_runs) * 100, 2) if analyzed_runs else 0.0,
        "contracts_improved_after_fix": contracts_improved,
        "avg_initial_issues_per_contract": avg_initial_issues,
        "avg_total_issues_per_contract": avg_total_issues,
        "avg_final_issues_per_contract": avg_final_issues,
        "total_issues_resolved": total_resolved,
        "fix_rate_percentage": fix_rate,
        "severity_totals": severity_totals,
        "top_tools_by_issue_count": [
            {"tool": tool, "count": count}
            for tool, count in tool_totals.most_common()
        ],
        "top_issue_titles": [
            {"title": title, "count": count}
            for title, count in title_totals.most_common(10)
        ],
        "category_summary": category_summary,
    }


def write_markdown(summary):
    lines = [
        "# Security Evaluation Summary",
        "",
        "## Experimental Summary",
        "",
        f"- Total runs with reports: {summary['total_runs_with_reports']}",
        f"- Successful analyses: {summary['successful_analyses']}",
        f"- Contracts with findings: {summary['contracts_with_findings']} ({summary['contracts_with_findings_percentage']}%)",
        f"- Avg initial issues per contract: {summary['avg_initial_issues_per_contract']}",
        f"- Avg total issues per contract: {summary['avg_total_issues_per_contract']}",
        f"- Avg final issues per contract: {summary['avg_final_issues_per_contract']}",
        f"- Contracts improved after fix: {summary['contracts_improved_after_fix']}",
        f"- Total issues resolved: {summary['total_issues_resolved']}",
        f"- Fix rate: {summary['fix_rate_percentage']}%",
        "",
        "## Severity Distribution",
        "",
    ]

    severity = summary["severity_totals"]
    for key in SEVERITY_KEYS + ["total"]:
        lines.append(f"- {key.title()}: {severity[key]}")

    lines.extend(["", "## Most Common Issue Titles", ""])
    for item in summary["top_issue_titles"][:10]:
        lines.append(f"- {item['title']}: {item['count']}")

    lines.extend(["", "## Category Summary", ""])
    for item in summary["category_summary"]:
        lines.append(
            f"- {item['category']}: {item['contracts']} contracts, "
            f"avg issues {item['avg_total_issues']}, "
            f"avg high {item['avg_high']}, avg medium {item['avg_medium']}"
        )

    lines.extend(["", "## Tool Contribution", ""])
    for item in summary["top_tools_by_issue_count"]:
        lines.append(f"- {item['tool']}: {item['count']}")

    MARKDOWN_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    records = gather_runs()
    summary = build_summary(records)

    RESULTS_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_markdown(summary)

    print(f"Saved {RESULTS_PATH}")
    print(f"Saved {SUMMARY_PATH}")
    print(f"Saved {MARKDOWN_PATH}")


if __name__ == "__main__":
    main()
