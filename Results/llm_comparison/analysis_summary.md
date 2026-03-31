# Result 5: Results and Discussion

## Experimental Summary

- Total runs: 42
- Successful runs: 38 (90.5%)
- Invalid generations: 0 (0.0%)
- Errors: 4 (9.5%)

## Overall Findings

The comparison shows a clear trade-off between runtime, contract richness, and security reliability. Pipeline achieved the strongest validation performance at 100.0%, indicating the most consistent generation quality across the dataset. Llama2 produced the lowest average issue count at 6.00; however, this result should be interpreted together with code complexity metrics because lower issue counts can coincide with shorter and simpler contracts. Grok was the fastest model with an average runtime of 20.08 seconds, while Pipeline generated the richest contracts with an average size of 70.0 non-empty lines.

## Model-Wise Interpretation

- Pipeline: avg runtime 45.35s, avg issues 13.17, validation 100.0%, avg LOC 70.0, avg functions 4.7
- GPT: avg runtime 37.68s, avg issues 21.67, validation 66.7%, avg LOC 47.2, avg functions 4.2
- Grok: avg runtime 20.08s, avg issues 14.33, validation 100.0%, avg LOC 51.0, avg functions 2.8
- CodeLlama: avg runtime 50.88s, avg issues 7.20, validation 83.3%, avg LOC 21.8, avg functions 2.6
- Gemma: avg runtime 27.05s, avg issues 7.40, validation 33.3%, avg LOC 36.6, avg functions 3.2
- Mistral: avg runtime 59.78s, avg issues 10.80, validation 66.7%, avg LOC 25.6, avg functions 2.4
- Llama2: avg runtime 53.96s, avg issues 6.00, validation 83.3%, avg LOC 23.6, avg functions 2.6

## Security Interpretation

The results indicate that direct LLM generation does not consistently optimize for secure contract construction. Models with higher function counts and richer code structure often accumulated more medium-severity findings, showing that contract complexity can expose more security weaknesses when generation is not guided by a structured pipeline. Conversely, some smaller local models achieved lower average issue counts partly because they generated shorter, simpler contracts with fewer behaviors to analyze. This means that lower vulnerability counts alone should not be treated as proof of better contract quality.

## Runtime and Quality Trade-Off

The runtime comparison suggests that faster generation does not automatically imply better outputs. Rapid models can be attractive for throughput, but they may sacrifice validation consistency or contract completeness. Slower approaches, especially structured generation pipelines, appear to gain reliability from additional processing stages such as validation and security analysis. This supports the claim that secure contract generation benefits from orchestration rather than relying on a single-pass LLM response.

## Category-Level Observations

- Finance: Llama2: 6.67, CodeLlama: 9.67, Gemma: 9.67, Mistral: 13.0, Pipeline: 16.67, Grok: 21.0, GPT: 25.67
- Governance: Llama2: 0.0, CodeLlama: 3.0, Gemma: 3.0, Mistral: 9.0, Grok: 11.0, Pipeline: 16.0, GPT: 28.0
- NFT: Pipeline: 7.0, Grok: 10.0, GPT: 23.0
- Token: GPT: 2.0, Grok: 2.0, CodeLlama: 4.0, Gemma: 5.0, Pipeline: 6.0, Mistral: 6.0, Llama2: 10.0

## Plot Interpretation Guide

- Plot 1 (Runtime Comparison): compares model speed and highlights the runtime overhead of structured generation.
- Plot 2 (Security Issues): compares high- and medium-severity findings to show security differences across models.
- Plot 3 (Code Metrics): shows average LOC and function count, helping explain whether lower issue counts come from simpler code.
- Plot 4 (Validation Success): summarizes how consistently each model generates code that passes validation checks.
- Plot 5 (Runtime vs Security): visualizes the speed-quality trade-off across models.
- Plot 6 (Heatmap): provides a compact all-metric comparison for paper figures or slides.
- Plot 7 (Issue Distribution): shows the overall severity profile across all successful runs.

## Final Result Statement

Overall, the experimental evidence suggests that standalone LLMs can generate workable smart contracts, but their outputs remain inconsistent in validation quality and security posture. A structured multi-stage pipeline provides a more reliable balance of correctness, contract completeness, and vulnerability awareness, making it a stronger choice for production-oriented smart contract generation workflows.
