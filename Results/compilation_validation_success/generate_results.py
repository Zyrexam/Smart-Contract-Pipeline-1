import json
from collections import Counter, defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parents[1]

PIPELINE_RESULTS_PATH = ROOT_DIR / "Results" / "pipeline_vs_manual" / "pipeline_results.json"
OUTPUT_PATH = BASE_DIR / "validation_results.json"
SUMMARY_PATH = BASE_DIR / "validation_summary.json"
MARKDOWN_PATH = BASE_DIR / "validation_summary.md"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def file_exists(root_dir: Path, relative_path: str, filename: str):
    if not relative_path:
        return False
    return (root_dir / relative_path / filename).exists()


def detect_stage_status(item):
    output_dir = item.get("output_dir")
    stage1_success = file_exists(ROOT_DIR, output_dir, "stage1_spec.json")

    stage2_candidates = []
    if output_dir:
        run_dir = ROOT_DIR / output_dir
        if run_dir.exists():
            stage2_candidates = [
                path for path in run_dir.glob("*.sol")
                if not path.name.startswith("final_")
            ]

    stage2_success = len(stage2_candidates) > 0
    stage3_success = file_exists(ROOT_DIR, output_dir, "stage3_report.json")
    final_contract_success = False
    if output_dir:
        run_dir = ROOT_DIR / output_dir
        final_contract_success = any(run_dir.glob("final_*.sol")) if run_dir.exists() else False

    validation_success = bool(item.get("validation_success", False))
    validation_errors = item.get("validation_errors", []) or []
    validation_warnings = item.get("validation_warnings", []) or []

    compilation_success = item.get("compilation_success")
    if compilation_success is None:
        compilation_success = validation_success and len(validation_errors) == 0

    end_to_end_success = (
        item.get("status") == "success"
        and stage1_success
        and stage2_success
        and stage3_success
        and validation_success
    )

    return {
        "stage1_success": stage1_success,
        "stage2_success": stage2_success,
        "compilation_success": bool(compilation_success),
        "stage3_success": stage3_success,
        "final_contract_success": final_contract_success,
        "validation_success": validation_success,
        "validation_errors": validation_errors,
        "validation_warnings": validation_warnings,
        "end_to_end_success": end_to_end_success,
    }


def build_records(items):
    records = []
    for item in items:
        stage = detect_stage_status(item)
        records.append(
            {
                "id": item.get("id"),
                "task_name": item.get("task_name"),
                "category": item.get("category"),
                "status": item.get("status"),
                "runtime_seconds": round(item.get("runtime_seconds", 0), 2),
                "output_dir": item.get("output_dir"),
                "contract_name": item.get("contract_name"),
                **stage,
            }
        )
    return records


