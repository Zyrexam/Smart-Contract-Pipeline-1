# Stage 3 Tools Guide - Complete Explanation

## 📁 Directory Structure

```
stage_3/tools/
├── slither/
│   ├── config.yaml          # Tool configuration (Docker image, command)
│   └── scripts/
│       └── do_solidity.sh   # Shell script that runs Slither in Docker
├── mythril/
│   ├── config.yaml
│   └── scripts/
│       └── do_solidity.sh
├── semgrep/
│   ├── config.yaml
│   └── scripts/
│       └── do_solidity.sh
└── solhint/
    ├── config.yaml
    └── scripts/
        └── do_solidity.sh
```

## 🔄 How It All Works Together

### Flow Diagram

```
1. analyzer.py calls tool_loader.py
   ↓
2. tool_loader.py reads config.yaml
   ↓
3. docker_executor.py uses config to:
   - Copy scripts/ to Docker container
   - Build command from entrypoint template
   - Run Docker container
   ↓
4. Docker container executes do_solidity.sh
   ↓
5. do_solidity.sh runs the actual tool (slither/mythril/etc)
   ↓
6. Tool output is captured (file or stdout)
   ↓
7. parser.py converts output to SecurityIssue objects
```

---

## 📄 File 1: `config.yaml` (Tool Configuration)

### What It Does
Defines how to run the tool: which Docker image, what command, where output goes.

### Location
Each tool has its own: `stage_3/tools/<tool>/config.yaml`

### Key Fields Explained

```yaml
name: Slither                    # Human-readable name
version: 0.11.3                  # Tool version
image: custom-slither:latest     # Docker image to use
output: /output.json             # Where tool writes output (optional)
bin: scripts                     # Directory with scripts to copy
solidity:
    entrypoint: "'$BIN/do_solidity.sh' '$FILENAME' '$TIMEOUT' '$BIN'"
    # Template command that gets executed in Docker
    # Variables: $FILENAME, $TIMEOUT, $BIN, $MAIN
    solc: yes                    # Tool needs Solidity compiler
```

### Example: Slither Config

```yaml
name: Slither
version: 0.11.3
image: custom-slither:latest
output: /output.json          # Slither writes JSON to this file
bin: scripts
solidity:
    entrypoint: "'$BIN/do_solidity.sh' '$FILENAME' '$TIMEOUT' '$BIN'"
    solc: yes
```

**What this means:**
- Use Docker image `custom-slither:latest`
- Copy `scripts/` directory to container
- Run: `/sb/bin/do_solidity.sh /sb/contract.sol 120 /sb/bin`
- Output will be in `/output.json` file

### Example: Mythril Config

```yaml
name: Mythril
image: custom-mythril:latest
bin: scripts
solidity:
    entrypoint: "'$BIN/do_solidity.sh' '$FILENAME' '$TIMEOUT' '$BIN' '$MAIN'"
    solc: yes
```

**What this means:**
- No `output:` field = tool writes to stdout (not a file)
- Mythril outputs JSON directly to stdout

### Who Reads This?
- **`tool_loader.py`** reads YAML and creates `ToolConfig` object
- **`docker_executor.py`** uses config to build Docker command

---

## 📄 File 2: `do_solidity.sh` (Execution Script)

### What It Does
Shell script that runs inside the Docker container. It:
1. Sets up environment (finds solc, disables downloads)
2. Runs the actual tool (slither/mythril/etc)
3. Handles errors gracefully
4. Ensures output is in correct format

### Location
`stage_3/tools/<tool>/scripts/do_solidity.sh`

### How It Gets Executed

1. **docker_executor.py** copies `scripts/` to `/sb/bin/` in container
2. **docker_executor.py** builds command from `entrypoint` template:
   ```
   '/sb/bin/do_solidity.sh' '/sb/contract.sol' '120' '/sb/bin'
   ```
3. Docker container runs this command
4. Script executes and produces output

---

## 🔍 Tool-Specific Scripts Explained

### 1. Slither Script (`slither/scripts/do_solidity.sh`)

**Purpose:** Run Slither and write JSON to `/output.json`

**Key Code Sections:**

```bash
# 1. Environment Setup (Lines 8-35)
# Prevents solc from trying to download (causes errors)
export SOLC_SELECT_DISABLED=1
export SLITHER_DISABLE_SOLC_DOWNLOAD=1

# Finds solc compiler in Docker image
if command -v solc >/dev/null 2>&1; then
    SOLC_PATH=$(command -v solc)
    export PATH="$(dirname "$SOLC_PATH"):$PATH"
fi

# 2. Run Slither (Lines 52-58)
slither "$FILENAME" \
  --json /output.json \        # Write JSON to file
  --solc-disable-warnings \
  --skip-clean \
  --filter-paths "node_modules" \
  > /dev/null 2>&1             # CRITICAL: Silence stdout (text output)

# 3. Validate Output (Lines 66-83)
# Check if /output.json exists and is valid JSON
# Only create fallback if file is missing or invalid
```

