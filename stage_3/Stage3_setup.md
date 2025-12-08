# Stage 3: Security Analysis Setup Guide

## Overview

Stage 3 uses **SmartBugs-style parsers** (extracted and adapted) to run 6 security analysis tools on generated smart contracts and automatically fixes detected vulnerabilities using GPT-4.

**No SmartBugs dependency required** - all parser logic is self-contained in `parsers/` directory.

---

## Quick Setup (2 Minutes)

```bash
# Install security tools (auto-installation also available)
pip install slither-analyzer mythril semgrep

# Optional: Install additional tools
npm install -g solhint  # For Solhint

# Set OpenAI API key
export OPENAI_API_KEY="your-api-key-here"
# Or create .env file with: OPENAI_API_KEY=your-api-key-here

# Run pipeline
python run_pipeline.py
```

**That's it!** Tools auto-install if missing.

---

## Tool Selection (6 Tools)

| Tool | Speed | Installation | What it Detects |
|------|-------|--------------|-----------------|
| **Slither** | 1-5s | `pip install slither-analyzer` | 90+ detectors: reentrancy, access control, best practices |
| **Mythril** | 1-2min | `pip install mythril` | Symbolic execution: integer overflows, reentrancy, unchecked calls |
| **Semgrep** | 2-5s | `pip install semgrep` | Pattern matching: code patterns, best practices |
| **Solhint** | 1-2s | `npm install -g solhint` | Linting + security rules |
| **Oyente** | 15-30s | Manual (see below) | Reentrancy, timestamp dependence, transaction ordering |
| **SmartCheck** | 2-5s | Manual (see below) | Common vulnerabilities, code smells |

**Default Tools:** `["slither", "mythril", "semgrep", "solhint", "oyente", "smartcheck"]`

---

## Installation Methods

### Method 1: Auto-Install (Recommended)

The pipeline automatically installs missing tools:

```python
from stage_3.security_integration import run_stage3

# Tools auto-install if missing
result = run_stage3(
    solidity_code=code,
    contract_name="MyContract",
    auto_install=True  # Default
)
```

### Method 2: Manual Installation

**Core Tools (Required):**
```bash
pip install slither-analyzer mythril semgrep
npm install -g solhint
```

