import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from run_pipeline import run_full_pipeline
from stage_2_v2.helpers_v2 import validate_generated_code
from stage_3 import run_stage3
from stage_3.models import Severity

load_dotenv()

DATASET_PATH = BASE_DIR / "dataset.json"
PIPELINE_RESULTS = BASE_DIR / "pipeline_results.json"
MANUAL_RESULTS = BASE_DIR / "manual_llm_results.json"
MANUAL_OUTPUTS_DIR = BASE_DIR / "manual_outputs"

STAGE3_TOOLS = ["slither", "mythril", "semgrep", "solhint"]
PIPELINE_STAGE3_OPTIONS = {
    "enable_stage3": True,
    "skip_auto_fix": True,
    "max_iterations": 1,
    "verbose": False,
}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")
OPENAI_MODEL = os.getenv("RESULT04_MANUAL_MODEL", "gpt-4o")


def load_dataset():
    with open(DATASET_PATH, encoding="utf-8") as f:
        return json.load(f)


def ensure_dirs():
    MANUAL_OUTPUTS_DIR.mkdir(exist_ok=True)


def count_non_empty_lines(code: str) -> int:
    return sum(1 for line in code.splitlines() if line.strip())


def count_functions(code: str) -> int:
    return len(re.findall(r"\bfunction\s+\w+\s*\(", code))


def summarize_analysis(analysis_result):
    if not analysis_result:
        return {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0,
            "total": 0,
        }

    return {
        "critical": len(analysis_result.get_by_severity(Severity.CRITICAL)),
        "high": len(analysis_result.get_by_severity(Severity.HIGH)),
        "medium": len(analysis_result.get_by_severity(Severity.MEDIUM)),
        "low": len(analysis_result.get_by_severity(Severity.LOW)),
        "info": len(analysis_result.get_by_severity(Severity.INFO)),
        "total": len(analysis_result.issues),
    }


def build_common_metrics(code: str):
    validation = validate_generated_code(code, debug=False)
    return {
        "loc": count_non_empty_lines(code),
        "function_count": count_functions(code),
        "validation_success": validation["is_valid"],
        "validation_errors": validation["errors"],
        "validation_warnings": validation["warnings"],
        "compilation_success": None,
    }


def strip_code_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```solidity"):
        text = text[len("```solidity"):].strip()
    elif text.startswith("```"):
        text = text[3:].strip()
    if text.endswith("```"):
        text = text[:-3].strip()
    return text


def build_manual_generation_prompt(user_prompt: str) -> str:
    return f"""Generate a complete Solidity smart contract for the following user request.

User request:
{user_prompt}

Rules:
- Return only Solidity code
- Include SPDX license identifier
- Include pragma solidity ^0.8.20;
- Produce one complete contract file
- Do not include markdown fences
"""


def generate_manual_contract(user_prompt: str) -> str:
    if not OPENAI_API_KEY:
        raise RuntimeError("OpenAI API key not found for manual LLM workflow")

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": "You are an expert Solidity developer. Return only Solidity code.",
            },
            {
                "role": "user",
                "content": build_manual_generation_prompt(user_prompt),
            },
        ],
    )
    code = response.choices[0].message.content or ""
    return strip_code_fences(code)


