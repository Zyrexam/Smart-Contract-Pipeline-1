# Stage 3: Security Analysis & Auto-Fix - Complete Guide

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [File-by-File Explanation](#file-by-file-explanation)
4. [Execution Flow](#execution-flow)
5. [Common Issues](#common-issues)

---

## Overview

**Stage 3** is a security analysis pipeline that:

1. Runs security tools (Slither, Mythril, Semgrep, Solhint) in Docker containers
2. Parses their outputs to find vulnerabilities
3. Uses GPT-4o to automatically fix critical/high-severity issues
4. Re-analyzes until issues are resolved or max iterations reached

**Why Docker?** Security tools are Linux-based and don't work natively on Windows. Docker provides cross-platform compatibility.

**Inspired by SmartBugs**: Uses YAML configs, Docker execution, and unified parsers from the SmartBugs project.

---

## Architecture

```
stage_3/
├── __init__.py              # Public API (exports run_stage3)
├── models.py                # Data structures (SecurityIssue, AnalysisResult, etc.)
├── utils.py                 # Helper functions (file I/O, error detection)
├── tool_loader.py           # Loads YAML configs for tools
├── docker_executor.py       # Runs tools in Docker containers
├── analyzer.py              # Orchestrates tool execution and parsing
├── fixer.py                 # LLM-based vulnerability fixer
├── runner.py                # Main entry point (run_stage3 function)
├── parsers/                 # Output parsers for each tool
│   ├── __init__.py
│   ├── base.py              # Base parser class
│   ├── slither_parser.py    # Parses Slither JSON
│   ├── mythril_parser.py    # Parses Mythril JSON
│   ├── semgrep_parser.py    # Parses Semgrep JSON
│   └── solhint_parser.py    # Parses Solhint JSON
└── tools/                   # Tool configurations
    ├── slither/
    │   ├── config.yaml      # Docker image, entrypoint, output path
    │   └── scripts/
    │       └── do_solidity.sh  # Wrapper script to run Slither
    ├── mythril/
    │   ├── config.yaml
    │   └── scripts/do_solidity.sh
    ├── semgrep/
    │   ├── config.yaml
    │   └── scripts/do_solidity.sh
    └── solhint/
        ├── config.yaml
        └── scripts/do_solidity.sh
```

---

## File-by-File Explanation

### 1. `__init__.py` - Public API

**Purpose**: Defines what external code can import from Stage 3.

**Code**:

```python
from .runner import run_stage3
from .models import SecurityIssue, Severity, AnalysisResult, Stage3Result

__all__ = [
    "run_stage3",           # Main function to run Stage 3
    "SecurityIssue",        # Represents a single vulnerability
    "Severity",             # Enum: CRITICAL, HIGH, MEDIUM, LOW, INFO
    "AnalysisResult",       # Results from running security tools
    "Stage3Result",         # Complete Stage 3 results (with fixes)
]
```

**How it works**:

- When you do `from stage_3 import run_stage3`, Python looks at this file
- It imports `run_stage3` from `runner.py` and re-exports it
- This creates a clean public interface

**Usage**:

```python
from stage_3 import run_stage3, Severity

result = run_stage3(code, "MyContract")
critical_issues = [i for i in result.initial_analysis.issues if i.severity == Severity.CRITICAL]
```

---

### 2. `models.py` - Data Structures

**Purpose**: Defines all data classes used throughout Stage 3.

#### **Class 1: `Severity` (Enum)**

**What it is**: An enumeration of issue severity levels.

**Code**:

```python
class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"
```

**Key Method**: `from_string(s: str) -> Severity`

**How it works**:

```python
@classmethod
def from_string(cls, s: str) -> "Severity":
    s_upper = s.upper()
    # Try exact match first
    for sev in cls:
        if sev.value == s_upper:
            return sev

    # Fallback mapping for tool-specific strings
    if "critical" in s_upper or "high" in s_upper:
        return cls.HIGH
    elif "medium" in s_upper:
        return cls.MEDIUM
    elif "low" in s_upper:
        return cls.LOW
    else:
        return cls.INFO
```

**Example**:

```python
Severity.from_string("High")          # → Severity.HIGH
Severity.from_string("medium")        # → Severity.MEDIUM
Severity.from_string("informational") # → Severity.INFO
```

---

#### **Class 2: `SecurityIssue` (Dataclass)**

**What it is**: Represents a single security vulnerability found by a tool.

**Code**:

```python
@dataclass
class SecurityIssue:
    tool: str                      # Which tool found it (e.g., "slither")
    severity: Severity             # How serious it is
    title: str                     # Issue name (e.g., "reentrancy-eth")
    description: str               # Detailed explanation
    line: Optional[int] = None     # Starting line number
    line_end: Optional[int] = None # Ending line number
    filename: Optional[str] = None # Source file name
    contract: Optional[str] = None # Contract name
    function: Optional[str] = None # Function name
    recommendation: str = ""       # How to fix it
```

**Example**:

```python
issue = SecurityIssue(
    tool="slither",
    severity=Severity.HIGH,
    title="reentrancy-eth",
    description="Reentrancy in withdraw() allows attacker to drain funds",
    line=42,
    line_end=45,
    contract="VulnerableBank",
    function="withdraw",
    recommendation="Use ReentrancyGuard and checks-effects-interactions pattern"
)
```

**Method**: `to_dict() -> Dict`

- Converts to JSON-serializable dictionary
- Used for saving results to files

---

#### **Class 3: `AnalysisResult` (Dataclass)**

**What it is**: Results from running security tools on a contract.

**Code**:

```python
@dataclass
class AnalysisResult:
    contract_name: str              # Name of analyzed contract
    tools_used: List[str]           # Tools that ran successfully
    issues: List[SecurityIssue]     # All issues found
    success: bool                   # Whether analysis completed
    error: Optional[str] = None     # Error message if failed
    warnings: List[str] = None      # Non-fatal warnings
```

**Helper Methods**:

1. **`get_critical_high() -> List[SecurityIssue]`**

   ```python
   def get_critical_high(self):
       return [i for i in self.issues
               if i.severity in [Severity.CRITICAL, Severity.HIGH]]
   ```

   - Returns only CRITICAL and HIGH issues
   - Used by fixer to prioritize what to fix

2. **`get_by_severity(severity: Severity) -> List[SecurityIssue]`**
   ```python
   def get_by_severity(self, severity: Severity):
       return [i for i in self.issues if i.severity == severity]
   ```
   - Filters issues by severity level

**Example**:

```python
analysis = AnalysisResult(
    contract_name="MyToken",
    tools_used=["slither", "mythril"],
    issues=[issue1, issue2, issue3],
    success=True
)

critical = analysis.get_critical_high()  # [issue1]
medium = analysis.get_by_severity(Severity.MEDIUM)  # [issue2, issue3]
```

---

#### **Class 4: `Stage3Result` (Dataclass)**

**What it is**: Complete results from Stage 3 execution (analysis + fixes).

**Code**:

```python
@dataclass
class Stage3Result:
    original_code: str                      # Input Solidity code
    final_code: str                         # Fixed Solidity code
    iterations: int                         # Number of fix iterations
    initial_analysis: AnalysisResult        # First analysis results
    final_analysis: Optional[AnalysisResult] # Analysis after fixes
    fixes_applied: List[Dict]               # Details of each fix iteration
    issues_resolved: int                    # Count of resolved issues
    stage2_metadata: Optional[Dict] = None  # Context from Stage 2
    compiles: Optional[bool] = None         # Whether final code compiles
```

**Example**:

```python
result = Stage3Result(
    original_code="contract Vulnerable { ... }",
    final_code="contract Secure { ... }",
    iterations=2,
    initial_analysis=AnalysisResult(...),  # 15 issues
    final_analysis=AnalysisResult(...),    # 3 issues
    fixes_applied=[
        {"iteration": 1, "issues_before": 10, "issues_after": 5},
        {"iteration": 2, "issues_before": 5, "issues_after": 3}
    ],
    issues_resolved=12
)
```

---

### 3. `utils.py` - Utility Functions

**Purpose**: Helper functions for file operations and error detection.

#### **Function 1: `ensure_dir(path: str) -> str`**

**What it does**: Creates directory if it doesn't exist.

**Code**:

```python
def ensure_dir(path: str) -> str:
    Path(path).mkdir(parents=True, exist_ok=True)
    return str(Path(path))
```

**How it works**:

- `parents=True`: Creates parent directories too (like `mkdir -p`)
- `exist_ok=True`: Doesn't error if directory already exists
- Returns absolute path

**Example**:

```python
ensure_dir("/tmp/stage3/outputs")
# Creates: /tmp/stage3/outputs (and /tmp/stage3 if needed)
```

---

#### **Function 2: `read_json(path: str) -> dict`**

**Code**:

```python
def read_json(path: str) -> dict:
    with open(path, "r", encoding="utf8") as f:
        return json.load(f)
```

**Why UTF-8?** Handles special characters in contract names/descriptions.

---

#### **Function 3: `write_json(path: str, obj: dict) -> None`**

**Code**:

```python
def write_json(path: str, obj: dict) -> None:
    ensure_dir(Path(path).parent)  # Create directory first
    with open(path, "w", encoding="utf8") as f:
        json.dump(obj, f, indent=2)  # Pretty-print with 2-space indent
```

---

#### **Function 4: `errors_fails(exit_code, log, log_expected) -> Tuple[Set[str], Set[str]]`**

**What it does**: Extracts errors and failures from tool execution (SmartBugs-inspired).

**Code**:

```python
def errors_fails(exit_code: Optional[int], log: Optional[List[str]],
                 log_expected: bool = True) -> Tuple[Set[str], Set[str]]:
    errors = set()  # Errors detected and handled by the tool
    fails = set()   # Exceptions or failures

    # Check exit code
    if exit_code is None:
        fails.add("TIMEOUT")
    elif exit_code == 0:
        pass  # Success
    elif exit_code == 127:
        fails.add("COMMAND_NOT_FOUND")
    else:
        errors.add(f"EXIT_CODE_{exit_code}")

    # Parse log for errors
    if log:
        traceback_started = False
        for line in log:
            if "Traceback (most recent call last):" in line:
                traceback_started = True
            elif traceback_started and line.strip() and not line.startswith(" "):
                errors.add(f"exception ({line.strip()})")
                traceback_started = False
            elif any(pattern in line.lower() for pattern in ["error", "failed", "exception"]):
                if "error" in line.lower():
                    errors.add(f"error: {line.strip()[:100]}")

    elif log_expected and not fails:
        fails.add("execution failed")

    return errors, fails
```

**How it works**:

1. **Exit code analysis**:

   - `None` → Tool timed out
   - `0` → Success
   - `127` → Command not found (tool not installed)
   - Other → Some error occurred

2. **Log parsing**:
   - Detects Python tracebacks
   - Finds lines with "error", "failed", "exception"
   - Extracts error messages

**Example**:

```python
errors, fails = errors_fails(
    exit_code=1,
    log=["Running analysis...", "Error: File not found", "Traceback...", "ValueError: Invalid input"]
)
# errors = {"EXIT_CODE_1", "error: Error: File not found", "exception (ValueError: Invalid input)"}
# fails = set()
```

---

### 4. `tool_loader.py` - YAML Configuration Loader

**Purpose**: Loads tool configurations from YAML files (SmartBugs-style).

#### **Class: `ToolConfig`**

**What it is**: Represents a tool's configuration loaded from YAML.

**Code**:

```python
class ToolConfig:
    def __init__(self, tool_id: str, config: dict):
        self.id = tool_id                    # e.g., "slither"
        self.name = config.get("name", tool_id)  # e.g., "Slither"
        self.version = config.get("version", "")  # e.g., "0.11.3"
        self.image = config.get("image")     # Docker image name

        # bin can be at top level or inside solidity section
        self.bin = config.get("bin") or config.get("solidity", {}).get("bin")
        self.output = config.get("output")   # Output file path

        # Solidity mode config
        solidity = config.get("solidity", {})
        self.solidity_entrypoint = solidity.get("entrypoint")
        self.solidity_solc = solidity.get("solc", False)

        self.config = config  # Store full config
```

**Method**: `to_dict() -> dict`

```python
def to_dict(self):
    return {
        "id": self.id,
        "name": self.name,
        "image": self.image,
        "bin": self.bin,
        "output": self.output,
        "solidity": {
            "entrypoint": self.solidity_entrypoint,
            "solc": self.solidity_solc,
        }
    }
```

---

#### **Function: `load_tool(tool_id: str) -> Optional[ToolConfig]`**

**What it does**: Loads a tool's config from `stage_3/tools/<tool_id>/config.yaml`.

**Code**:

```python
def load_tool(tool_id: str) -> Optional[ToolConfig]:
    tools_dir = Path(__file__).parent / "tools"
    tool_dir = tools_dir / tool_id
    config_path = tool_dir / "config.yaml"

    if not config_path.exists():
        return None

    try:
        with open(config_path, "r", encoding="utf8") as f:
            config = yaml.safe_load(f)

        # Handle aliases (if tool references another)
        if "alias" in config:
            return load_tool(config["alias"])

        return ToolConfig(tool_id, config)

    except Exception as e:
        print(f"  ⚠️  Failed to load tool {tool_id}: {e}")
        return None
```

**Example YAML** (`tools/slither/config.yaml`):

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

**How it works**:

1. Constructs path: `stage_3/tools/slither/config.yaml`
2. Reads YAML file
3. Creates `ToolConfig` object with parsed values
4. Returns `None` if file not found or parsing fails

---

### 5. `docker_executor.py` - Docker Execution Engine

**Purpose**: Executes security tools in Docker containers.

#### **Class: `DockerExecutor`**

**Initialization**:

```python
def __init__(self, verbose: bool = False):
    self.verbose = verbose
    if not DOCKER_AVAILABLE:
        raise RuntimeError("Docker Python library not installed")

    try:
        self._client = docker.from_env()  # Connect to Docker daemon
        self._client.info()  # Test connection
    except Exception as e:
        raise RuntimeError(f"Docker not available: {e}")
```

**What happens**:

1. Checks if `docker` Python library is installed
2. Connects to Docker daemon (Docker Desktop must be running)
3. Tests connection with `info()` call
4. Raises error if Docker not available

---

#### **Method: `execute(solidity_code, tool_config, timeout)`**

**What it does**: Runs a security tool in a Docker container.

**Step-by-step breakdown**:

**Step 1: Create temporary directory**

```python
sbdir = tempfile.mkdtemp()  # e.g., /tmp/tmpXYZ123
```

- This directory will be mounted into the Docker container as `/sb`

**Step 2: Write contract file**

```python
contract_filename = "contract.sol"
contract_path = os.path.join(sbdir, contract_filename)
with open(contract_path, "w", encoding="utf8") as f:
    f.write(solidity_code)
```

- Creates `/tmp/tmpXYZ123/contract.sol` with the Solidity code

**Step 3: Copy tool scripts**

```python
bin_dest = os.path.join(sbdir, "bin")
tool_id = tool_config.get("id", "unknown")
script_dir_name = tool_config["bin"]  # "scripts"
current_file_dir = os.path.dirname(os.path.abspath(__file__))
bin_source = os.path.join(current_file_dir, "tools", tool_id, script_dir_name)

if os.path.exists(bin_source):
    shutil.copytree(bin_source, bin_dest)
    # Make scripts executable
    for root, dirs, files in os.walk(bin_dest):
        for file in files:
            os.chmod(os.path.join(root, file), 0o755)
```

- Copies `stage_3/tools/slither/scripts/` → `/tmp/tmpXYZ123/bin/`
- Makes scripts executable (chmod 755)

**Step 4: Ensure Docker image**

```python
def _ensure_image(self, image: str):
    images = self._client.images.list(image)
    if not images:
        print(f"  📦 Pulling Docker image: {image}")
        self._client.images.pull(image)
```

- Checks if image exists locally
- Pulls from Docker Hub if not found

**Step 5: Build command**

```python
def _build_command(self, tool_config, filename, timeout, bin_path):
    entrypoint_template = tool_config.get("solidity", {}).get("entrypoint", "")
    # Template: "'$BIN/do_solidity.sh' '$FILENAME' '$TIMEOUT' '$BIN'"

    command = entrypoint_template.replace("'$FILENAME'", f"'/sb/{filename}'")
    command = command.replace("'$TIMEOUT'", f"'{timeout}'")
    command = command.replace("'$BIN'", f"'{bin_path}'")

    # Result: "'/sb/bin/do_solidity.sh' '/sb/contract.sol' '120' '/sb/bin'"
    return command
```

**Step 6: Run Docker container**

```python
docker_args = {
    "image": "custom-slither:latest",
    "volumes": {sbdir: {"bind": "/sb", "mode": "rw"}},
    "command": ["/bin/sh", "-c", command],
    "detach": True,
    "user": "root",
    "working_dir": "/sb",
    "environment": {
        "SOLC_SELECT_DISABLED": "1",
        "MYTHRIL_DISABLE_SOLC_DOWNLOAD": "1",
        "SOLC_VERSION": "0.8.20",
    },
    "network_mode": "bridge",
}

container = self._client.containers.run(**docker_args)
```

**What this does**:

- Mounts `/tmp/tmpXYZ123` as `/sb` in container
- Runs command: `/bin/sh -c "'/sb/bin/do_solidity.sh' '/sb/contract.sol' '120' '/sb/bin'"`
- Sets environment variables to prevent auto-downloads
- Runs in background (`detach=True`)

**Step 7: Wait for completion**

```python
try:
    result = container.wait(timeout=timeout)
    exit_code = result["StatusCode"]
except requests.exceptions.ReadTimeout:
    container.stop(timeout=10)
    exit_code = None  # Timeout
```

**Step 8: Get logs**

```python
logs_bytes = container.logs()
logs = logs_bytes.decode("utf8", errors="replace").splitlines()
```

**Step 9: Extract output file**

```python
output_path = tool_config.get("output")  # "/output.json"
if output_path:
    try:
        tar_stream, stat = container.get_archive(output_path)
        output_chunks = []
        for chunk in tar_stream:
            output_chunks.append(chunk)
        output = b"".join(output_chunks)
    except docker.errors.NotFound:
        output = None
```

- Gets file from container as tar archive
- Returns raw bytes

**Step 10: Cleanup**

```python
finally:
    if container:
        container.kill()
        container.remove()
    shutil.rmtree(sbdir)
```

**Returns**: `(exit_code, logs, output_bytes)`

---

### 6. `analyzer.py` - Security Analyzer

**Purpose**: Orchestrates tool execution and result parsing.

#### **Class: `SecurityAnalyzer`**

**Parser Mapping**:

```python
PARSERS = {
    "slither": SlitherParser,
    "mythril": MythrilParser,
    "semgrep": SemgrepParser,
    "solhint": SolhintParser,
}
```

---

#### **Method: `analyze(solidity_code, contract_name, tools, timeout)`**

**Step 1: Load tool configs**

```python
tool_configs = load_tools(tools)  # Default: ["slither", "mythril", "semgrep", "solhint"]
```

**Step 2: Run each tool**

```python
for tool_config in tool_configs:
    tool_id = tool_config.id
    print(f"    • {tool_id}...", end=" ", flush=True)

    # Execute in Docker
    exit_code, logs, output = self.docker.execute(
        solidity_code,
        tool_config.to_dict(),
        timeout=timeout
    )
```

**Step 3: Extract output**

For **file-based tools** (Slither):

```python
if output and tool_config.output:
    # Extract JSON from tar archive
    output_content = self._extract_output_from_tar(output, tool_config.output)
    if output_content:
        parse_result = parser.parse(
            exit_code=exit_code,
            stdout=output_content,  # This is the JSON file content
            stderr=""
        )
```

For **stdout-based tools** (Mythril):

```python
else:
    # Use logs as stdout
    stdout = "\n".join(logs) if logs else ""
    parse_result = parser.parse(
        exit_code=exit_code,
        stdout=stdout,
        stderr=""
    )
```

**Step 4: Collect issues**

```python
if parse_result and not parse_result.fails:
    all_issues.extend(parse_result.issues)
    tools_succeeded.append(tool_id)
    print(f"✓ ({len(parse_result.issues)} issues)")
else:
    print(f"✗ (parsing failed)")
```

**Step 5: Return results**

```python
return AnalysisResult(
    contract_name=contract_name,
    tools_used=tools_succeeded,
    issues=all_issues,
    success=len(tools_succeeded) > 0
)
```

---

#### **Method: `_extract_output_from_tar(output: bytes, output_path: str)`**

**What it does**: Extracts a file from a tar archive.

**Code**:

```python
def _extract_output_from_tar(self, output: bytes, output_path: str):
    import tarfile, io

    try:
        with tarfile.open(fileobj=io.BytesIO(output)) as tar:
            clean_path = output_path.lstrip("/")  # "output.json"

            # Try multiple path variations
            paths_to_try = [
                clean_path,              # output.json
                f"/{clean_path}",        # /output.json
                clean_path.split("/")[-1], # Just filename
            ]

            for path in paths_to_try:
                try:
                    member = tar.getmember(path)
                    file_obj = tar.extractfile(member)
                    if file_obj:
                        content = file_obj.read().decode("utf8")
                        return content
                except KeyError:
                    continue

            return None
    except Exception as e:
        return None
```

**How it works**:

1. Opens tar archive from bytes
2. Tries to find file with different path variations
3. Extracts and decodes file content
4. Returns `None` if not found

---

### 7. `parsers/slither_parser.py` - Slither Output Parser

**Purpose**: Parses Slither JSON output into `SecurityIssue` objects.

#### **Expected JSON Structure**:

```json
{
  "success": false,
  "error": "...",
  "results": {
    "detectors": [
      {
        "check": "reentrancy-eth",
        "impact": "High",
        "confidence": "High",
        "description": "Reentrancy in withdraw()...",
        "elements": [...]
      }
    ]
  }
}
```

---

#### **Method: `parse(exit_code, stdout, stderr)`**

**Step 1: Parse JSON**

```python
output_dict = {}
if stdout.strip():
    try:
        output_dict = json.loads(stdout)
    except json.JSONDecodeError:
        # Try to find JSON in mixed output
        json_start = stdout.find('{')
        if json_start >= 0:
            # Find matching closing brace
            brace_count = 0
            for i in range(json_start, len(stdout)):
                if stdout[i] == '{':
                    brace_count += 1
                elif stdout[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        json_str = stdout[json_start:i+1]
                        output_dict = json.loads(json_str)
                        break
```

**Why this complexity?**

- Slither sometimes outputs text before/after JSON
- Need to extract just the JSON part

**Step 2: Extract detectors (CRITICAL)**

```python
results = output_dict.get("results", {})
detectors = results.get("detectors", [])

# Parse detectors FIRST, before checking success flag
for detector in detectors:
    issue = self._parse_detector(detector)
    if issue:
        issues.append(issue)
```

**Why parse detectors first?**

- Slither may set `success=false` even when detectors are found
- Previous bug: Ignored all detectors if `success=false`
- Fix: Parse detectors regardless of success flag

**Step 3: Check success flag**

```python
if not output_dict.get("success", False):
    error_msg = output_dict.get("error", "analysis unsuccessful")
    if len(detectors) > 0:
        # Slither found issues but marked success=false - this is OK
        infos.add("slither found detectors despite success=false")
    elif error_msg not in ["analysis unsuccessful", "Slither execution failed"]:
        # No detectors and a specific error message
        infos.add(f"slither reported: {error_msg}")
```

---

#### **Method: `_parse_detector(detector: dict)`**

**What it does**: Converts a Slither detector to a `SecurityIssue`.

**Code**:

```python
def _parse_detector(self, detector: dict):
    check = detector.get("check", "")          # "reentrancy-eth"
    impact = detector.get("impact", "Informational")  # "High"
    description = detector.get("description", "")
    elements = detector.get("elements", [])

    # Map impact to severity
    severity = self.IMPACT_TO_SEVERITY.get(impact, Severity.INFO)
    # {"High": Severity.HIGH, "Medium": Severity.MEDIUM, ...}

    # Extract location from elements
    line = None
    contract = None
    function = None

    for element in elements:
        if element.get("type") == "function":
            function = element.get("name")
            parent = element.get("type_specific_fields", {}).get("parent", {})
            if parent.get("type") == "contract":
                contract = parent.get("name")

        if "source_mapping" in element:
            source_mapping = element["source_mapping"]
            lines = sorted(source_mapping.get("lines", []))
            if lines:
                line = lines[0]
                line_end = lines[-1] if len(lines) > 1 else None

    # Get recommendation
    recommendation = self._get_recommendation(check, impact)

    return SecurityIssue(
        tool="slither",
        severity=severity,
        title=check,
        description=description,
        line=line,
        contract=contract,
        function=function,
        recommendation=recommendation
    )
```

**Recommendation mapping**:

```python
def _get_recommendation(self, check: str, impact: str):
    recommendations = {
        "reentrancy-eth": "Use ReentrancyGuard and checks-effects-interactions pattern",
        "unchecked-transfer": "Check return value or use SafeERC20",
        "tx-origin": "Replace tx.origin with msg.sender",
        "arbitrary-send-eth": "Add access control and input validation",
        "suicidal": "Add access control to selfdestruct",
    }
    return recommendations.get(check, "Review and apply security best practices")
```

---

### 8. `tools/slither/scripts/do_solidity.sh` - Slither Wrapper Script

**Purpose**: Runs Slither inside Docker container.

**Key Sections**:

#### **1. Environment Setup**

```bash
export SOLC_SELECT_DISABLED=1
export SLITHER_DISABLE_SOLC_DOWNLOAD=1
export PATH="/usr/local/bin:$PATH"
```

- Prevents `solc-select` from auto-downloading compilers
- Uses only pre-installed Solidity compiler

#### **2. Find Solidity Compiler**

```bash
if command -v solc > /dev/null 2>&1; then
    SOLC_PATH=$(command -v solc)
    export PATH="$(dirname "$SOLC_PATH"):$PATH"
else
    # Try common locations
    for path in /usr/bin/solc /usr/local/bin/solc /root/.solcx/bin/solc; do
        if [ -f "$path" ]; then
            export PATH="$(dirname "$path"):$PATH"
            break
        fi
    done
fi
```

#### **3. Run Slither (CRITICAL FIX)**

```bash
slither "$FILENAME" \
  --json /output.json \
  --solc-disable-warnings \
  --skip-clean \
  --filter-paths "node_modules" \
  > /dev/null 2>&1  # Silence stdout/stderr
```

**Why silence output?**

- Slither prints human-readable text to stdout
- Also writes JSON to `/output.json`
- We ONLY want the JSON file
- Previous bug: Mixed text+JSON caused parsing failures

#### **4. Validate Output**

```bash
if [ ! -f /output.json ] || [ ! -s /output.json ]; then
    # File missing or empty - create fallback
    echo '{"success":false,"error":"Slither execution failed","results":{"detectors":[]}}' > /output.json
elif ! python3 -c "import json; json.load(open('/output.json'))" 2>/dev/null; then
    # Invalid JSON - create fallback
    echo '{"success":false,"error":"Invalid JSON output","results":{"detectors":[]}}' > /output.json
fi
```

**CRITICAL**: Does NOT overwrite Slither's output if it exists and is valid JSON.

#### **5. Exit**

```bash
exit 0  # Always exit 0 to not block pipeline
```

- Errors are handled by parser, not exit code

---

### 9. `fixer.py` - LLM-Based Auto-Fixer

**Purpose**: Uses GPT-4o to fix security vulnerabilities.

#### **Method: `fix_issues(code, issues, contract_name, stage2_metadata, iteration)`**

**Step 1: Build metadata context**

```python
def _build_metadata_context(self, metadata):
    if not metadata:
        return ""

    context_parts = []
    if metadata.get("base_standard"):
        context_parts.append(f"Base Standard: {metadata['base_standard']}")
    if metadata.get("access_control"):
        context_parts.append(f"Access Control: {metadata['access_control']}")
    if metadata.get("inheritance_chain"):
        chain = " -> ".join(metadata["inheritance_chain"])
        context_parts.append(f"Inheritance: {chain}")

    return "\n".join(context_parts)
```

**Example output**:

```
Base Standard: ERC20
Access Control: OWNER
Inheritance: ERC20 -> Ownable
```

**Step 2: Format issues**

```python
def _format_issues(self, issues):
    lines = []
    for i, issue in enumerate(issues, 1):
        line_info = f"Line {issue.line}" if issue.line else "Unknown location"
        lines.append(
            f"{i}. [{issue.severity.value}] {issue.title}\n"
            f"   Tool: {issue.tool}\n"
            f"   Location: {line_info}\n"
            f"   Description: {issue.description}\n"
            f"   Recommendation: {issue.recommendation}\n"
        )
    return "\n".join(lines)
```

**Example output**:

```
1. [HIGH] reentrancy-eth
   Tool: slither
   Location: Line 42
   Description: Reentrancy in withdraw() allows attacker to drain funds
   Recommendation: Use ReentrancyGuard and checks-effects-interactions pattern

2. [MEDIUM] tx-origin
   Tool: slither
   Location: Line 58
   Description: Use of tx.origin for authorization
   Recommendation: Replace tx.origin with msg.sender
```

**Step 3: Build system prompt**

```python
def _build_system_prompt(self, metadata_context):
    base = """You are a Solidity security expert. Fix vulnerabilities while:
1. Preserving all functionality and public API
2. Maintaining OpenZeppelin v5 compatibility (^0.8.20)
3. Not introducing new bugs
4. Following the contract's existing architecture

COMMON FIXES:
- Reentrancy: Add ReentrancyGuard, use checks-effects-interactions
- Access Control: Add onlyOwner or AccessControl modifiers
- Unchecked Calls: Check return values, use SafeERC20
- Integer Issues: Use ^0.8.20 built-in checks
- tx.origin: Replace with msg.sender

Return ONLY the fixed Solidity code (no markdown, no explanations)."""

    if metadata_context:
        base += f"\n\nCONTRACT CONTEXT:\n{metadata_context}"

    return base
```

**Step 4: Build user prompt**

```python
def _build_user_prompt(self, code, issues_text, contract_name, metadata_context):
    prompt = f"Fix these security issues:\n\nCONTRACT: {contract_name}\n\n"
    if metadata_context:
        prompt += f"CONTEXT:\n{metadata_context}\n\n"
    prompt += f"CODE:\n{code}\n\nISSUES TO FIX:\n{issues_text}\n\n"
    prompt += "Fix all CRITICAL and HIGH issues. Return complete fixed contract."
    return prompt
```

**Step 5: Call GPT-4o**

```python
response = self.client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.1  # Low temperature for consistency
)

fixed_code = response.choices[0].message.content
```

**Step 6: Clean output**

````python
def _clean_code(self, code):
    code = code.strip()

    # Remove markdown code fences
    if code.startswith("```solidity"):
        code = code[11:].strip()
    elif code.startswith("```"):
        code = code[3:].strip()
    if code.endswith("```"):
        code = code[:-3].strip()

    # Add SPDX license if missing
    if "// SPDX-License-Identifier" not in code:
        code = "// SPDX-License-Identifier: MIT\n" + code

    # Add pragma if missing
    if "pragma solidity" not in code:
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if line.startswith("// SPDX"):
                lines.insert(i + 1, "pragma solidity ^0.8.20;")
                break
        code = '\n'.join(lines)

    return code
````

---

### 10. `runner.py` - Main Entry Point

**Purpose**: Orchestrates the entire Stage 3 workflow.

#### **Function: `run_stage3(...)`**

**Parameters**:

```python
def run_stage3(
    solidity_code: str,           # Input code from Stage 2
    contract_name: str,           # Contract name
    stage2_metadata: Optional[Dict] = None,  # Context from Stage 2
    max_iterations: int = 2,      # Max fix iterations
    tools: Optional[List[str]] = None,  # Tools to use
    skip_auto_fix: bool = False   # Analysis-only mode
) -> Stage3Result:
```

**Workflow**:

**Step 1: Initial Analysis**

```python
analyzer = SecurityAnalyzer(verbose=False)
initial_analysis = analyzer.analyze(solidity_code, contract_name, tools)

print(f"Found {len(initial_analysis.issues)} total issues:")
print(f"  • Critical: {len(initial_analysis.get_by_severity(Severity.CRITICAL))}")
print(f"  • High: {len(initial_analysis.get_by_severity(Severity.HIGH))}")
print(f"  • Medium: {len(initial_analysis.get_by_severity(Severity.MEDIUM))}")
print(f"  • Low: {len(initial_analysis.get_by_severity(Severity.LOW))}")
```

**Step 2: Iterative Fixing**

```python
fixer = SecurityFixer()
iteration = 0
current_code = solidity_code
current_analysis = initial_analysis

while iteration < max_iterations:
    # Get critical/high issues
    high_priority = current_analysis.get_critical_high()

    if not high_priority:
        print(f"✓ No critical/high issues after {iteration} iterations")
        break

    iteration += 1

    # Fix issues
    fixed_code = fixer.fix_issues(
        current_code,
        high_priority,
        contract_name,
        stage2_metadata,
        iteration
    )

    if fixed_code == current_code:
        print(f"⚠️ No changes in iteration {iteration}")
        break

    current_code = fixed_code

    # Re-analyze
    print(f"🔍 Re-analyzing...")
    current_analysis = analyzer.analyze(current_code, contract_name, tools)

    if not current_analysis.success:
        print(f"⚠️ Re-analysis failed")
        current_code = solidity_code  # Rollback
        break

    # Track fixes
    fixes_applied.append({
        "iteration": iteration,
        "issues_before": len(high_priority),
        "issues_after": len(current_analysis.get_critical_high())
    })

    print(f"✓ Iteration {iteration}: {len(current_analysis.issues)} issues remain")
```

**Step 3: Final Report**

```python
issues_resolved = len(initial_analysis.issues) - len(final_analysis.issues)

print(f"✅ Stage 3 Complete:")
print(f"  • Iterations: {iteration}")
print(f"  • Initial issues: {len(initial_analysis.issues)}")
print(f"  • Final issues: {len(final_analysis.issues)}")
print(f"  • Issues resolved: {issues_resolved}")

return Stage3Result(
    original_code=solidity_code,
    final_code=current_code,
    iterations=iteration,
    initial_analysis=initial_analysis,
    final_analysis=final_analysis,
    fixes_applied=fixes_applied,
    issues_resolved=issues_resolved,
    stage2_metadata=stage2_metadata
)
```

---

## Execution Flow

### Complete Example

**Input**:

```python
from stage_3 import run_stage3

vulnerable_code = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VulnerableBank {
    mapping(address => uint256) public balances;

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] -= amount;  // Reentrancy vulnerability!
    }
}
"""

result = run_stage3(
    solidity_code=vulnerable_code,
    contract_name="VulnerableBank",
    max_iterations=2,
    tools=["slither", "mythril"]
)
```

**Execution Flow**:

1. **runner.py** → `run_stage3()`
2. **analyzer.py** → `analyze()`
3. **tool_loader.py** → `load_tools(["slither", "mythril"])`
4. For Slither:
   - **docker_executor.py** → `execute()`
     - Creates `/tmp/tmpXYZ/contract.sol`
     - Copies `tools/slither/scripts/` → `/tmp/tmpXYZ/bin/`
     - Runs Docker: `custom-slither:latest`
     - Executes: `/sb/bin/do_solidity.sh /sb/contract.sol 120 /sb/bin`
   - **do_solidity.sh** runs inside container:
     - `slither /sb/contract.sol --json /output.json > /dev/null 2>&1`
     - Creates `/output.json` with results
   - **docker_executor.py** extracts `/output.json` as tar
   - **analyzer.py** → `_extract_output_from_tar()`
   - **slither_parser.py** → `parse()`
     - Parses JSON
     - Finds `detectors` array
     - Creates `SecurityIssue` objects
5. Repeat for Mythril
6. **analyzer.py** returns `AnalysisResult`:
   ```python
   AnalysisResult(
       contract_name="VulnerableBank",
       tools_used=["slither", "mythril"],
       issues=[
           SecurityIssue(
               tool="slither",
               severity=Severity.HIGH,
               title="reentrancy-eth",
               description="Reentrancy in withdraw()...",
               line=13,
               recommendation="Use ReentrancyGuard..."
           )
       ],
       success=True
   )
   ```
7. **runner.py** prints summary:
   ```
   Found 1 total issues:
     • Critical: 0
     • High: 1
     • Medium: 0
     • Low: 0
   ```
8. **fixer.py** → `fix_issues()`
   - Builds prompt with issue details
   - Calls GPT-4o
   - Returns fixed code:

     ```solidity
     import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

     contract SecureBank is ReentrancyGuard {
         mapping(address => uint256) public balances;

         function deposit() public payable {
             balances[msg.sender] += msg.value;
         }

         function withdraw(uint256 amount) public nonReentrant {
             require(balances[msg.sender] >= amount);
             balances[msg.sender] -= amount;  // Checks-effects-interactions
             (bool success, ) = msg.sender.call{value: amount}("");
             require(success);
         }
     }
     ```
9. **runner.py** re-analyzes fixed code
10. **analyzer.py** finds 0 issues
11. **runner.py** returns `Stage3Result`:
    ```python
    Stage3Result(
        original_code=vulnerable_code,
        final_code=fixed_code,
        iterations=1,
        initial_analysis=AnalysisResult(...),  # 1 issue
        final_analysis=AnalysisResult(...),    # 0 issues
        fixes_applied=[{"iteration": 1, "issues_before": 1, "issues_after": 0}],
        issues_resolved=1
    )
    ```

---

## Common Issues & Solutions

### Issue 1: "Docker not available"

**Cause**: Docker Desktop not installed or not running
**Solution**:

1. Install Docker Desktop for Windows
2. Start Docker Desktop
3. Verify: `docker ps` in terminal

### Issue 2: "0 issues found" (but contract is vulnerable)

**Cause**: Parser not extracting detectors correctly
**Solution**:

- Check `do_solidity.sh` doesn't overwrite output
- Ensure parser checks `detectors` before `success` flag
- Verify stdout is silenced (`> /dev/null 2>&1`)

### Issue 3: "JSON decode error"

**Cause**: Mixed text+JSON output
**Solution**:

- Silence tool stdout in wrapper script
- Use file-based output (`/output.json`)
- Extract from tar archive, not logs

### Issue 4: "Slither compilation failed"

**Cause**: Missing Solidity compiler
**Solution**:

- Use Docker images with pre-installed solc
- Set `SOLC_SELECT_DISABLED=1`
- Check `do_solidity.sh` finds solc

### Issue 5: "LLM fixes don't work"

**Cause**: No OpenAI API key
**Solution**:

- Add `OPENAI_API_KEY` to `.env` file
- Or set environment variable

---

## Summary

**Stage 3 Architecture**:

1. **Tool Configs** (YAML) → Define how to run tools
2. **Docker Executor** → Runs tools in containers
3. **Wrapper Scripts** → Execute tools inside containers
4. **Parsers** → Convert tool output to `SecurityIssue` objects
5. **Analyzer** → Orchestrates execution and parsing
6. **Fixer** → Uses LLM to fix vulnerabilities
7. **Runner** → Main workflow (analyze → fix → re-analyze)

**Key Design Decisions**:

- Docker for cross-platform compatibility
- SmartBugs-inspired architecture (YAML configs, unified parsers)
- Parse detectors before checking success flags
- Silence stdout, use file-based output
- LLM context from Stage 2 metadata
- Graceful error handling (partial results are valuable)

**Critical Fixes**:

1. Parse `detectors` array before checking `success` flag
2. Silence tool stdout to avoid mixed text+JSON
3. Don't overwrite valid output with fallback JSON
4. Extract output from tar archives, not logs
5. Disable solc auto-downloads to prevent network errors
