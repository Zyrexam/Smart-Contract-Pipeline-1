# Result: Robustness Across Contract Categories

## Objective

Measure how consistently the proposed pipeline performs across different smart contract categories.

The purpose is to show that the pipeline is not limited to a single contract pattern or demo case.

## Scope

This experiment evaluates pipeline outputs across diverse functional categories using existing generated contracts and metadata.

Recommended categories:

- NFT
- token
- governance
- crowdfunding
- escrow
- marketplace
- auction
- timelock
- multisig
- DAO

## Research Questions

1. Does the pipeline complete successfully across different contract categories?
2. Do some categories produce more vulnerabilities or failures than others?
3. Does runtime or code size vary significantly by category?
4. Which categories are easiest or hardest for the pipeline?

## Evaluation Metrics

### Reliability

- pipeline completion rate by category
- Stage 1 success rate by category
- Stage 2 generation success rate by category
- Stage 3 completion rate by category

### Security

- average findings per category
- average high and medium findings per category
- percentage of contracts with at least one finding

### Output Characteristics

- average lines of code by category
- average function count by category
- average runtime by category

## Dataset

Use category-labeled prompts already represented in `pipeline_outputs/`.

If category labels are not explicit in metadata, assign them using the contract task or dataset prompt.

## Procedure

1. Build a category mapping for each contract run.
2. Aggregate success, runtime, and issue metrics by category.
3. Compare category-level averages.
4. Identify categories with unusually high failure or vulnerability counts.
5. Summarize what contract features may explain harder categories.

## Expected Outputs

- `category_results.json`
- `category_summary.json`
- `plots/category_success_rate.png`
- `plots/category_avg_issues.png`
- `plots/category_avg_runtime.png`
- `plots/category_avg_loc.png`

## Expected Tables

### Table 1 - Category-Wise Success Rates

| Category | Total Runs | Successful Runs | Success Rate |
| -------- | ---------- | --------------- | ------------ |
| NFT | | | |
| Token | | | |
| Governance | | | |
| Others | | | |

### Table 2 - Category-Wise Security Summary

| Category | Avg Total Issues | Avg High | Avg Medium |
| -------- | ---------------- | -------- | ---------- |
| NFT | | | |
| Token | | | |
| Governance | | | |
| Others | | | |

### Table 3 - Category-Wise Output Characteristics

| Category | Avg Runtime | Avg LOC | Avg Functions |
| -------- | ----------- | ------- | ------------- |
| NFT | | | |
| Token | | | |
| Governance | | | |
| Others | | | |

## Notes

- This result section supports the claim of general applicability.
- Keep category names consistent across all experiments.
- If sample sizes differ heavily between categories, report the run counts clearly.