def run_automated_pipeline(item):
    prompt = item["prompt"]
    start = time.perf_counter()

    try:
        result = run_full_pipeline(prompt, PIPELINE_STAGE3_OPTIONS)
        runtime = time.perf_counter() - start

        if not result:
            return {
                "id": item["id"],
                "task_name": item["task_name"],
                "category": item["category"],
                "prompt": prompt,
                "method": "pipeline",
                "status": "failed",
                "user_steps": 1,
                "runtime_seconds": runtime,
            }

        code = result["stage2_result"].solidity_code
        analysis_result = result["stage3_result"].initial_analysis if result["stage3_result"] else None

        return {
            "id": item["id"],
            "task_name": item["task_name"],
            "category": item["category"],
            "prompt": prompt,
            "method": "pipeline",
            "status": "success",
            "user_steps": 1,
            "runtime_seconds": runtime,
            "output_dir": result["output_dir"],
            "contract_name": result["spec"].get("contract_name"),
            "severity": summarize_analysis(analysis_result),
            **build_common_metrics(code),
        }
    except Exception as exc:
        runtime = time.perf_counter() - start
        return {
            "id": item["id"],
            "task_name": item["task_name"],
            "category": item["category"],
            "prompt": prompt,
            "method": "pipeline",
            "status": "error",
            "user_steps": 1,
            "runtime_seconds": runtime,
            "error": str(exc),
        }


def run_manual_llm_workflow(item):
    prompt = item["prompt"]
    output_dir = MANUAL_OUTPUTS_DIR / item["id"]
    output_dir.mkdir(parents=True, exist_ok=True)

    start = time.perf_counter()

    try:
        code = generate_manual_contract(prompt)
        contract_path = output_dir / "manual_generated.sol"
        contract_path.write_text(code, encoding="utf-8")

        stage3_result = run_stage3(
            solidity_code=code,
            contract_name=item["task_name"].replace(" ", ""),
            stage2_metadata=None,
            max_iterations=1,
            tools=STAGE3_TOOLS,
            skip_auto_fix=True,
        )

        report_path = output_dir / "stage3_report.json"
        report_path.write_text(json.dumps(stage3_result.to_dict(), indent=2), encoding="utf-8")
        runtime = time.perf_counter() - start

        return {
            "id": item["id"],
            "task_name": item["task_name"],
            "category": item["category"],
            "prompt": prompt,
            "method": "manual_llm",
            "status": "success",
            "user_steps": 3,
            "runtime_seconds": runtime,
            "model": OPENAI_MODEL,
            "output_dir": str(output_dir),
            "contract_path": str(contract_path),
            "analysis_report_path": str(report_path),
            "severity": summarize_analysis(stage3_result.initial_analysis),
            **build_common_metrics(code),
        }
    except Exception as exc:
        runtime = time.perf_counter() - start
        return {
            "id": item["id"],
            "task_name": item["task_name"],
            "category": item["category"],
            "prompt": prompt,
            "method": "manual_llm",
            "status": "error",
            "user_steps": 3,
            "runtime_seconds": runtime,
            "model": OPENAI_MODEL,
            "error": str(exc),
        }


def save_results(path: Path, results):
    path.write_text(json.dumps(results, indent=2), encoding="utf-8")


def run_experiment(mode: str = "all", limit: int | None = None):
    ensure_dirs()
    dataset = load_dataset()

    if limit:
        dataset = dataset[:limit]

    pipeline_results = []
    manual_results = []

    for item in dataset:
        print(f"\nRunning task: {item['task_name']}")

        if mode in {"all", "pipeline"}:
            pipeline_results.append(run_automated_pipeline(item))

        if mode in {"all", "manual"}:
            manual_results.append(run_manual_llm_workflow(item))

    if mode in {"all", "pipeline"}:
        save_results(PIPELINE_RESULTS, pipeline_results)
        print(f"\nSaved pipeline results to: {PIPELINE_RESULTS}")

    if mode in {"all", "manual"}:
        save_results(MANUAL_RESULTS, manual_results)
        print(f"Saved manual results to: {MANUAL_RESULTS}")


def main():
    parser = argparse.ArgumentParser(description="Result 04 runner: automated pipeline vs manual LLM workflow")
    parser.add_argument(
        "--mode",
        choices=["all", "pipeline", "manual"],
        default="all",
        help="Choose which workflow to run",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Run only the first N dataset entries",
    )
    args = parser.parse_args()

    run_experiment(mode=args.mode, limit=args.limit)


if __name__ == "__main__":
    main()
