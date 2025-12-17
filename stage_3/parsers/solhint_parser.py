import json
import re
from typing import List, Optional, Set

from ..models import SecurityIssue, Severity
from .base import Parser, ParseResult


class SolhintParser(Parser):
    """Parse Solhint output (multiple formats)"""
    
    SEVERITY_MAP = {
        "error": Severity.HIGH,
        "Error": Severity.HIGH,
        "warning": Severity.MEDIUM,
        "Warning": Severity.MEDIUM,
        "info": Severity.INFO,
        "Info": Severity.INFO,
    }
    
    # Format: /sb/contract.sol:96:5: Missing @notice tag [Warning/use-natspec]
    TEXT_PATTERN = re.compile(
        r"^(.+?):(\d+):(\d+):\s+(.+?)\s+\[(Error|Warning|Info)/(.+?)\]$"
    )
    
    # Unix format: file:line:column: severity message (rule)
    UNIX_PATTERN = re.compile(
        r"^(.+?):(\d+):(\d+):\s+(error|warning|info)\s+(.+?)\s+\((.+?)\)$"
    )
    
    # Solhint default format: "  line:column  severity  message  rule"
    # Example: "  11:9   warning  Provide an error message for require                 reason-string"
    SOLHINT_PATTERN = re.compile(
        r"^\s*(\d+):(\d+)\s+(error|warning|info)\s+(.+?)\s{2,}([\w-]+)\s*$"
    )
    
    def __init__(self):
        super().__init__("solhint")
    
    def parse(self, exit_code, stdout, stderr):
        issues = []
        errors = set()
        fails = set()
        infos = set()
        
        stdout_lines = stdout.split('\n') if stdout else []
        stderr_lines = stderr.split('\n') if stderr else []
        
        errs, fls = self._extract_errors_fails(exit_code, stdout_lines, stderr_lines)
        errors.update(errs)
        fails.update(fls)
        
        # Exit code 1 means issues found (not an error)
        if exit_code == 1:
            errors.discard("EXIT_CODE_1")
        
        # Try JSON format first
        try:
            result = json.loads(stdout)
            issues = self._parse_json_format(result)
            return ParseResult(issues=issues, errors=errors, fails=fails, infos=infos)
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Parse text/unix format
        for line in stdout_lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Skip header/footer lines
            if "problem" in line_stripped.lower() or "discord" in line_stripped.lower():
                continue
            if line_stripped.startswith("---") or line_stripped.startswith("==="):
                continue
            
            # Try SOLHINT_PATTERN first (most common format)
            match = self.SOLHINT_PATTERN.match(line)
            if match:
                line_num = int(match.group(1))
                col_num = int(match.group(2))
                severity_str = match.group(3)
                message = match.group(4).strip()
                rule = match.group(5).strip()
                
                severity = self.SEVERITY_MAP.get(severity_str, Severity.INFO)
                
                # Filter out documentation warnings if desired
                if "use-natspec" in rule.lower() or "natspec" in message.lower():
                    continue  # Skip natspec warnings entirely
                
                recommendation = self._get_recommendation(rule)
                
                issue = SecurityIssue(
                    tool=self.tool_name,
                    severity=severity,
                    title=rule,
                    description=message,
                    line=line_num,
                    filename="contract.sol",
                    recommendation=recommendation
                )
                issues.append(issue)
                continue
            
            # Try TEXT_PATTERN (with filename)
            match = self.TEXT_PATTERN.match(line_stripped)
            if match:
                filename = match.group(1)
                line_num = int(match.group(2))
                message = match.group(4)
                severity_str = match.group(5)
                rule = match.group(6)
                
                severity = self.SEVERITY_MAP.get(severity_str, Severity.INFO)
                
                # Filter out documentation warnings
                if "use-natspec" in rule.lower():
                    continue
                
                recommendation = self._get_recommendation(rule)
                
                issue = SecurityIssue(
                    tool=self.tool_name,
                    severity=severity,
                    title=rule,
                    description=message,
                    line=line_num,
                    filename=filename,
                    recommendation=recommendation
                )
                issues.append(issue)
                continue
            
            # Try UNIX_PATTERN as fallback
            match = self.UNIX_PATTERN.match(line_stripped)
            if match:
                filename = match.group(1)
                line_num = int(match.group(2))
                severity_str = match.group(4)
                message = match.group(5)
                rule = match.group(6)
                
                severity = self.SEVERITY_MAP.get(severity_str, Severity.INFO)
                recommendation = self._get_recommendation(rule)
                
                issue = SecurityIssue(
                    tool=self.tool_name,
                    severity=severity,
                    title=rule,
                    description=message,
                    line=line_num,
                    filename=filename,
                    recommendation=recommendation
                )
                issues.append(issue)
        
        return ParseResult(issues=issues, errors=errors, fails=fails, infos=infos)
    
    def _parse_json_format(self, result):
        """Parse Solhint JSON format"""
        issues = []
        
        for file_obj in result:
            filename = file_obj.get("filePath", "")
            
            for msg in file_obj.get("messages", []):
                line = msg.get("line")
                severity_num = msg.get("severity", 1)
                message = msg.get("message", "")
                rule_id = msg.get("ruleId", "unknown")
                
                severity_str = {1: "warning", 2: "error", 3: "info"}.get(severity_num, "info")
                severity = self.SEVERITY_MAP.get(severity_str, Severity.INFO)
                
                issue = SecurityIssue(
                    tool=self.tool_name,
                    severity=severity,
                    title=rule_id,
                    description=message,
                    line=line,
                    filename=filename,
                    recommendation=self._get_recommendation(rule_id)
                )
                issues.append(issue)
        
        return issues
    
    def _get_recommendation(self, rule: str) -> str:
        """Get fix recommendation"""
        rule_lower = rule.lower()
        
        recommendations = {
            "use-natspec": "Add NatSpec documentation (@notice, @param, @return)",
            "no-console": "Remove console.log statements",
            "no-empty-blocks": "Add logic to empty blocks or remove them",
            "no-unused-vars": "Remove unused variables",
            "avoid-tx-origin": "Replace tx.origin with msg.sender",
            "check-send-result": "Check return value from send()",
            "avoid-call-value": "Use call{value: x}() instead of call.value()",
            "avoid-low-level-calls": "Avoid low-level calls or check return values",
            "state-visibility": "Specify visibility for state variables",
            "func-visibility": "Specify visibility for functions",
        }
        
        for key, rec in recommendations.items():
            if key in rule_lower:
                return rec
        
        return "Follow Solidity style guide"