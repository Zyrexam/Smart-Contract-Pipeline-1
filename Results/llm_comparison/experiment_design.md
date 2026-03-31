# Result 5: LLM Comparison

## Objective

Compare our pipeline against direct contract generation from selected LLMs on the same smart contract prompts.

## Models Compared

* Pipeline
* CodeGemma 2B
* CodeLlama
* Gemma 2B
* Mistral
* Qwen 3.5 4B
* Grok

## Dataset

Use `dataset.json` in this folder.

## Evaluation Flow

1. Use the same prompt for every model.
2. Generate one Solidity contract per prompt.
3. Run Stage 3 security analysis on every generated contract.
4. Record latency, validation result, and vulnerability counts.
5. Build a merged summary JSON for tables/plots.

## Output Files

* `llm_results.json` - raw per-contract results for all models
* `llm_comparison_summary.json` - aggregated summary
* `outputs/<model>/<contract_id>/generated.sol` - generated contract
* `outputs/<model>/<contract_id>/stage3_report.json` - security analysis report

## Metrics

### Security

* Critical vulnerabilities
* High vulnerabilities
* Medium vulnerabilities
* Low vulnerabilities
* Total findings

### Performance

* Average generation time
* Contracts per minute
* Validation pass count

## Notes

* Keep the code simple and runnable.
* Local models are called through Ollama.
* Grok requires a valid xAI API key.
* The pipeline path reuses `run_full_pipeline`.
* Direct LLM generation uses minimal provider wrappers, not a heavy framework.
