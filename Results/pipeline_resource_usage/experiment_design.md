# Result - Pipeline Resource Usage

## Objective

Measure the computational behavior of the proposed pipeline across contract categories.

The focus is on:

- runtime
- memory usage
- CPU usage
- code size

## Workflow

For each dataset prompt:

1. Run the existing pipeline.
2. Measure total runtime.
3. Measure process CPU time before and after execution.
4. Measure current and peak memory usage.
5. Record generated contract size and function count.

## Output Files

- `resource_results.json`
- `resource_summary.json`

## Notes

- This is a simple local resource study.
- CPU is recorded as process CPU time in seconds.
- Memory is recorded using Python `tracemalloc` peak memory in MB.
- The result is intended for paper tables and charts, not low-level profiling.
