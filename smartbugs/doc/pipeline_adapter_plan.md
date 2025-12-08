# Pipeline Adapter Plan for SmartBugs Tool Integrations

## Purpose

Provide an actionable, copy-paste-ready plan an LLM can follow to implement a small Python adapter and runner that reuses SmartBugs' `tools/*` integrations (config and parsers) for use in another pipeline.

## Goal

Implement a minimal, modular adapter that:
- loads tool metadata from `tools/*/config.yaml`,
- executes the tool (Docker or local) on a given contract file,
- captures stdout/stderr and any output artifact (e.g., `result.json`, `result.tar`),
- calls the existing `tools/{tool_id}/parser.py` to normalize results,
- returns or writes standardized JSON with findings and metadata.

## Environment & Assumptions

- Python 3.9+.
- Docker daemon available for tools that require containers (fallback to local execution allowed).
- Repository root is accessible; `tools/` and `samples/` exist as in SmartBugs.
- Parsers in `tools/*/parser.py` conform to the SmartBugs interface: `parse(exit_code, tool_log:list[str], tool_output:bytes) -> dict`.
- Use `string.Template` semantics for command templates (same as SmartBugs).

## Deliverables (files to create)

- `pipeline_adapter/loader.py` — ToolLoader: read `tools/*/config.yaml` and expose Tool metadata and command rendering.
- `pipeline_adapter/executor.py` — Executor: run a tool (Docker preferred), capture `exit_code`, `log_lines`, `output_bytes`.
- `pipeline_adapter/parser_adapter.py` — ParserAdapter: import and call `tools.{tool_id}.parser.parse(...)` and wrap results.
- `pipeline_adapter/cli.py` — Minimal CLI to run one tool on one contract and print JSON results.
- `pipeline_adapter/tests/test_runner.py` — Minimal tests using `samples/` or mocks.
- `doc/pipeline_adapter_plan.md` — (this file) reference for the LLM.

## Key Component Specs

### 1) ToolLoader (`pipeline_adapter/loader.py`)

**Responsibilities:**
- Enumerate `tools/*` directories and load `config.yaml` for each tool.
- Provide a `Tool` dataclass with fields: `id`, `mode`, `image`, `command_template`, `entrypoint_template`, `solc` (bool), `cpu_quota`, `mem_limit`, `absbin`.
- Render command/entrypoint using `string.Template` with parameters `(filename, timeout, bin_dir, main_flag)` to match SmartBugs behavior.

**API:**
- `load_tools() -> list[Tool]`
- `get_tool(tool_id: str) -> Tool`
- `render_command(tool: Tool, filename: str, timeout: int, bin_dir: str, main: bool) -> tuple[str, str]`

### 2) Executor (`pipeline_adapter/executor.py`)

**Responsibilities:**
- Given a `Tool` and an input file, prepare a temporary `/sb` folder like SmartBugs does (copy `.sol` or write `.hex`).
- If `tool.image` is set: run via Docker (prefer `docker` Python SDK; fallback to `subprocess docker run`).
- Mount the temp folder into container path `/sb` and set command/entrypoint according to rendered templates.
- Enforce `timeout` and resource limits (`cpu_quota`, `mem_limit`) where feasible.
- Capture stdout+stderr, produce `log_lines: list[str]`.
- Collect preferred outputs from `/sb`: `result.json`, `result.tar`, `result.sarif` (in that order) and return bytes for the first found.

**API:**
- `run_tool(tool: Tool, filename: str, timeout: int) -> tuple[int, list[str], bytes|None]`

### 3) ParserAdapter (`pipeline_adapter/parser_adapter.py`)

**Responsibilities:**
- Dynamically import `tools.{tool_id}.parser` using `importlib`.
- Call `parse(exit_code, log_lines, output_bytes)` and validate the return keys.
- Wrap parser results in a stable JSON with task metadata, docker info, and platform info (optional from `sb/cfg.py`).

**API:**
- `parse_results(tool_id: str, filename: str, exit_code: int, log_lines: list[str], output_bytes: bytes|None) -> dict`

### 4) CLI (`pipeline_adapter/cli.py`)

Simple CLI to run a single tool on a file:
- Options: `--tool TOOL_ID`, `--file PATH`, `--timeout N`, `--output FILE`.
- Calls Loader -> Executor -> ParserAdapter and prints resulting JSON to stdout or writes it to `--output`.

## Testing

**Unit tests for:**
- `ToolLoader` parsing of a sample `tools/*/config.yaml`.
- `ParserAdapter` with a real parser module (one of the simple parsers in `tools/*`) using a mocked `exit_code` and `log_lines`.
- `Executor` can be tested with a no-docker tool or by mocking Docker (use `pytest-mock` or `unittest.mock`).

**Integration test:**
- Run the CLI for one tool and one `samples/` contract (or a trivial `.sol`) and assert the JSON contains `result.parser` and `findings` keys.

## Acceptance Criteria

- Given `--tool <tool-id>` and `--file <path>`, CLI returns JSON with:
  - `task`: filename/tool/mode/exit_code/duration
  - `result`: parser output containing `findings` (list), `infos`, `errors`, `fails`, and `parser` metadata
  - `docker`: image and runtime args when used

- Parsers from `tools/*/parser.py` are invoked directly; parsing logic is not reimplemented.

## Example LLM Prompt (copy-paste)

```
Write Python code that implements a `ToolLoader` reading `tools/*/config.yaml`, 
an `Executor` that runs a tool in Docker (mounted at `/sb`), and a `ParserAdapter` 
that loads `tools.{tool_id}.parser` and calls its `parse` function. Provide a small 
CLI `pipeline_adapter/cli.py` to run a single task and print normalized JSON. Use 
`string.Template` for command templating and prefer Docker SDK but allow `subprocess` 
fallback. Add minimal tests using `samples/SimpleDAO.sol`. Keep code modular and 
add a README with run steps.
```

## Quick Run & Test Commands

```bash
# Run a tool (example)
python -m pipeline_adapter.cli --tool slither-0.11.3 --file samples/SimpleDAO.sol --timeout 600

# Run tests
pytest pipeline_adapter/tests/test_runner.py -q
```

## Notes for the implementing LLM

- Inspect `sb/parsing.py` to see exactly how SmartBugs loads/parses parser modules.
- Inspect `sb/docker.py` for how SmartBugs prepares folders and builds Docker args (use it as a reference).
- Parsers expect `log` as `list[str]` (not one long string) and `output` as `bytes` or `None`.
- Use minimal external dependencies: `PyYAML`, optionally `docker` Python SDK.

## Next steps you can ask me to do

- Generate the Python skeleton files described above in `pipeline_adapter/`.
- Produce a refined, ready-to-run prompt for an external LLM (e.g., GPT) including file templates and tests.
- Create the minimal test and run it locally (requires Docker).
