# Security Evaluation

This folder contains the standalone security result for the pipeline.

## Files

- `experiment_design.md` - experiment plan and expected tables
- `generate_results.py` - builds aggregate security outputs from `pipeline_outputs/`
- `security_results.json` - per-run security records
- `security_summary.json` - aggregate paper-ready metrics
- `security_summary.md` - readable summary for report drafting

## Usage

```powershell
python Results/security_evaluation/generate_results.py
```

## Data Source

The script reads:

- `pipeline_outputs/<run_id>/stage3_report.json`
- `pipeline_outputs/<run_id>/metadata.json` when available

It summarizes:

- severity totals
- contracts with findings
- improvement after Stage 3 fix
- category-wise issue averages
- most common issue titles
- tool-wise issue counts
