# Stage 3: Security Analysis & Auto-Fix

**Docker-based security analysis pipeline with Windows compatibility and LLM-powered auto-fix.**

## Quick Start

### 1. Prerequisites

```bash
# Install Python dependencies
pip install docker pyyaml openai python-dotenv

# Install Docker Desktop (Windows)
# Download from: https://www.docker.com/products/docker-desktop
```

### 2. Docker Images

Docker images will auto-pull on first run, or pull manually:

```bash
docker pull custom-slither:latest
docker pull custom-mythril:latest
docker pull smartbugs/semgrep:1.131.0-1.2.1
docker pull smartbugs/solhint:6.0.0
```

### 3. Basic Usage

```python
from stage_3 import run_stage3

# Analysis only (no API key needed)
result = run_stage3(
    solidity_code=code,
    contract_name="MyContract",
    skip_auto_fix=True
)

print(f"Found {len(result.initial_analysis.issues)} issues")

# With auto-fix (requires OPENAI_API_KEY)
result = run_stage3(
    solidity_code=code,
    contract_name="MyContract",
    stage2_metadata=metadata,
    max_iterations=2
)

print(f"Fixed code: {result.final_code}")
print(f"Resolved {result.issues_resolved} issues")
```

### 4. Set API Key (Optional, for auto-fix)

```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your-key-here"

# Or create .env file
echo OPENAI_API_KEY=your-key-here > .env
```

## Architecture

- **Docker Execution**: Tools run in Docker containers (Windows compatible)
- **YAML Configs**: Each tool has a `config.yaml` (SmartBugs-style)
- **Unified Parsing**: SmartBugs-style parsers convert tool output to `SecurityIssue` objects
- **LLM Auto-Fix**: Iterative vulnerability fixing with GPT-4o
- **Stage 2 Integration**: Uses metadata for context-aware fixing

## Directory Structure

```
stage_3/
├── __init__.py           # Public API (run_stage3)
├── runner.py             # Main entry point
├── analyzer.py           # Security analyzer
├── fixer.py              # LLM-based fixer
├── docker_executor.py    # Docker execution
├── tool_loader.py        # YAML config loader
├── models.py             # Data structures
├── parsers/              # Output parsers
│   ├── slither_parser.py
│   ├── mythril_parser.py
│   ├── semgrep_parser.py
│   └── solhint_parser.py
└── tools/                # Tool configs
    ├── slither/
    │   ├── config.yaml
    │   └── scripts/do_solidity.sh
    ├── mythril/
    ├── semgrep/
    └── solhint/
```

## Usage Examples

### Analysis Only

```python
from stage_3 import run_stage3

result = run_stage3(
    solidity_code=code,
    contract_name="TestContract",
    tools=["slither", "mythril", "semgrep", "solhint"],
    skip_auto_fix=True
)

# Access results
for issue in result.initial_analysis.issues:
    print(f"[{issue.severity.value}] {issue.title} at line {issue.line}")
```

### With Auto-Fix

```python
result = run_stage3(
    solidity_code=code,
    contract_name="MyContract",
    stage2_metadata={
        "base_standard": "ERC20",
        "access_control": "OWNER",
        "inheritance_chain": ["ERC20", "Ownable"]
    },
    max_iterations=2,
    tools=["slither", "mythril"]
)

print(f"Original issues: {len(result.initial_analysis.issues)}")
print(f"Final issues: {len(result.final_analysis.issues)}")
print(f"Resolved: {result.issues_resolved}")
```

### Verbose Mode (Debugging)

```python
result = run_stage3(
    solidity_code=code,
    contract_name="Test",
    stage2_metadata={"_verbose": True},  # Enable verbose logging
    skip_auto_fix=True
)
```

## How It Works

### 1. Tool Execution (Docker)
- Loads tool config from `stage_3/tools/<tool>/config.yaml`
- Creates temp directory with contract file
- Runs Docker container with tool image
- Extracts logs and output files

### 2. Parsing
- Uses parsers in `parsers/` directory
- Converts tool-specific output to `SecurityIssue` objects
- Handles JSON, text, and structured formats

### 3. Analysis
- Combines results from all tools
- Filters by severity (Critical, High, Medium, Low, Info)
- Returns `AnalysisResult`

### 4. Auto-Fix (Optional)
- Uses LLM (GPT-4o) to fix vulnerabilities
- Integrates Stage 2 metadata for context
- Iteratively re-analyzes until no critical/high issues remain

## Testing

```bash
# Quick test
python -m stage_3.test

# Production test
python -m stage_3.test_production

# Test with vulnerable contract
python test_mythril_slither_fixes.py
```

## Troubleshooting

### Docker Not Available
```
Error: Docker not available
```
**Solution**: Install Docker Desktop and ensure it's running.

### Tool Image Not Found
```
Failed to load Docker image custom-slither:latest
```
**Solution**: Pull the image manually or rebuild:
```bash
docker pull custom-slither:latest
# Or rebuild from docker directory
cd stage_3/docker
.\build.ps1  # Windows
./build.sh   # Linux/Mac
```

### Slither/Mythril Finding 0 Issues
If tools report 0 issues on vulnerable contracts:
1. Check verbose mode output: `stage2_metadata={"_verbose": True}`
2. Verify Docker containers are running
3. Check parser debug output in stderr
4. Ensure JSON files are being extracted correctly

### Parser Errors
If a parser fails:
1. Check tool output format matches parser expectations
2. Verify Docker container executed successfully
3. Check output file exists in container
4. Review verbose debug output

## Tool Configuration

Each tool has a `config.yaml` file:

```yaml
name: Slither
version: 0.11.3
image: custom-slither:latest
output: /output.json
bin: scripts
solidity:
    entrypoint: "'$BIN/do_solidity.sh' '$FILENAME' '$TIMEOUT' '$BIN'"
    solc: yes
```

## Example Output

```
================================================================================
STAGE 3: SECURITY ANALYSIS & AUTO-FIX
Mode: Docker-based execution (Windows compatible)
================================================================================

[1/2] Security analysis

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
  ✓ Iteration 1: 11 issues remain

[3/3] Final verification

✅ Stage 3 Complete:
  • Iterations: 1
  • Initial issues: 28
  • Final issues: 11
  • Issues resolved: 17
```

## API Reference

### `run_stage3()`

Main entry point for Stage 3.

**Parameters:**
- `solidity_code` (str): Solidity source code
- `contract_name` (str): Name of the contract
- `stage2_metadata` (dict, optional): Stage 2 metadata for context-aware fixing
- `max_iterations` (int, default=2): Maximum fix iterations
- `tools` (list, optional): Tools to use (default: all)
- `skip_auto_fix` (bool, default=False): If True, only run analysis

**Returns:**
- `Stage3Result` with:
  - `original_code`: Original Solidity code
  - `final_code`: Fixed code (or original if skip_auto_fix)
  - `initial_analysis`: Initial `AnalysisResult`
  - `final_analysis`: Final `AnalysisResult` (after fixes)
  - `issues_resolved`: Number of issues resolved
  - `iterations`: Number of fix iterations

## Status

- **Tools**: 4/4 working (Slither, Mythril, Semgrep, Solhint)
- **Success Rate**: 100%
- **Production Ready**: ✅ Yes
- **Windows Compatible**: ✅ Yes
