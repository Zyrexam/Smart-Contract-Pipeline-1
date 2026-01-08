# Using Vulnerable Contracts in ICBC Results

## Quick Start

Run Stage 3 on all vulnerable contracts:

```bash
python run_stage3_on_vulnerable_contracts.py
```

This will:
1. Process all `.sol` files in `vulnerable_dataset/`
2. Run Stage 3 analysis and auto-fix on each
3. Save results in `pipeline_outputs/` (same format as regular pipeline)
4. Results can be included in ICBC results generation

## Options

### Process all contracts:
```bash
python run_stage3_on_vulnerable_contracts.py
```

### Process a specific contract:
```bash
python run_stage3_on_vulnerable_contracts.py --contract BadLottery.sol
```

### Analysis only (no auto-fix):
```bash
python run_stage3_on_vulnerable_contracts.py --skip-auto-fix
```

### Custom output directory:
```bash
python run_stage3_on_vulnerable_contracts.py --output-dir my_results
```

### More fix iterations:
```bash
python run_stage3_on_vulnerable_contracts.py --max-iterations 3
```

## Including in ICBC Results

After running the script, the vulnerable contracts will be in `pipeline_outputs/` with the same structure as regular pipeline outputs:

```
pipeline_outputs/
  └── vulnerable_ReentrancyBank_2025-01-08_12-00-00/
      ├── ReentrancyBank.sol
      ├── final_ReentrancyBank.sol  (if fixes applied)
      ├── metadata.json
      └── stage3_report.json
```

Then run the results generator (it will automatically include these):

```bash
cd ICBC_Results_Work
python generate_icbc_results.py --input-dir ../pipeline_outputs
