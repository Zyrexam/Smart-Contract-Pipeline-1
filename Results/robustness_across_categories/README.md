# Robustness Across Contract Categories

This folder summarizes how the pipeline behaves across different smart contract categories.

## Files

- `experiment_design.md` - experiment plan
- `generate_results.py` - builds category-level summary outputs
- `category_results.json` - detailed per-category metrics
- `category_summary.json` - aggregate summary
- `category_summary.md` - readable report draft summary

## Usage

```powershell
python Results/robustness_across_categories/generate_results.py
```

## Data Source

The current implementation uses:

- `Results/pipeline_resource_usage/resource_results.json`

This keeps the category analysis tied to a clean, controlled dataset rather than all historical runs in `pipeline_outputs/`.
