# Stage 3: Security Analysis & Auto-Fix

**SmartBugs-Lite**: A lightweight security analysis pipeline with Docker support for Windows compatibility.

## Architecture

This implementation uses **SmartBugs-inspired architecture** but rewritten for our pipeline:

- ✅ **YAML Configs**: Each tool has a `config.yaml` (like SmartBugs)
- ✅ **Docker Execution**: Tools run in Docker containers (Windows compatible)
- ✅ **Unified Parsing**: SmartBugs-style parsers (already in `parsers/`)
- ✅ **Stage 2 Integration**: Uses metadata for context-aware fixing
- ✅ **LLM Auto-Fix**: Iterative vulnerability fixing with GPT-4o

## Why Docker?

Some security tools don't work natively on Windows. Docker provides:
- **Cross-platform compatibility**: Works on Windows, Linux, macOS
- **Isolation**: Tools run in controlled environments
- **Consistency**: Same behavior across all platforms

## Installation

```bash
# Install Python dependencies
pip install docker pyyaml openai python-dotenv

# Install Docker Desktop (Windows)
# Download from: https://www.docker.com/products/docker-desktop

# Pull SmartBugs Docker images (automatic on first run)
# Or manually:
docker pull smartbugs/slither:0.11.3
docker pull smartbugs/mythril:0.24.7
docker pull smartbugs/semgrep:1.131.0-1.2.1
docker pull smartbugs/solhint:6.0.0

# Set OpenAI API key (for auto-fix)
export OPENAI_API_KEY="your-key"
# Or create .env file
```

## Structure

```
stage_3/
├── __init__.py           # Public API
├── models.py             # Data structures
├── utils.py              # Utilities
├── docker_executor.py    # Docker execution (SmartBugs-inspired)
├── tool_loader.py        # YAML config loader
├── analyzer.py           # Main analyzer
├── fixer.py              # LLM-based fixer
├── runner.py             # Main entry point
├── parsers/              # Output parsers (existing)
│   ├── slither_parser.py
│   ├── mythril_parser.py
│   ├── semgrep_parser.py
│   └── solhint_parser.py
└── tools/                # Tool configs (SmartBugs-style)
    ├── slither/
    │   ├── config.yaml
    │   └── scripts/do_solidity.sh
    ├── mythril/
    ├── semgrep/
    └── solhint/
```

## Usage

### Basic Usage

```python
from stage_3 import run_stage3

result = run_stage3(
    solidity_code=code,
    contract_name="MyContract",
    stage2_metadata={
        "base_standard": "ERC20",
        "access_control": "OWNER",
        "inheritance_chain": ["ERC20", "Ownable"]
    },
    max_iterations=2,
    tools=["slither", "mythril", "semgrep", "solhint"]
)

print(f"Fixed code: {result.final_code}")
print(f"Issues resolved: {result.issues_resolved}")
```

### Analysis Only

```python
result = run_stage3(
    solidity_code=code,
    contract_name="Test",
    skip_auto_fix=True  # Only detect issues
)
```

## How It Works

### 1. Tool Execution (Docker)

- Loads tool config from `stage_3/tools/<tool>/config.yaml`
- Creates temp directory with contract file
- Copies scripts/bin directory
- Runs Docker container with SmartBugs image
- Extracts logs and output files

### 2. Parsing

- Uses existing parsers in `parsers/` directory
- Converts tool-specific output to `SecurityIssue` objects
- Handles JSON, text, and structured formats

### 3. Analysis

- Combines results from all tools
- Filters by severity
- Returns `AnalysisResult`

### 4. Auto-Fix (Optional)

- Uses LLM (GPT-4o) to fix vulnerabilities
- Integrates Stage 2 metadata for context
- Iteratively re-analyzes until no critical/high issues remain

## Tool Configs

Each tool has a `config.yaml` file (SmartBugs format):

```yaml
name: Slither
version: 0.11.3
image: smartbugs/slither:0.11.3
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

## Differences from SmartBugs

| Feature | SmartBugs | Our Stage 3 |
|---------|-----------|-------------|
| **Architecture** | Standalone CLI | Integrated pipeline module |
| **Docker** | Required | Required (for Windows) |
| **Parsers** | 30+ tools | 4 tools we need |
| **Auto-Fix** | None | LLM-based iterative |
| **Stage 2 Integration** | None | Full metadata support |
| **Config** | YAML in tools/ | YAML in stage_3/tools/ |

## Troubleshooting

### Docker Not Available

```
Error: Docker not available
```

**Solution**: Install Docker Desktop and ensure it's running.

### Tool Image Not Found

```
Failed to load Docker image smartbugs/slither:0.11.3
```

**Solution**: Pull the image manually:
```bash
docker pull smartbugs/slither:0.11.3
```

### Parser Errors

If a parser fails, check:
1. Tool output format matches parser expectations
2. Docker container executed successfully
3. Output file exists in container

## Next Steps

1. **Install Docker**: Download Docker Desktop for Windows
2. **Pull Images**: Docker images will auto-pull on first run
3. **Set API Key**: Add `OPENAI_API_KEY` to `.env` for auto-fix
4. **Test**: Run on a sample contract
5. **Integrate**: Use in your pipeline after Stage 2

## Resources

- **SmartBugs**: https://github.com/smartbugs/smartbugs
- **Docker Images**: https://hub.docker.com/u/smartbugs
- **Docker Desktop**: https://www.docker.com/products/docker-desktop