**Why `> /dev/null 2>&1`?**
- Slither prints human-readable text to stdout
- We ONLY want the JSON file, not the text
- This prevents mixing text with JSON parsing

**Output:** JSON file at `/output.json` with structure:
```json
{
  "success": true/false,
  "results": {
    "detectors": [
      {
        "check": "reentrancy-eth",
        "impact": "High",
        "description": "...",
        "elements": [...]
      }
    ]
  }
}
```

---

### 2. Mythril Script (`mythril/scripts/do_solidity.sh`)

**Purpose:** Run Mythril and output JSON to stdout

**Key Code Sections:**

```bash
# 1. Calculate Timeout (Lines 9-15)
# Use 80% of total timeout for execution
TO=$(( (TIMEOUT * 8 + 9) / 10 ))
OPT_TIMEOUT="--execution-timeout $TO"

# 2. Run Mythril (Lines 22-28)
OUTPUT=$(/usr/local/bin/myth analyze \
  $OPT_TIMEOUT \
  --max-depth 12 \
  --solver-timeout 10000 \
  -o json \                    # Output JSON format
  "$FILENAME" 2>&1)

# 3. Validate and Output (Lines 30-40)
# Check if output contains valid JSON
if echo "$OUTPUT" | grep -q '^{'; then
  echo "$OUTPUT"              # Valid JSON, output it
else
  echo '{"error":"...","issues":[]}'  # Fallback JSON
fi
```

**Why stdout instead of file?**
- Mythril outputs JSON directly to stdout
- No `output:` field in config.yaml
- Parser reads from stdout (logs)

**Output:** JSON to stdout with structure:
```json
{
  "issues": [
    {
      "title": "External Call",
      "severity": "High",
      "swc-id": "107",
      "description": "...",
      "lineno": 25
    }
  ]
}
```

---

### 3. Semgrep Script (`semgrep/scripts/do_solidity.sh`)

**Purpose:** Run Semgrep with custom rules and output JSON

**Key Code Sections:**

```bash
# 1. Create Rules File (Lines 9-48)
# Defines patterns to search for
RULES_FILE="/tmp/semgrep-rules-$$.yaml"
cat > "$RULES_FILE" <<'EOF'
rules:
  - id: tx-origin-usage
    pattern: tx.origin
    message: "Avoid using tx.origin..."
    severity: ERROR
  - id: reentrancy-pattern
    pattern: $X.call{value: $V}(...)
    message: "Potential reentrancy..."
  # ... more rules
EOF

# 2. Run Semgrep (Lines 51-56)
semgrep \
  --config "$RULES_FILE" \
  --timeout ${TIMEOUT:-120} \
  --json \                    # JSON output
  --disable-version-check \
  "$FILENAME" 2>&1
```

**Why custom rules?**
- Semgrep needs rules to know what to search for
- We define security patterns (reentrancy, tx.origin, etc.)
- Rules are created dynamically in the script

**Output:** JSON to stdout with Semgrep format

---

### 4. Solhint Script (`solhint/scripts/do_solidity.sh`)

**Purpose:** Run Solhint linter with security-focused config

**Key Code Sections:**

```bash
# 1. Create Config File (Lines 8-25)
# Security-focused rules, filters out noise
cat > /sb/.solhint.json <<'EOF'
{
  "extends": "solhint:recommended",
  "rules": {
    "avoid-tx-origin": "error",
    "check-send-result": "error",
    "avoid-low-level-calls": "warn",
    # ... more rules
  }
}
EOF

# 2. Run Solhint (Line 28)
cd /sb && solhint "$FILENAME" 2>&1
```

**Why custom config?**
- Default Solhint has too many warnings (noise)
- We focus on security-relevant rules
- Filters out style-only warnings

**Output:** Text to stdout (parsed by parser)

---

## 🔧 Supporting Files

### `tool_loader.py` - Loads Configs

**What it does:**
- Reads `config.yaml` files
- Creates `ToolConfig` objects
- Provides config to `docker_executor.py`

**Key Code:**

```python
def load_tool(tool_id: str) -> Optional[ToolConfig]:
    """Load tool configuration from YAML file"""
    tools_dir = Path(__file__).parent / "tools"
    tool_dir = tools_dir / tool_id
    config_path = tool_dir / "config.yaml"
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    return ToolConfig(tool_id, config)
```

