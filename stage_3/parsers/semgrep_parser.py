"""
Semgrep Parser
==============

Adapted from SmartBugs tools/semgrep-1.131.0-1.2.1/parser.py
Modified for direct CLI execution
"""

import json
import re
from typing import Iterator, List, Optional, Set

from ..models import SecurityIssue, Severity
from .base import Parser, ParseResult


class SemgrepParser(Parser):
    """Parse Semgrep JSON output"""
    
    # Severity mapping
    SEVERITY_MAP = {
        "ERROR": Severity.HIGH,
        "WARNING": Severity.MEDIUM,
        "INFO": Severity.INFO,
    }
    
    def __init__(self):
        super().__init__("semgrep")
    
    def parse(
        self,
        exit_code: Optional[int],
        stdout: str,
        stderr: str
    ) -> ParseResult:
        """Parse Semgrep JSON output"""
        issues: List[SecurityIssue] = []
        errors: Set[str] = set()
        fails: Set[str] = set()
        infos: Set[str] = set()
        
        stdout_lines = stdout.split('\n') if stdout else []
        stderr_lines = stderr.split('\n') if stderr else []
        
        # Extract errors and fails
        errs, fls = self._extract_errors_fails(exit_code, stdout_lines, stderr_lines)
        errors.update(errs)
        fails.update(fls)
        
        # Semgrep returns 1 when findings are found (not an error)
        if exit_code == 1:
            errors.discard("EXIT_CODE_1")
        
        # Try to parse JSON
        # Semgrep may output some text before JSON, so try to find JSON in the output
        result = {}
        if stdout.strip():
            # Try parsing entire stdout as JSON first
            try:
                result = json.loads(stdout)
            except json.JSONDecodeError:
                # Try to find JSON object in the output (look for { ... })
                json_start = stdout.find('{')
                json_end = stdout.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    try:
                        json_str = stdout[json_start:json_end]
                        result = json.loads(json_str)
                    except json.JSONDecodeError:
                        # Try line by line to find JSON
                        for line in stdout_lines:
                            line = line.strip()
                            if line.startswith('{') and line.endswith('}'):
                                try:
                                    result = json.loads(line)
                                    break
                                except json.JSONDecodeError:
                                    continue
                        if not result:
                            # If exit code is 0 and no findings, that's OK (empty result)
                            if exit_code == 0:
                                result = {"results": []}  # Empty results
                            else:
                                fails.add("error parsing JSON output")
                else:
                    # No JSON found, but exit code 0 means success (no findings)
                    if exit_code == 0:
                        result = {"results": []}  # Empty results
                    else:
                        fails.add("error parsing JSON output")
        
        # Parse results
        for result_item in result.get("results", []):
            issue = self._parse_result(result_item)
            if issue:
                issues.append(issue)
        
        return ParseResult(
            issues=issues,
            errors=errors,
            fails=fails,
            infos=infos
        )
    
    def _parse_result(self, result: dict) -> Optional[SecurityIssue]:
        """Parse a single Semgrep result"""
        check_id = result.get("check_id", "")
        message = result.get("message", "")
        severity_str = result.get("severity", "INFO")
        path = result.get("path", "")
        start = result.get("start", {})
        end = result.get("end", {})
        
        # Extract check name
        if "." in check_id:
            check_name = check_id.split(".")[-1]
        else:
            check_name = check_id
        
        # Map severity
        severity = self.SEVERITY_MAP.get(severity_str, Severity.INFO)
        
        # Extract line numbers
        line = start.get("line")
        line_end = end.get("line") if end.get("line") != line else None
        
        # Build recommendation
        recommendation = self._get_recommendation(check_name)
        
        return SecurityIssue(
            tool=self.tool_name,
            severity=severity,
            title=check_name,
            description=message or f"{check_name} detected",
            line=line,
            line_end=line_end,
            filename=path,
            recommendation=recommendation
        )
    
    def _get_recommendation(self, check_name: str) -> str:
        """Get fix recommendation based on check name"""
        name_lower = check_name.lower()
        
        if "reentrancy" in name_lower:
            return "Use ReentrancyGuard and checks-effects-interactions pattern"
        elif "unchecked" in name_lower:
            return "Check return values or use SafeERC20"
        elif "tx-origin" in name_lower or "txorigin" in name_lower:
            return "Replace tx.origin with msg.sender"
        elif "access-control" in name_lower:
            return "Add proper access control modifiers"
        elif "timestamp" in name_lower:
            return "Avoid using block.timestamp for critical logic"
        
        return "Review and apply security best practices"
