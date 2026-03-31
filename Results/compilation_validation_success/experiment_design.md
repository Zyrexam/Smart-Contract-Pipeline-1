# Result: Compilation and Validation Success

## Objective

Measure how often the proposed pipeline produces contracts that successfully compile, validate, and pass stage-level execution without breakdown.

This experiment provides an objective reliability result for the overall system.

## Scope

Use pipeline outputs, generation metadata, and Stage 3 reports to track whether each run produced a usable contract.

Possible success checkpoints:

- Stage 1 spec generated successfully
- Stage 2 contract generated successfully
- Solidity contract compiled successfully
- Stage 3 analysis completed successfully
- final contract produced successfully

## Research Questions

1. What percentage of user prompts lead to a valid end-to-end pipeline result?
2. At which stage do failures occur most often?
3. Does validation success vary by contract category or model source?

## Evaluation Metrics

### End-to-End Reliability

- total runs
- successful end-to-end runs
- end-to-end success rate

### Stage-Wise Reliability

- Stage 1 success count and percentage
- Stage 2 success count and percentage
- compilation success count and percentage
- Stage 3 success count and percentage

### Breakdown Analysis

- number of failures by stage
- percentage of failures by stage

## Dataset

Use all available runs in `pipeline_outputs/`.

Optional extensions:

- compare against manual workflow outputs
- compare against direct LLM outputs in `Results/llm_comparison`

## Procedure

1. Enumerate all pipeline runs.
2. Check presence and validity of `stage1_spec.json`, generated `.sol` file, and `stage3_report.json`.
3. Extract compile or validation status from metadata and reports where available.
4. Classify each run as successful, partially successful, or failed.
5. Aggregate results overall and by category.

## Expected Outputs

- `validation_results.json`
- `validation_summary.json`
- `plots/stage_success_rates.png`
- `plots/failure_stage_breakdown.png`

## Expected Tables

### Table 1 - End-to-End Pipeline Reliability

| Metric | Value |
| ------ | ----- |
| Total runs | |
| Successful runs | |
| Success rate | |

### Table 2 - Stage-Wise Success Rates

| Stage | Success Count | Success Rate |
| ----- | ------------- | ------------ |
| Stage 1 | | |
| Stage 2 | | |
| Compilation | | |
| Stage 3 | | |

### Table 3 - Failure Breakdown

| Failure Type | Count |
| ------------ | ----- |
| Spec generation failed | |
| Code generation failed | |
| Compilation failed | |
| Security analysis failed | |

## Notes

- This result is simple but important for demonstrating system dependability.
- Define success criteria clearly and keep them fixed across all runs.
- If metadata is incomplete for older runs, mark those entries explicitly rather than guessing.
