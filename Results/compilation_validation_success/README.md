# Compilation and Validation Success

This folder captures pipeline reliability across stage completion, validation, and final artifact generation.

## Files

- `experiment_design.md` - experiment plan
- `generate_results.py` - builds reliability outputs from existing pipeline results
- `validation_results.json` - per-run stage and validation status
- `validation_summary.json` - aggregate reliability summary
- `validation_summary.md` - readable paper-facing summary

## Usage

```powershell
python Results/compilation_validation_success/generate_results.py
```

## Data Source

The current implementation uses:

- `Results/pipeline_vs_manual/pipeline_results.json`

It also checks whether expected files exist inside each referenced `pipeline_outputs/<run_id>/` directory.
