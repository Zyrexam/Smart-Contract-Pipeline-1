"""
Mythril Parser
==============

Adapted from SmartBugs tools/mythril-0.24.7/parser.py
Modified for direct CLI execution
"""

import json
from typing import List, Optional, Set

from ..models import SecurityIssue, Severity
from .base import Parser, ParseResult


class MythrilParser(Parser):
    """Parse Mythril JSON output"""
    
    # Severity mapping
    SEVERITY_MAP = {
        "High": Severity.HIGH,
        "Medium": Severity.MEDIUM,
        "Low": Severity.LOW,
        "Informational": Severity.INFO,
    }
    
    def __init__(self):
        super().__init__("mythril")
    
    def parse(
        self,
        exit_code: Optional[int],
        stdout: str,
        stderr: str
    ) -> ParseResult:
        """Parse Mythril JSON output"""
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
        
        # Mythril returns 1 when issues are found (not an error)
        if exit_code == 1:
            errors.discard("EXIT_CODE_1")
        
        # Check for exceptions in output
        for line in stdout_lines + stderr_lines:
            if "Exception occurred, aborting analysis." in line:
                infos.add("analysis incomplete")
                if not fails and not errors:
                    fails.add("execution failed")
        
        # Try to parse JSON (usually last line of stdout)
        result = None
        try:
            # Mythril outputs JSON as the last line
            if stdout_lines:
                last_line = stdout_lines[-1].strip()
                if last_line.startswith('{'):
                    result = json.loads(last_line)
        except json.JSONDecodeError:
            # Try parsing entire stdout
            try:
                result = json.loads(stdout)
            except json.JSONDecodeError:
                fails.add("error parsing JSON output")
        
        if result:
            error = result.get("error")
            if error:
                errors.add(error.split(".")[0])
            
            # Parse issues
            for issue in result.get("issues", []):
                security_issue = self._parse_issue(issue)
                if security_issue:
                    issues.append(security_issue)
        
        return ParseResult(
            issues=issues,
            errors=errors,
            fails=fails,
            infos=infos
        )
    
    def _parse_issue(self, issue: dict) -> Optional[SecurityIssue]:
        """Parse a single Mythril issue"""
        title = issue.get("title", "Mythril Finding")
        severity_str = issue.get("severity", "Informational")
        description = issue.get("description", "")
        swc_id = issue.get("swc-id")
        
        # Map severity
        severity = self.SEVERITY_MAP.get(severity_str, Severity.INFO)
        
        # Add SWC ID to title if present
        if swc_id:
            title = f"{title} (SWC {swc_id})"
            description += f"\nClassification: SWC-{swc_id}"
        
        # Extract location
        filename = issue.get("filename", "")
        line = issue.get("lineno")
        contract = issue.get("contract")
        function = issue.get("function")
        address = issue.get("address")
        
        # Workaround for utility.yul files
        if filename and filename.endswith("#utility.yul"):
            filename = None
            line = None
        
        # Build recommendation
        recommendation = self._get_recommendation(title, swc_id)
        
        return SecurityIssue(
            tool=self.tool_name,
            severity=severity,
            title=title,
            description=description,
            line=line,
            filename=filename if filename else None,
            contract=contract,
            function=function,
            recommendation=recommendation
        )
    
    def _get_recommendation(self, title: str, swc_id: Optional[str]) -> str:
        """Get fix recommendation based on SWC ID or title"""
        if swc_id:
            swc_recommendations = {
                "107": "Validate external call targets and use checks-effects-interactions",
                "104": "Check return values from external calls",
                "105": "Add access control to withdrawal functions",
                "106": "Add access control to selfdestruct",
                "112": "Validate delegatecall targets",
                "115": "Replace tx.origin with msg.sender",
                "116": "Avoid using block.timestamp for randomness",
                "120": "Avoid using block.number for randomness",
            }
            return swc_recommendations.get(swc_id, "Review SWC documentation")
        
        # Fallback to title-based recommendations
        title_lower = title.lower()
        if "reentrancy" in title_lower:
            return "Use ReentrancyGuard and checks-effects-interactions pattern"
        elif "unchecked" in title_lower:
            return "Check return values or use SafeERC20"
        elif "tx.origin" in title_lower or "tx-origin" in title_lower:
            return "Replace tx.origin with msg.sender"
        
        return "Review and apply security best practices"