**What `ToolConfig` contains:**
- `id`: "slither", "mythril", etc.
- `image`: Docker image name
- `output`: Output file path (if any)
- `bin`: Scripts directory
- `solidity_entrypoint`: Command template

---

### `docker_executor.py` - Executes Tools

**What it does:**
1. Creates temp directory with contract file
2. Copies `scripts/` to container
3. Builds command from `entrypoint` template
4. Runs Docker container
5. Extracts output (file or logs)

**Key Code Flow:**

```python
# 1. Write contract file
contract_path = os.path.join(sbdir, "contract.sol")
with open(contract_path, "w") as f:
    f.write(solidity_code)

# 2. Copy scripts directory
bin_source = os.path.join("stage_3", "tools", tool_id, "scripts")
shutil.copytree(bin_source, bin_dest)  # Copies to /sb/bin

# 3. Build command from template
# Template: "'$BIN/do_solidity.sh' '$FILENAME' '$TIMEOUT' '$BIN'"
# Becomes:  '/sb/bin/do_solidity.sh /sb/contract.sol 120 /sb/bin'
command = entrypoint_template.replace("'$FILENAME'", f"'/sb/{filename}'")
command = command.replace("'$TIMEOUT'", f"'{timeout}'")
command = command.replace("'$BIN'", f"'{bin_path}'")

# 4. Run Docker container
container = docker_client.containers.run(
    image=tool_config.image,
    volumes={sbdir: {"bind": "/sb", "mode": "rw"}},
    command=["/bin/sh", "-c", command],
    ...
)

# 5. Extract output
if tool_config.output:  # File-based (Slither)
    tar_stream, stat = container.get_archive(tool_config.output)
    output = b"".join(tar_stream)  # Tar archive with JSON file
else:  # Stdout-based (Mythril, Semgrep, Solhint)
    logs = container.logs().decode("utf8").splitlines()
```

---

## 📊 Output Handling

### File-Based Tools (Slither)

1. Script writes to `/output.json` in container
2. `docker_executor.py` extracts file as tar archive
3. `analyzer.py` extracts JSON from tar
4. Parser receives JSON string in `stdout` parameter

### Stdout-Based Tools (Mythril, Semgrep, Solhint)

1. Script outputs JSON/text to stdout
2. `docker_executor.py` captures logs (stdout)
3. `analyzer.py` passes logs to parser
4. Parser extracts JSON from stdout string

---

## 🎯 Summary: What Each File Does

| File | Purpose | Key Code |
|------|---------|----------|
| `config.yaml` | Tool configuration | Defines Docker image, command template, output location |
| `do_solidity.sh` | Execution script | Runs tool in Docker, handles errors, produces output |
| `tool_loader.py` | Config loader | Reads YAML, creates ToolConfig objects |
| `docker_executor.py` | Docker runner | Copies files, builds command, runs container, extracts output |

---

## 🔍 Quick Reference: Tool Differences

| Tool | Output Type | Output Location | Parser Reads From |
|------|------------|-----------------|-------------------|
| **Slither** | JSON file | `/output.json` | Extracted file content |
| **Mythril** | JSON stdout | stdout | Logs (stdout) |
| **Semgrep** | JSON stdout | stdout | Logs (stdout) |
| **Solhint** | Text stdout | stdout | Logs (stdout) |

---

## 🛠️ Adding a New Tool

1. **Create directory:**
   ```bash
   mkdir -p stage_3/tools/newtool/scripts
   ```

2. **Create `config.yaml`:**
   ```yaml
   name: NewTool
   image: newtool:latest
   output: /output.json  # or omit for stdout
   bin: scripts
   solidity:
       entrypoint: "'$BIN/do_solidity.sh' '$FILENAME' '$TIMEOUT' '$BIN'"
       solc: yes
   ```

3. **Create `scripts/do_solidity.sh`:**
   ```bash
   #!/bin/sh
   FILENAME="$1"
   TIMEOUT="$2"
   BIN="$3"
   
   # Run your tool
   newtool "$FILENAME" --json /output.json
   
   exit 0
   ```

4. **Create parser** in `stage_3/parsers/newtool_parser.py`

5. **Add to `PARSERS` dict** in `analyzer.py`

Done! The tool will be automatically loaded and executed.

---

## 💡 Key Takeaways

1. **`config.yaml`** = "What Docker image and command to use"
2. **`do_solidity.sh`** = "How to run the tool inside Docker"
3. **`tool_loader.py`** = "Reads configs and provides to executor"
4. **`docker_executor.py`** = "Actually runs tools in Docker containers"
5. **Output handling** = File-based (Slither) vs stdout-based (others)

The system is designed to be modular - each tool is self-contained in its directory with config and script.

