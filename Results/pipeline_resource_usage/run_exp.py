import argparse
import json
import os
import re
import sys
import time
import tracemalloc
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from run_pipeline import run_full_pipeline


DATASET_PATH = BASE_DIR / "dataset.json"
RESOURCE_RESULTS_PATH = BASE_DIR / "resource_results.json"
RESOURCE_SUMMARY_PATH = BASE_DIR / "resource_summary.json"

PIPELINE_STAGE3_OPTIONS = {
    "enable_stage3": True,
    "skip_auto_fix": True,
    "max_iterations": 1,
    "verbose": False,
}


def load_dataset():
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


def count_non_empty_lines(code: str) -> int:
    return sum(1 for line in code.splitlines() if line.strip())


def count_functions(code: str) -> int:
    return len(re.findall(r"\bfunction\s+\w+\s*\(", code))


def mb(num_bytes: int) -> float:
    return round(num_bytes / (1024 * 1024), 4)


def build_record(item, result, wall_time, cpu_time, current_mem, peak_mem):
    if not result:
        return {
            "id": item["id"],
            "task_name": item["task_name"],
            "category": item["category"],
            "status": "failed",
            "runtime_seconds": round(wall_time, 4),
            "cpu_time_seconds": round(cpu_time, 4),
            "memory_current_mb": mb(current_mem),
            "memory_peak_mb": mb(peak_mem),
        }

    code = result["stage2_result"].solidity_code
    stage3_result = result.get("stage3_result")
    issue_count = len(stage3_result.initial_analysis.issues) if stage3_result and stage3_result.initial_analysis else 0

    return {
        "id": item["id"],
        "task_name": item["task_name"],
        "category": item["category"],
        "status": "success",
        "runtime_seconds": round(wall_time, 4),
        "cpu_time_seconds": round(cpu_time, 4),
        "memory_current_mb": mb(current_mem),
        "memory_peak_mb": mb(peak_mem),
        "output_dir": result["output_dir"],
        "contract_name": result["spec"].get("contract_name"),
        "loc": count_non_empty_lines(code),
        "function_count": count_functions(code),
        "stage3_issue_count": issue_count,
    }


def summarize_results(results):
    successful = [item for item in results if item.get("status") == "success"]
    by_category = defaultdict(list)
    for item in successful:
        by_category[item["category"]].append(item)

    summary = {
        "contracts": len(successful),
        "avg_runtime_seconds": round(sum(x["runtime_seconds"] for x in successful) / len(successful), 4) if successful else 0,
        "avg_cpu_time_seconds": round(sum(x["cpu_time_seconds"] for x in successful) / len(successful), 4) if successful else 0,
        "avg_memory_peak_mb": round(sum(x["memory_peak_mb"] for x in successful) / len(successful), 4) if successful else 0,
        "avg_loc": round(sum(x["loc"] for x in successful) / len(successful), 2) if successful else 0,
        "avg_function_count": round(sum(x["function_count"] for x in successful) / len(successful), 2) if successful else 0,
        "by_category": {},
    }

    for category, items in sorted(by_category.items()):
        summary["by_category"][category] = {
            "contracts": len(items),
            "avg_runtime_seconds": round(sum(x["runtime_seconds"] for x in items) / len(items), 4),
            "avg_cpu_time_seconds": round(sum(x["cpu_time_seconds"] for x in items) / len(items), 4),
            "avg_memory_peak_mb": round(sum(x["memory_peak_mb"] for x in items) / len(items), 4),
            "avg_loc": round(sum(x["loc"] for x in items) / len(items), 2),
            "avg_function_count": round(sum(x["function_count"] for x in items) / len(items), 2),
        }

    return summary


def run_single(item):
    tracemalloc.start()
    start_wall = time.perf_counter()
    start_cpu = time.process_time()

    try:
        result = run_full_pipeline(item["prompt"], PIPELINE_STAGE3_OPTIONS)
        status_error = None
    except Exception as exc:
        result = None
        status_error = str(exc)

    end_cpu = time.process_time()
    end_wall = time.perf_counter()
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    record = build_record(
        item,
        result,
        end_wall - start_wall,
        end_cpu - start_cpu,
        current_mem,
        peak_mem,
    )
    if status_error:
        record["status"] = "error"
        record["error"] = status_error
    return record


def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Run simple pipeline resource usage experiment")
    parser.add_argument("--limit", type=int, help="Run only the first N dataset items")
    args = parser.parse_args()

    dataset = load_dataset()
    if args.limit:
        dataset = dataset[: args.limit]

    results = []
    for item in dataset:
        print(f"Running {item['id']} - {item['task_name']}")
        results.append(run_single(item))

    summary = summarize_results(results)
    save_json(RESOURCE_RESULTS_PATH, results)
    save_json(RESOURCE_SUMMARY_PATH, summary)

    print(f"Saved {RESOURCE_RESULTS_PATH}")
    print(f"Saved {RESOURCE_SUMMARY_PATH}")


if __name__ == "__main__":
    main()
