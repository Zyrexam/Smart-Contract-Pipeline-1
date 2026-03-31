import json
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parents[1]

RESULTS_PATH = BASE_DIR / "llm_results.json"
OUTPUT_PATH = BASE_DIR / "llm_comparison_summary.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_report_issues(item):
    if item["method"] == "pipeline":
        report_path = ROOT_DIR / item["output_dir"] / "stage3_report.json"
    else:
        report_path = Path(item["analysis_report_path"])

    report = load_json(report_path)
    return report.get("initial_analysis", {}).get("issues", [])


def aggregate_items(items):
    successful = [item for item in items if item.get("status") == "success"]
    count = len(successful)

    if count == 0:
        return {
            "contracts": 0,
            "avg_runtime_seconds": 0,
            "contracts_per_minute": 0,
            "avg_loc": 0,
            "avg_function_count": 0,
            "validation_pass_count": 0,
            "severity_totals": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0,
                "total": 0,
            },
            "tool_breakdown": {},
        }

    total_runtime = sum(item["runtime_seconds"] for item in successful)
    severity_totals = {
        "critical": sum(item["severity"]["critical"] for item in successful),
        "high": sum(item["severity"]["high"] for item in successful),
        "medium": sum(item["severity"]["medium"] for item in successful),
        "low": sum(item["severity"]["low"] for item in successful),
        "info": sum(item["severity"]["info"] for item in successful),
        "total": sum(item["severity"]["total"] for item in successful),
    }

    tool_breakdown = defaultdict(lambda: {"total": 0, "severity_counts": defaultdict(int)})
    for item in successful:
        for issue in load_report_issues(item):
            tool = issue.get("tool", "unknown")
            severity = issue.get("severity", "UNKNOWN").lower()
            tool_breakdown[tool]["total"] += 1
            tool_breakdown[tool]["severity_counts"][severity] += 1

    normalized_tool_breakdown = {}
    for tool, details in sorted(tool_breakdown.items()):
        normalized_tool_breakdown[tool] = {
            "total": details["total"],
            "severity_counts": dict(sorted(details["severity_counts"].items())),
        }

    return {
        "contracts": count,
        "avg_runtime_seconds": round(total_runtime / count, 2),
        "contracts_per_minute": round((count / total_runtime) * 60, 2) if total_runtime else 0,
        "avg_loc": round(sum(item["loc"] for item in successful) / count, 2),
        "avg_function_count": round(sum(item["function_count"] for item in successful) / count, 2),
        "validation_pass_count": sum(1 for item in successful if item.get("validation_success")),
        "severity_totals": severity_totals,
        "tool_breakdown": normalized_tool_breakdown,
    }


def build_per_contract(items):
    grouped = defaultdict(dict)

    for item in items:
        grouped[item["id"]][item.get("provider", item["method"])] = item

    rows = []
    for contract_id, providers in sorted(grouped.items()):
        sample = next(iter(providers.values()))
        row = {
            "id": contract_id,
            "task_name": sample["task_name"],
            "category": sample["category"],
            "results": {},
        }

        for provider_name, item in sorted(providers.items()):
            row["results"][provider_name] = {
                "status": item["status"],
                "provider_model": item.get("provider_model"),
                "runtime_seconds": round(item["runtime_seconds"], 2),
                "validation_success": item.get("validation_success"),
                "severity": item.get("severity"),
            }
        rows.append(row)

    return rows


def main():
    items = load_json(RESULTS_PATH)

    grouped = defaultdict(list)
    for item in items:
        key = item.get("provider", item["method"])
        grouped[key].append(item)

    summary = {
        "result_id": "result_05",
        "title": "Pipeline vs GPT, Gemini, Grok, and Perplexity",
        "source_file": str(RESULTS_PATH),
        "models": {model_name: aggregate_items(model_items) for model_name, model_items in sorted(grouped.items())},
        "per_contract": build_per_contract(items),
    }

    OUTPUT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