**Optional Tools:**
- **Oyente**: Requires manual setup (see [Oyente GitHub](https://github.com/melonproject/oyente))
- **SmartCheck**: Requires manual setup (see [SmartCheck GitHub](https://github.com/smartdec/smartcheck))

**Verify Installation:**
```bash
slither --version
myth version
semgrep --version
solhint --version
```

---

## Solidity Compiler Setup

Most tools require `solc` (Solidity compiler):

```bash
# Install solc-select (recommended)
pip install solc-select

# Install and use Solidity 0.8.20
solc-select install 0.8.20
solc-select use 0.8.20

# Verify
solc --version
```

**Alternative (System-wide):**
```bash
# Ubuntu/Debian
sudo add-apt-repository ppa:ethereum/ethereum
sudo apt-get update
sudo apt-get install solc

# macOS
brew tap ethereum/ethereum
brew install solidity
```

---

## Usage

### Basic Usage

```python
from stage_3.security_integration import run_stage3

code = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract MyContract {
    mapping(address => uint256) public balances;
    
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount);
        (bool success,) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] -= amount;  // VULNERABLE: Reentrancy
    }
}
"""

result = run_stage3(
    solidity_code=code,
    contract_name="MyContract",
    max_iterations=2
)

print(f"Initial issues: {len(result.initial_analysis.issues)}")
print(f"Final issues: {len(result.final_analysis.issues)}")
print(f"Issues resolved: {result.issues_resolved}")
print(f"Fixed code:\n{result.final_code}")
```

### Custom Tool Selection

```python
# Use only fast tools
result = run_stage3(
    solidity_code=code,
    contract_name="Test",
    tools=["slither", "semgrep", "solhint"]  # ~5 seconds total
)

# Use all tools for thorough analysis
result = run_stage3(
    solidity_code=code,
    contract_name="Test",
    tools=["slither", "mythril", "semgrep", "solhint", "oyente", "smartcheck"]
)
```

### Pipeline Integration

```python
# In your main pipeline
from stage_2.code_generator import generate_code
from stage_3.security_integration import run_stage3

# Stage 2: Generate code
solidity_code = generate_code(spec, profile)

# Stage 3: Security analysis & auto-fix
security_result = run_stage3(
    solidity_code=solidity_code,
    contract_name=spec["contract_name"],
    max_iterations=2
)

# Use fixed code
final_code = security_result.final_code
```

---

## Output Format

### Stage3Result

```python
@dataclass
class Stage3Result:
    original_code: str              # Original code from Stage 2
    final_code: str                 # Fixed code after LLM iterations
    iterations: int                 # Number of fix iterations
    initial_analysis: AnalysisResult # Initial security scan results
    final_analysis: AnalysisResult   # Final security scan results
    fixes_applied: List[Dict]       # Fix history per iteration
    issues_resolved: int            # Total issues resolved
```

### AnalysisResult

```python
@dataclass
class AnalysisResult:
    contract_name: str
    tools_used: List[str]           # Tools that ran successfully
    issues: List[SecurityIssue]     # All detected issues
    success: bool
    error: Optional[str]
    
    def get_critical_high(self) -> List[SecurityIssue]:
        # Returns only CRITICAL and HIGH severity issues
```

### SecurityIssue

```python
@dataclass
class SecurityIssue:
    tool: str                        # Tool that found it
    severity: Severity               # CRITICAL, HIGH, MEDIUM, LOW, INFO
    title: str                       # Issue title/name
    description: str                 # Detailed description
    line: Optional[int]              # Line number
    recommendation: str              # Fix recommendation
```

---

## How It Works

### 1. Initial Analysis
- Runs all selected tools on the contract
- Parses output using SmartBugs-style parsers
- Collects all security issues

### 2. Iterative Fixing
- Filters CRITICAL and HIGH severity issues
- Sends to GPT-4 with fix instructions
- Re-analyzes fixed code
- Repeats until no critical/high issues remain or max iterations reached

### 3. Final Verification
- Runs final security scan
- Calculates issues resolved
- Returns complete results

---

## Parser Architecture

All parsers are in `stage_3/parsers/` directory:

```
parsers/
├── __init__.py              # Exports all parsers
├── parse_utils.py            # Shared utilities (extracted from SmartBugs)
├── slither_parser.py         # Slither parser (from SmartBugs)
├── mythril_parser.py         # Mythril parser (from SmartBugs)
├── semgrep_parser.py         # Semgrep parser (from SmartBugs)
├── solhint_parser.py         # Solhint parser (from SmartBugs)
├── oyente_parser.py          # Oyente parser (from SmartBugs)
└── smartcheck_parser.py      # SmartCheck parser (from SmartBugs)
```

**Each parser:**
- Extracted from SmartBugs repository
- Adapted for direct CLI execution (no Docker)
- Uses SmartBugs interface: `parse(exit_code, log, output)`
- Returns `List[SecurityIssue]`

---

## Configuration

### Environment Variables

Create `.env` file:
```bash
OPENAI_API_KEY=your-api-key-here
# OR
API_KEY=your-api-key-here
```

### Tool Timeouts

Default timeouts (can be adjusted in code):
- Slither: 60s
- Mythril: 120s
- Semgrep: 60s
- Solhint: 30s
- Oyente: 60s
- SmartCheck: 30s

---

## Troubleshooting

### Tool Not Found

```bash
# Check if tool is installed
slither --version

# Reinstall if needed
pip install --upgrade slither-analyzer
```

### Solidity Compiler Issues

```bash
# Check solc version
solc --version

# Install correct version
solc-select install 0.8.20
solc-select use 0.8.20
```

### OpenAI API Errors

```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Or check .env file
cat .env
```

### Parser Errors

If a parser fails, check:
1. Tool output format matches expected format
2. Tool version compatibility
3. Log files for error messages

---

## Example Output

```
================================================================================
STAGE 3: SECURITY ANALYSIS & AUTO-FIX (5 TOOLS)
================================================================================

[1/3] Initial security analysis

  🔍 Running: slither, mythril, semgrep, solhint
    • slither... ✓ (12 issues)
    • mythril... ✓ (5 issues)
    • semgrep... ✓ (3 issues)
    • solhint... ✓ (8 issues)

  Found 28 total issues:
    • Critical: 2
    • High: 8
    • Medium: 12
    • Low: 6

[2/3] Applying automatic fixes

  🔧 Iteration 1: Fixing 10 issues
  ✓ Fixes generated

  🔍 Re-analyzing...
    • slither... ✓ (5 issues)
    • mythril... ✓ (2 issues)
    • semgrep... ✓ (1 issues)
    • solhint... ✓ (3 issues)
  ✓ Iteration 1: 11 issues remain

  🔧 Iteration 2: Fixing 4 issues
  ✓ Fixes generated

  🔍 Re-analyzing...
    • slither... ✓ (2 issues)
    • mythril... ✓ (0 issues)
    • semgrep... ✓ (0 issues)
    • solhint... ✓ (1 issues)
  ✓ Iteration 2: 3 issues remain

[3/3] Final verification

✅ Stage 3 Complete:
  • Iterations: 2
  • Initial issues: 28
  • Final issues: 3
  • Issues resolved: 25
```

---

## Performance

**Typical Execution Times:**
- Fast tools only (slither, semgrep, solhint): 5-10 seconds
- All tools: 2-3 minutes
- With LLM fixes: +30-60 seconds per iteration

**Recommended:**
- Development: Use fast tools only
- Production: Use all tools for thorough analysis

---

## Next Steps

1. **Install tools**: `pip install slither-analyzer mythril semgrep`
2. **Set API key**: Add `OPENAI_API_KEY` to `.env`
3. **Test**: Run `python -m stage_3.security_integration` (test mode)
4. **Integrate**: Use in your pipeline
5. **Run**: Execute full pipeline

---

## Resources

- **Slither**: https://github.com/crytic/slither
- **Mythril**: https://github.com/ConsenSys/mythril
- **Semgrep**: https://semgrep.dev/
- **Solhint**: https://github.com/protofire/solhint
- **Oyente**: https://github.com/melonproject/oyente
- **SmartCheck**: https://github.com/smartdec/smartcheck
- **Solc-select**: https://github.com/crytic/solc-select

---

**Ready to use?**
```bash
pip install slither-analyzer mythril semgrep
python run_pipeline.py
```
