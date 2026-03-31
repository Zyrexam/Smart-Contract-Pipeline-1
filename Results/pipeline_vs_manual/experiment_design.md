# Result 04: Automated Pipeline vs Manual LLM Workflow

## 1. Objective

The goal of this experiment is to evaluate the benefits of the proposed automated smart contract pipeline compared to a manual LLM-assisted development workflow.

The comparison focuses on three aspects:

* development workflow complexity
* execution time
* security vulnerabilities in generated contracts

---

## 2. Systems Compared

### 2.1 Proposed Automated Pipeline

The proposed pipeline automatically processes the entire smart contract generation workflow.

Workflow:

User Query
→ Stage 1: Specification Generator
→ Stage 2: Smart Contract Generator
→ Stage 3: Security Analysis (SmartBugs)
→ Final Smart Contract

User interaction required: **1 step**

---

### 2.2 Manual LLM Workflow

In the manual workflow, a developer interacts with an LLM and external tools step-by-step.

Workflow:

User Query
→ LLM generates specification
→ LLM generates smart contract code
→ User runs SmartBugs manually
→ Vulnerabilities analyzed manually

User interaction required: **multiple steps**

---

## 3. Dataset (Input Prompts)

The following smart contract tasks will be used as input prompts.

1. NFT rental system
2. ERC20 token contract
3. Voting contract
4. Crowdfunding contract
5. Escrow contract
6. Multi-signature wallet
7. DAO governance contract
8. NFT marketplace
9. Time-lock contract
10. Auction contract

All prompts will be tested on both systems.

---

## 4. Evaluation Metrics

### 4.1 Workflow Efficiency

Metrics used to measure development efficiency:

* number of user interaction steps
* time required to obtain final contract

---

### 4.2 Security Analysis

Generated contracts will be analyzed using SmartBugs.

Metrics recorded:

* number of high severity vulnerabilities
* number of medium severity vulnerabilities
* number of low severity vulnerabilities

---

### 4.3 Code Characteristics

Additional contract characteristics:

* lines of code (LOC)
* number of functions
* compilation success

---

## 5. Experiment Procedure

For each prompt in the dataset:

1. Generate a contract using the manual LLM workflow.
2. Generate a contract using the automated pipeline.
3. Run SmartBugs security analysis on both contracts.
4. Record vulnerabilities and execution time.

For the basic working implementation in this folder:

* the automated pipeline is executed using the existing `run_pipeline.py` logic
* the manual baseline contract must be placed manually in `manual_contracts/<contract_id>.sol`
* Stage 3 is run in **analysis-only mode** for both systems to keep the comparison fair
* workflow steps are recorded as fixed values:
  * Pipeline = `1`
  * Manual LLM workflow = `3`

This keeps the experiment simple and avoids reusing pipeline stages inside the manual baseline.

---

## 6. Expected Result Tables

The experiment will produce the following result tables.

### Table 1 — Workflow Efficiency

| Method              | User Steps | Avg Time |
| ------------------- | ---------- | -------- |
| Manual LLM Workflow |            |          |
| Proposed Pipeline   |            |          |

---

### Table 2 — Vulnerability Comparison

| Contract | Manual Workflow | Pipeline |
| -------- | --------------- | -------- |

---

### Table 3 — Severity Distribution

| Severity | Manual Workflow | Pipeline |
| -------- | --------------- | -------- |
