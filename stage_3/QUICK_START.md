# Stage 3 Quick Start Guide

## ✅ Step 1: Verify Docker Images

You've already pulled the images! Verify they're available:

```bash
docker images | grep smartbugs
```

You should see:
- `smartbugs/slither:0.11.3`
- `smartbugs/mythril:0.24.7`
- `smartbugs/semgrep:1.131.0-1.2.1`
- `smartbugs/solhint:6.0.0`

## ✅ Step 2: Test Stage 3 Standalone

Test Stage 3 with a sample contract:

```bash
python stage_3/test_stage3.py
```

This will:
1. Run analysis only (no API key needed)
2. Optionally test auto-fix (requires `OPENAI_API_KEY`)

## ✅ Step 3: Integrate with Full Pipeline

Update your pipeline to include Stage 3. See `pipeline_with_stage3.py` below.

## ✅ Step 4: Set OpenAI API Key (Optional)

For auto-fix functionality, set your API key:

```bash
# Windows PowerShell
$env:OPENAI_API_KEY="your-key-here"

# Or create .env file
echo OPENAI_API_KEY=your-key-here > .env
```

## Usage Examples

### Example 1: Analysis Only

```python
from stage_3 import run_stage3

result = run_stage3(
    solidity_code=code,
    contract_name="MyContract",
    skip_auto_fix=True  # No API key needed
)

print(f"Found {len(result.initial_analysis.issues)} issues")
```

### Example 2: With Auto-Fix

```python
from stage_3 import run_stage3

result = run_stage3(
    solidity_code=code,
    contract_name="MyContract",
    stage2_metadata=metadata,
    max_iterations=2
)

print(f"Fixed code: {result.final_code}")
print(f"Resolved {result.issues_resolved} issues")
```

## Troubleshooting

### Docker Not Running
```
Error: Docker not available
```
**Fix**: Start Docker Desktop

### Image Not Found
```
Failed to load Docker image smartbugs/slither:0.11.3
```
**Fix**: Pull manually: `docker pull smartbugs/slither:0.11.3`

### Tool Execution Fails
Check Docker Desktop logs and ensure containers can start.

