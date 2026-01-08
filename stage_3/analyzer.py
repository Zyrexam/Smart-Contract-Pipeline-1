"""
Security Analyzer
================

Orchestrates Docker-based tool execution and parsing
"""

from typing import List, Optional

from .docker_executor import DockerExecutor
from .models import AnalysisResult, SecurityIssue
from .parsers import (
    SlitherParser,
    MythrilParser,
    SemgrepParser,
    SolhintParser,
)
from .tool_loader import load_tools
from .utils import errors_fails


class SecurityAnalyzer:
    """Main security analyzer using Docker execution"""
    
    # Parser mapping
    PARSERS = {
        "slither": SlitherParser,
        "mythril": MythrilParser,
        "semgrep": SemgrepParser,
        "solhint": SolhintParser,
    }
    
    DEFAULT_TOOLS = ["slither", "mythril", "semgrep", "solhint"]
    
    def __init__(self, verbose: bool = False):
        """Initialize analyzer"""
        self.verbose = verbose
        try:
            self.docker = DockerExecutor(verbose=verbose)
        except RuntimeError as e:
            print(f"  ⚠️  Docker not available: {e}")
            self.docker = None
    
    def analyze(
        self,
        solidity_code: str,
        contract_name: str,
        tools: Optional[List[str]] = None,
        timeout: int = 120
    ) -> AnalysisResult:
        """
        Run security analysis on Solidity code using Docker
        
        Args:
            solidity_code: Solidity source code
            contract_name: Name of the contract
            tools: List of tools to use (default: DEFAULT_TOOLS)
            timeout: Timeout per tool in seconds
        
        Returns:
            AnalysisResult with all detected issues
        """
        if self.docker is None:
            return AnalysisResult(
                contract_name=contract_name,
                tools_used=[],
                issues=[],
                success=False,
                error="Docker not available. Install Docker and docker Python library."
            )
        
        if tools is None:
            tools = self.DEFAULT_TOOLS
        
        # Load tool configs
        tool_configs = load_tools(tools)
        
        if not tool_configs:
            return AnalysisResult(
                contract_name=contract_name,
                tools_used=[],
                issues=[],
                success=False,
                error="No tools available. Check tool configs in stage_3/tools/"
            )
        
        print(f"\n  🔍 Running: {', '.join([t.id for t in tool_configs])}")
        
        all_issues: List[SecurityIssue] = []
        tools_succeeded: List[str] = []
        all_warnings: List[str] = []
        
        # Run each tool
        for tool_config in tool_configs:
            tool_id = tool_config.id
            print(f"    • {tool_id}...", end=" ", flush=True)
            
            try:
                # Execute in Docker
                exit_code, logs, output = self.docker.execute(
                    solidity_code,
                    tool_config.to_dict(),
                    timeout=timeout
                )
                
                # Debug: Show last few log lines if verbose
                if self.verbose and logs:
                    last_logs = "\n".join(logs[-10:])
                    print(f"    [DEBUG] Exit code: {exit_code}")
                    print(f"    [DEBUG] Log lines: {len(logs)}")
                    print(f"    [DEBUG] Output size: {len(output) if output else 0} bytes")
                    print(f"    [DEBUG] Last 10 log lines:\n{last_logs}")
                
                # Parse output
                parser_class = self.PARSERS.get(tool_id)
                if not parser_class:
                    print(f"✗ (no parser)")
                    all_warnings.append(f"{tool_id}: no parser available")
                    continue
                
                parser = parser_class()
                
                # SmartBugs parsers expect: exit_code, log (list[str]), output (bytes)
                # Convert logs to list of strings
                log_lines = logs if logs else []
                
                # For tools that output to file (like Slither), use output bytes
                # For tools that output to stdout (like Mythril), use logs
                parse_result = None
                
                if output and tool_config.output:
                    # Tool writes to file (e.g., Slither -> /output.json)
                    # IMPORTANT: For file-based tools like Slither, we ONLY use the extracted JSON file
                    # We ignore stdout/stderr entirely to avoid mixing text output with JSON
                    # Output is a tar archive, extract it
                    output_content = self._extract_output_from_tar(output, tool_config.output)
                    if output_content:
                        if self.verbose:
                            print(f"    [DEBUG] Extracted output file, size: {len(output_content)} bytes")
                            print(f"    [DEBUG] Output preview: {output_content[:200]}")
                        # For file-based tools, ONLY pass the extracted JSON file content
                        # Do NOT pass logs/stdout as it may contain human-readable text
                        parse_result = parser.parse(
                            exit_code=exit_code,
                            stdout=output_content,  # This is the JSON file content, not stdout
                            stderr=""
                        )
                    else:
                        # Fallback to logs - check if JSON is in logs
                        # This should rarely happen if file extraction works correctly
                        if self.verbose:
                            print(f"    [DEBUG] Output file not found in tar, checking logs for JSON")
                            print(f"    [DEBUG] Log lines: {len(log_lines)}")
                            if log_lines:
                                print(f"    [DEBUG] First 5 log lines:")
                                for i, line in enumerate(log_lines[:5]):
                                    print(f"      [{i}] {line[:100]}")
                            # Look for JSON in logs
                            for line in log_lines:
                                if line.strip().startswith('{'):
                                    print(f"    [DEBUG] Found JSON-like line in logs: {line[:100]}")
                        # Combine all logs as stdout (fallback only)
                        stdout = "\n".join(log_lines) if log_lines else ""
                        parse_result = parser.parse(
                            exit_code=exit_code,
                            stdout=stdout,
                            stderr=""
                        )
                else:
                    # Tool outputs to stdout (e.g., Mythril, Semgrep)
                    stdout = "\n".join(log_lines) if log_lines else ""
                    if self.verbose:
                        print(f"    [DEBUG] Using stdout from logs, length: {len(stdout)}")
                        if stdout:
                            print(f"    [DEBUG] First 200 chars: {stdout[:200]}")
                    parse_result = parser.parse(
                        exit_code=exit_code,
                        stdout=stdout,
                        stderr=""
                    )
                
                if not parse_result:
                    print(f"✗ (parsing failed)")
                    all_warnings.append(f"{tool_id}: parsing failed")
                    # Graceful degradation: mark as partial success
                    tools_succeeded.append(f"{tool_id}-failed")
                    if self.verbose:
                        print(f"    [DEBUG] Parse result is None - parser returned nothing")
                        print(f"    [DEBUG] Exit code: {exit_code}")
                        print(f"    [DEBUG] Output size: {len(output) if output else 0} bytes")
                        print(f"    [DEBUG] Log lines: {len(logs)}")
                        if logs:
                            print(f"    [DEBUG] Last 5 log lines:")
                            for line in logs[-5:]:
                                print(f"      {line[:100]}")
                    continue
                
                if parse_result.fails:
                    fail_msg = list(parse_result.fails)[:1]
                    if self.verbose:
                        print(f"    [DEBUG] Parse fails: {fail_msg}")
                        print(f"    [DEBUG] All fails: {parse_result.fails}")
                        if output:
                            print(f"    [DEBUG] Output size: {len(output)} bytes")
                        if logs:
                            print(f"    [DEBUG] Log lines: {len(logs)}")
                            if len(logs) > 0:
                                print(f"    [DEBUG] Last log line: {logs[-1][:200]}")
                    print(f"⚠️  (partial: {fail_msg})")
                    all_warnings.append(f"{tool_id}: parsing issues - {fail_msg}")
                    # Still add any issues found, even with parse failures
                    if parse_result.issues:
                        all_issues.extend(parse_result.issues)
                        tools_succeeded.append(f"{tool_id}-partial")
                        print(f"    → Found {len(parse_result.issues)} issues despite errors")
                    else:
                        tools_succeeded.append(f"{tool_id}-failed")
                        if self.verbose:
                            print(f"    [DEBUG] No issues found despite parse result existing")
                            print(f"    [DEBUG] Errors: {parse_result.errors}")
                            print(f"    [DEBUG] Infos: {parse_result.infos}")
                    continue
                
                # Add issues
                all_issues.extend(parse_result.issues)
                tools_succeeded.append(tool_id)
                
                if len(parse_result.issues) > 0:
                    print(f"✓ ({len(parse_result.issues)} issues)")
                else:
                    print(f"✓ (0 issues)")
                    if self.verbose:
                        print(f"    [DEBUG] Tool completed but found no issues")
                        print(f"    [DEBUG] Errors: {parse_result.errors}")
                        print(f"    [DEBUG] Infos: {parse_result.infos}")
                        print(f"    [DEBUG] Exit code: {exit_code}")
            
            except Exception as e:
                error_msg = str(e)[:50]
                print(f"✗ ({error_msg})")
                all_warnings.append(f"{tool_id}: {str(e)}")
                # Mark as attempted but failed
                tools_succeeded.append(f"{tool_id}-error")
                if self.verbose:
                    import traceback
                    print(f"    [DEBUG] Exception: {traceback.format_exc()}")
                continue
        
        return AnalysisResult(
            contract_name=contract_name,
            tools_used=tools_succeeded,
            issues=all_issues,
            success=len(tools_succeeded) > 0,
            warnings=all_warnings if all_warnings else None
        )
    
    def _extract_output_from_tar(self, output: bytes, output_path: str) -> Optional[str]:
        """Extract output file from tar archive"""
        import tarfile
        import io
        
        try:
            with tarfile.open(fileobj=io.BytesIO(output)) as tar:
                # Remove leading slash from path
                clean_path = output_path.lstrip("/")
                
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
                            content = file_obj.read().decode("utf8", errors="replace")
                            if self.verbose:
                                print(f"    [DEBUG] Successfully extracted {path}, size: {len(content)} bytes")
                            return content
                    except KeyError:
                        continue
                
                # List available files for debugging
                available = tar.getnames()
                if self.verbose:
                    print(f"    [DEBUG] Available files in tar: {available}")
                    print(f"    [DEBUG] Looking for: {paths_to_try}")
                
                # Try to find any JSON file if exact match fails
                for member_name in available:
                    if member_name.endswith('.json') or 'output' in member_name.lower():
                        try:
                            member = tar.getmember(member_name)
                            file_obj = tar.extractfile(member)
                            if file_obj:
                                content = file_obj.read().decode("utf8", errors="replace")
                                if self.verbose:
                                    print(f"    [DEBUG] Found alternative JSON file: {member_name}")
                                return content
                        except Exception:
                            continue
                
                return None
        
        except Exception as e:
            if self.verbose:
                print(f"    [DEBUG] Tar extraction error: {e}")
                import traceback
                print(f"    [DEBUG] Traceback: {traceback.format_exc()}")
            return None

