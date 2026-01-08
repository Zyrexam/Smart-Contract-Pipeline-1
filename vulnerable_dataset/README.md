# 🚨 Vulnerable Smart Contracts Dataset for ICBC Results

This directory contains specifically crafted vulnerable contracts to test the security repair capabilities of the pipeline (Stage 3).

## Contracts Overview

| Contract                 | Vulnerability   | Severity   | SWC ID  | description                                                     |
| ------------------------ | --------------- | ---------- | ------- | --------------------------------------------------------------- |
| **ReentrancyBank.sol**   | Reentrancy      | High       | SWC-107 | Logic error allowing repeated withdrawals before balance update |
| **UnprotectedVault.sol** | access Control  | Critical   | SWC-105 | Missing `onlyOwner` modifier on sensitive function              |
| **PhishableWallet.sol**  | tx.origin Usage | Medium     | SWC-115 | Authentication using `tx.origin` susceptible to phishing        |
| **BadLottery.sol**       | Weak Randomness | Low/Medium | SWC-120 | Randomness dependent on predictable block variables             |

## Value for Research Paper

Running the pipeline on these contracts will demonstrate:

1.  **True Positive Detection:** Validating that Stage 3 tools (Slither, Mythril, etc.) correctly identify these issues.
2.  **Repair Effectiveness:** Proving that the LLM-based fixer can patch high-severity logic and access control bugs, not just gas optimizations.
3.  **Severity Handling:** Showing the system works across Critical, High, and Medium severity tiers.

## How to Run

Use the `run_stage3_on_existing_contracts.py` script (if available) or standard pipeline injection:

```bash
# Example command to run Stage 3 on this directory
python run_stage3_on_existing_contracts.py --input-dir vulnerable_dataset --output pipeline_outputs/vulnerable_test
```
