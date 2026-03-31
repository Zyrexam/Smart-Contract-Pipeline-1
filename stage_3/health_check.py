"""
Quick Stage 3 health check.

Runs a small set of known vulnerable contracts through Stage 3 in analysis-only
mode and prints a per-tool severity summary. This is meant to be a simple
preflight check before generating experimental results.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from stage_3 import run_stage3
from stage_3.models import Severity


ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT_DIR / "Results" / "stage3_health_check.json"

TEST_CASES = [
    {
        "name": "reentrancy",
        "path": ROOT_DIR / "vulnerable_dataset" / "ReentrancyBank.sol",
    },
    {
        "name": "access_control",
        "path": ROOT_DIR / "vulnerable_dataset" / "UnprotectedVault.sol",
    },
]


def summarize_by_tool(issues):
    summary = defaultdict(lambda: {"HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0, "TOTAL": 0})
    for issue in issues:
        tool_summary = summary[issue.tool]
        tool_summary[issue.severity.value] += 1
        tool_summary["TOTAL"] += 1
    return dict(summary)


def run_case(case):
    code = case["path"].read_text(encoding="utf-8")
    result = run_stage3(
        solidity_code=code,
        contract_name=case["name"],
        stage2_metadata=None,
        max_iterations=1,
        tools=["slither", "mythril", "semgrep", "solhint"],
        skip_auto_fix=True,
    )
    return {
        "case": case["name"],
        "source_file": str(case["path"]),
        "total_issues": len(result.initial_analysis.issues),
        "severity": {
            "critical": len(result.initial_analysis.get_by_severity(Severity.CRITICAL)),
            "high": len(result.initial_analysis.get_by_severity(Severity.HIGH)),
            "medium": len(result.initial_analysis.get_by_severity(Severity.MEDIUM)),
            "low": len(result.initial_analysis.get_by_severity(Severity.LOW)),
            "info": len(result.initial_analysis.get_by_severity(Severity.INFO)),
        },
        "by_tool": summarize_by_tool(result.initial_analysis.issues),
        "tools_used": result.initial_analysis.tools_used,
    }


def main():
    parser = argparse.ArgumentParser(description="Quick Stage 3 health check")
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT),
        help="Where to save the JSON summary",
    )
    args = parser.parse_args()

    summaries = []
    for case in TEST_CASES:
        if not case["path"].exists():
            print(f"Skipping missing test case: {case['path']}")
            continue
        print(f"\nChecking: {case['name']}")
        summary = run_case(case)
        summaries.append(summary)

        print(f"  Total issues: {summary['total_issues']}")
        for tool, counts in summary["by_tool"].items():
            print(
                f"  {tool}: "
                f"H={counts['HIGH']} M={counts['MEDIUM']} "
                f"L={counts['LOW']} I={counts['INFO']} T={counts['TOTAL']}"
            )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    print(f"\nSaved health check summary to: {output_path}")


if __name__ == "__main__":
    main()