def build_summary(records):
    total_runs = len(records)
    if total_runs == 0:
        return {
            "total_runs": 0,
            "successful_end_to_end_runs": 0,
            "end_to_end_success_rate": 0.0,
            "stage_success_rates": {},
            "validation_pass_count": 0,
            "compilation_pass_count": 0,
            "warning_count": 0,
            "failure_breakdown": {},
            "category_summary": [],
        }

    stage_keys = [
        "stage1_success",
        "stage2_success",
        "compilation_success",
        "stage3_success",
        "validation_success",
        "final_contract_success",
        "end_to_end_success",
    ]

    stage_success_rates = {}
    for key in stage_keys:
        passed = sum(1 for record in records if record[key])
        stage_success_rates[key] = {
            "count": passed,
            "rate": round((passed / total_runs) * 100, 2),
        }

    failure_breakdown = Counter()
    warning_count = 0
    for record in records:
        if record["validation_warnings"]:
            warning_count += 1

        if not record["stage1_success"]:
            failure_breakdown["stage1_missing_spec"] += 1
        if not record["stage2_success"]:
            failure_breakdown["stage2_missing_contract"] += 1
        if not record["compilation_success"]:
            failure_breakdown["compilation_or_validation_failed"] += 1
        if not record["stage3_success"]:
            failure_breakdown["stage3_missing_report"] += 1
        if not record["final_contract_success"]:
            failure_breakdown["final_contract_not_generated"] += 1

    grouped = defaultdict(list)
    for record in records:
        grouped[record["category"]].append(record)

    category_summary = []
    for category, items in sorted(grouped.items()):
        total = len(items)
        end_to_end = sum(1 for item in items if item["end_to_end_success"])
        validation = sum(1 for item in items if item["validation_success"])
        compilation = sum(1 for item in items if item["compilation_success"])
        category_summary.append(
            {
                "category": category,
                "total_runs": total,
                "end_to_end_success_count": end_to_end,
                "end_to_end_success_rate": round((end_to_end / total) * 100, 2),
                "validation_success_count": validation,
                "validation_success_rate": round((validation / total) * 100, 2),
                "compilation_success_count": compilation,
                "compilation_success_rate": round((compilation / total) * 100, 2),
            }
        )

    return {
        "total_runs": total_runs,
        "successful_end_to_end_runs": stage_success_rates["end_to_end_success"]["count"],
        "end_to_end_success_rate": stage_success_rates["end_to_end_success"]["rate"],
        "validation_pass_count": stage_success_rates["validation_success"]["count"],
        "compilation_pass_count": stage_success_rates["compilation_success"]["count"],
        "warning_count": warning_count,
        "stage_success_rates": stage_success_rates,
        "failure_breakdown": dict(sorted(failure_breakdown.items())),
        "category_summary": category_summary,
    }


def write_markdown(summary):
    lines = [
        "# Compilation and Validation Success",
        "",
        "## Experimental Summary",
        "",
        "- Source dataset: Results/pipeline_vs_manual/pipeline_results.json",
        f"- Total runs: {summary['total_runs']}",
        f"- Successful end-to-end runs: {summary['successful_end_to_end_runs']}",
        f"- End-to-end success rate: {summary['end_to_end_success_rate']}%",
        f"- Validation pass count: {summary['validation_pass_count']}",
        f"- Compilation pass count: {summary['compilation_pass_count']}",
        f"- Runs with validation warnings: {summary['warning_count']}",
        "",
        "## Stage-Wise Success Rates",
        "",
    ]

    labels = {
        "stage1_success": "Stage 1 spec generation",
        "stage2_success": "Stage 2 contract generation",
        "compilation_success": "Compilation / validation",
        "stage3_success": "Stage 3 analysis",
        "validation_success": "Validation checks",
        "final_contract_success": "Final contract generation",
        "end_to_end_success": "End-to-end pipeline",
    }

    for key, value in summary["stage_success_rates"].items():
        lines.append(f"- {labels[key]}: {value['count']}/{summary['total_runs']} ({value['rate']}%)")

    lines.extend(["", "## Failure Breakdown", ""])
    for key, value in summary["failure_breakdown"].items():
        lines.append(f"- {key}: {value}")

    lines.extend(["", "## Category Summary", ""])
    for item in summary["category_summary"]:
        lines.append(
            f"- {item['category']}: end-to-end {item['end_to_end_success_count']}/{item['total_runs']}, "
            f"validation {item['validation_success_count']}/{item['total_runs']}, "
            f"compilation {item['compilation_success_count']}/{item['total_runs']}"
        )

    MARKDOWN_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    items = load_json(PIPELINE_RESULTS_PATH)
    records = build_records(items)
    summary = build_summary(records)

    OUTPUT_PATH.write_text(json.dumps(records, indent=2), encoding="utf-8")
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    write_markdown(summary)

    print(f"Saved {OUTPUT_PATH}")
    print(f"Saved {SUMMARY_PATH}")
    print(f"Saved {MARKDOWN_PATH}")


if __name__ == "__main__":
    main()
