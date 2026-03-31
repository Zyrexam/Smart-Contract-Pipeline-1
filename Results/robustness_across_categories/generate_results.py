import json
from collections import defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parents[1]

RESOURCE_RESULTS_PATH = ROOT_DIR / "Results" / "pipeline_resource_usage" / "resource_results.json"
OUTPUT_PATH = BASE_DIR / "category_results.json"
SUMMARY_PATH = BASE_DIR / "category_summary.json"
MARKDOWN_PATH = BASE_DIR / "category_summary.md"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_per_category(records):
    grouped = defaultdict(list)
    for record in records:
        grouped[record.get("category", "Unknown")].append(record)

    rows = []
    for category, items in sorted(grouped.items()):
        total_runs = len(items)
        successful = [item for item in items if item.get("status") == "success"]
        success_count = len(successful)

        if success_count == 0:
            rows.append(
                {
                    "category": category,
                    "total_runs": total_runs,
                    "successful_runs": 0,
                    "success_rate": 0.0,
                    "avg_runtime_seconds": 0.0,
                    "avg_loc": 0.0,
                    "avg_function_count": 0.0,
                    "avg_issue_count": 0.0,
                    "max_issue_count": 0,
                    "contracts": [],
                }
            )
            continue

        rows.append(
            {
                "category": category,
                "total_runs": total_runs,
                "successful_runs": success_count,
                "success_rate": round((success_count / total_runs) * 100, 2),
                "avg_runtime_seconds": round(sum(item.get("runtime_seconds", 0) for item in successful) / success_count, 2),
                "avg_loc": round(sum(item.get("loc", 0) for item in successful) / success_count, 2),
                "avg_function_count": round(sum(item.get("function_count", 0) for item in successful) / success_count, 2),
                "avg_issue_count": round(sum(item.get("stage3_issue_count", 0) for item in successful) / success_count, 2),
                "max_issue_count": max(item.get("stage3_issue_count", 0) for item in successful),
                "contracts": [
                    {
                        "id": item.get("id"),
                        "task_name": item.get("task_name"),
                        "contract_name": item.get("contract_name"),
                        "runtime_seconds": round(item.get("runtime_seconds", 0), 2),
                        "loc": item.get("loc", 0),
                        "function_count": item.get("function_count", 0),
                        "stage3_issue_count": item.get("stage3_issue_count", 0),
                        "output_dir": item.get("output_dir"),
                    }
                    for item in successful
                ],
            }
        )

    return rows


def build_summary(records, per_category):
    total_runs = len(records)
    successful = [item for item in records if item.get("status") == "success"]
    success_count = len(successful)

    if success_count == 0:
        return {
            "dataset_size": total_runs,
            "successful_runs": 0,
            "overall_success_rate": 0.0,
            "avg_runtime_seconds": 0.0,
            "avg_loc": 0.0,
            "avg_function_count": 0.0,
            "avg_issue_count": 0.0,
            "highest_issue_category": None,
            "highest_runtime_category": None,
            "largest_code_category": None,
            "category_count": len(per_category),
            "category_summary": per_category,
        }

    highest_issue_category = max(per_category, key=lambda item: item["avg_issue_count"]) if per_category else None
    highest_runtime_category = max(per_category, key=lambda item: item["avg_runtime_seconds"]) if per_category else None
    largest_code_category = max(per_category, key=lambda item: item["avg_loc"]) if per_category else None

    return {
        "dataset_size": total_runs,
        "successful_runs": success_count,
        "overall_success_rate": round((success_count / total_runs) * 100, 2),
        "avg_runtime_seconds": round(sum(item.get("runtime_seconds", 0) for item in successful) / success_count, 2),
        "avg_loc": round(sum(item.get("loc", 0) for item in successful) / success_count, 2),
        "avg_function_count": round(sum(item.get("function_count", 0) for item in successful) / success_count, 2),
        "avg_issue_count": round(sum(item.get("stage3_issue_count", 0) for item in successful) / success_count, 2),
        "highest_issue_category": {
            "category": highest_issue_category["category"],
            "avg_issue_count": highest_issue_category["avg_issue_count"],
        } if highest_issue_category else None,
        "highest_runtime_category": {
            "category": highest_runtime_category["category"],
            "avg_runtime_seconds": highest_runtime_category["avg_runtime_seconds"],
        } if highest_runtime_category else None,
        "largest_code_category": {
            "category": largest_code_category["category"],
            "avg_loc": largest_code_category["avg_loc"],
        } if largest_code_category else None,
        "category_count": len(per_category),
        "category_summary": per_category,
    }


def write_markdown(summary):
    lines = [
        "# Robustness Across Contract Categories",
        "",
        "## Experimental Summary",
        "",
        f"- Dataset size: {summary['dataset_size']}",
        f"- Successful runs: {summary['successful_runs']}",
        f"- Overall success rate: {summary['overall_success_rate']}%",
        f"- Avg runtime per contract: {summary['avg_runtime_seconds']} seconds",
        f"- Avg LOC per contract: {summary['avg_loc']}",
        f"- Avg function count per contract: {summary['avg_function_count']}",
        f"- Avg Stage 3 issue count per contract: {summary['avg_issue_count']}",
        "",
        "## Category Highlights",
        "",
    ]

    if summary["highest_issue_category"]:
        lines.append(
            f"- Highest average issue count: {summary['highest_issue_category']['category']} "
            f"({summary['highest_issue_category']['avg_issue_count']})"
        )
    if summary["highest_runtime_category"]:
        lines.append(
            f"- Highest average runtime: {summary['highest_runtime_category']['category']} "
            f"({summary['highest_runtime_category']['avg_runtime_seconds']} seconds)"
        )
    if summary["largest_code_category"]:
        lines.append(
            f"- Largest average code size: {summary['largest_code_category']['category']} "
            f"({summary['largest_code_category']['avg_loc']} LOC)"
        )

    lines.extend(["", "## Category Summary", ""])
    for item in summary["category_summary"]:
        lines.append(
            f"- {item['category']}: success {item['successful_runs']}/{item['total_runs']}, "
            f"avg runtime {item['avg_runtime_seconds']}s, avg LOC {item['avg_loc']}, "
            f"avg functions {item['avg_function_count']}, avg issues {item['avg_issue_count']}"
        )

    MARKDOWN_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    records = load_json(RESOURCE_RESULTS_PATH)
    per_category = build_per_category(records)
    summary = build_summary(records, per_category)

    OUTPUT_PATH.write_text(json.dumps(per_category, indent=2), encoding="utf-8")
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_markdown(summary)

    print(f"Saved {OUTPUT_PATH}")
    print(f"Saved {SUMMARY_PATH}")
    print(f"Saved {MARKDOWN_PATH}")


if __name__ == "__main__":
    main()
