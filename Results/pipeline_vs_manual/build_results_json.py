import json
from collections import Counter, defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parents[1]

PIPELINE_RESULTS_PATH = BASE_DIR / "pipeline_results.json"
MANUAL_RESULTS_PATH = BASE_DIR / "manual_llm_results.json"
OUTPUT_PATH = BASE_DIR / "result_04_summary.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def aggregate_method(items):
    successful = [item for item in items if item.get("status") == "success"]
    count = len(successful)

    if count == 0:
        return {
            "contracts": 0,
            "avg_runtime_seconds": 0,
            "avg_loc": 0,
            "avg_function_count": 0,
            "validation_pass_count": 0,
            "user_steps": None,
            "severity_totals": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "info": 0,
                "total": 0,
            },
        }

    severity_totals = {
        "critical": sum(item["severity"]["critical"] for item in successful),
        "high": sum(item["severity"]["high"] for item in successful),
        "medium": sum(item["severity"]["medium"] for item in successful),
        "low": sum(item["severity"]["low"] for item in successful),
        "info": sum(item["severity"]["info"] for item in successful),
        "total": sum(item["severity"]["total"] for item in successful),
    }

    return {
        "contracts": count,
        "avg_runtime_seconds": round(sum(item["runtime_seconds"] for item in successful) / count, 2),
        "avg_loc": round(sum(item["loc"] for item in successful) / count, 2),
        "avg_function_count": round(sum(item["function_count"] for item in successful) / count, 2),
        "validation_pass_count": sum(1 for item in successful if item.get("validation_success")),
        "user_steps": successful[0].get("user_steps"),
        "severity_totals": severity_totals,
    }


def load_report_issues(item, method):
    if method == "manual":
        report_path = Path(item["analysis_report_path"])
    else:
        report_path = ROOT_DIR / item["output_dir"] / "stage3_report.json"

    report = load_json(report_path)
    return report.get("initial_analysis", {}).get("issues", [])


def build_tool_breakdown(items, method):
    counts = Counter()
    severities = defaultdict(lambda: Counter())

    for item in items:
        if item.get("status") != "success":
            continue

        for issue in load_report_issues(item, method):
            tool = issue.get("tool", "unknown")
            severity = issue.get("severity", "UNKNOWN").lower()
            counts[tool] += 1
            severities[tool][severity] += 1

    breakdown = {}
    for tool, total in sorted(counts.items()):
        breakdown[tool] = {
            "total": total,
            "severity_counts": dict(sorted(severities[tool].items())),
        }
    return breakdown


def build_per_contract(pipeline_items, manual_items):
    manual_by_id = {item["id"]: item for item in manual_items}
    rows = []

    for pipeline_item in pipeline_items:
        if pipeline_item.get("status") != "success":
            continue

        manual_item = manual_by_id.get(pipeline_item["id"])
        if not manual_item or manual_item.get("status") != "success":
            continue

        rows.append(
            {
                "id": pipeline_item["id"],
                "task_name": pipeline_item["task_name"],
                "category": pipeline_item["category"],
                "pipeline": {
                    "runtime_seconds": round(pipeline_item["runtime_seconds"], 2),
                    "loc": pipeline_item["loc"],
                    "function_count": pipeline_item["function_count"],
                    "validation_success": pipeline_item["validation_success"],
                    "severity": pipeline_item["severity"],
                },
                "manual_llm": {
                    "runtime_seconds": round(manual_item["runtime_seconds"], 2),
                    "loc": manual_item["loc"],
                    "function_count": manual_item["function_count"],
                    "validation_success": manual_item["validation_success"],
                    "severity": manual_item["severity"],
                    "model": manual_item.get("model"),
                },
            }
        )

    return rows


def main():
    pipeline_items = load_json(PIPELINE_RESULTS_PATH)
    manual_items = load_json(MANUAL_RESULTS_PATH)

    result = {
        "result_id": "result_04",
        "title": "Automated Pipeline vs Manual LLM Workflow",
        "source_files": {
            "pipeline_results": str(PIPELINE_RESULTS_PATH),
            "manual_llm_results": str(MANUAL_RESULTS_PATH),
        },
        "methods": {
            "pipeline": {
                "workflow": ["stage_1", "stage_2", "stage_3"],
                **aggregate_method(pipeline_items),
                "tool_breakdown": build_tool_breakdown(pipeline_items, "pipeline"),
            },
            "manual_llm": {
                "workflow": ["direct_llm_generation", "stage_3"],
                **aggregate_method(manual_items),
                "tool_breakdown": build_tool_breakdown(manual_items, "manual"),
            },
        },
        "per_contract": build_per_contract(pipeline_items, manual_items),
    }

    OUTPUT_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
