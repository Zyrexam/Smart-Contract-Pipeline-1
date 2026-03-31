# Result: Failure Case Analysis

## Objective

Analyze where and why the pipeline fails, degrades, or produces weak outputs.

This section improves research credibility by documenting limitations instead of reporting only positive results.

## Scope

Use failed or low-quality runs from the pipeline, manual workflow comparison, vulnerable-dataset experiments, and cross-model outputs where useful.

Failure may include:

- malformed or incomplete Stage 1 specification
- incorrect or partial Stage 2 contract generation
- compilation failure
- Stage 3 tool failure
- unresolved security findings after auto-fix
- category-specific weaknesses

## Research Questions

1. What are the most common failure modes in the pipeline?
2. Which stage contributes most to end-to-end breakdown?
3. Are failures caused by model output quality, orchestration issues, or analyzer limitations?
4. What limitations remain even when the pipeline completes successfully?

## Failure Taxonomy

### Stage 1 Failures

- missing required fields
- invalid JSON or malformed structure
- vague or underspecified contract behavior

### Stage 2 Failures

- incomplete code
- mismatch between spec and code
- missing access control or event logic
- invalid Solidity syntax

### Stage 3 Failures

- analyzer crash or timeout
- parser mismatch
- false negatives or inconsistent tool output
- issues that remain unresolved after fix iterations

## Evaluation Metrics

- failure count by stage
- failure percentage by stage
- unresolved issue count after auto-fix
- number of tool-execution failures
- representative failure examples

## Procedure

1. Collect runs with explicit errors, missing artifacts, or poor final outcomes.
2. Label each case using the failure taxonomy.
3. Count recurring failure patterns.
4. Select representative examples for qualitative discussion.
5. Summarize implications for future improvement.

## Expected Outputs

- `failure_cases.json`
- `failure_summary.json`
- `case_studies.md`

## Expected Tables

### Table 1 - Failure Mode Distribution

| Failure Mode | Count | Stage |
| ------------ | ----- | ----- |
| Invalid spec | | Stage 1 |
| Incomplete contract | | Stage 2 |
| Compilation error | | Stage 2 |
| Stage 3 tool failure | | Stage 3 |

### Table 2 - Representative Failure Cases

| Case ID | Prompt / Contract | Failure Type | Short Description |
| ------- | ----------------- | ------------ | ----------------- |
| | | | |

## Notes

- Keep this section concise but honest.
- Use 3 to 5 representative cases rather than listing every minor error.
- This section pairs especially well with the standalone security and validation sections.
