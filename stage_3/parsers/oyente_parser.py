"""
Oyente Parser
=============

Adapted from SmartBugs tools/oyente/parser.py
Modified for direct CLI execution
"""

import re
from typing import List, Optional, Set

from ..models import SecurityIssue, Severity
from .base import Parser, ParseResult


class OyenteParser(Parser):
    """Parse Oyente output"""
    
    # Vulnerability patterns
    VULN_PATTERNS = {
        "Reentrancy": ("reentrancy", Severity.HIGH),
        "Timestamp Dependency": ("timestamp-dependency", Severity.MEDIUM),
        "Transaction Ordering": ("transaction-ordering", Severity.MEDIUM),
        "Integer Overflow": ("integer-overflow", Severity.HIGH),
        "Integer Underflow": ("integer-underflow", Severity.HIGH),
        "Callstack Depth": ("callstack-depth", Severity.LOW),
        "Parity Multisig Bug": ("parity-multisig", Severity.HIGH),
    }
    
    def __init__(self):
        super().__init__("oyente")
    
    def parse(
        self,
        exit_code: Optional[int],
        stdout: str,
        stderr: str
    ) -> ParseResult:
        """Parse Oyente output"""
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
        
        # Parse vulnerabilities from output
        current_vuln = None
        for line in stdout_lines:
            line = line.strip()
            
            # Check for vulnerability patterns
            for vuln_name, (vuln_id, severity) in self.VULN_PATTERNS.items():
                if vuln_name.lower() in line.lower() or vuln_id in line.lower():
                    # Extract line number if present
                    line_match = re.search(r'line\s+(\d+)', line, re.IGNORECASE)
                    line_num = int(line_match.group(1)) if line_match else None
                    
                    issue = SecurityIssue(
                        tool=self.tool_name,
                        severity=severity,
                        title=vuln_name,
                        description=line,
                        line=line_num,
                        recommendation=self._get_recommendation(vuln_id)
                    )
                    issues.append(issue)
                    break
        
        return ParseResult(
            issues=issues,
            errors=errors,
            fails=fails,
            infos=infos
        )
    
    def _get_recommendation(self, vuln_id: str) -> str:
        """Get fix recommendation based on vulnerability ID"""
        recommendations = {
            "reentrancy": "Use ReentrancyGuard and checks-effects-interactions pattern",
            "timestamp-dependency": "Avoid using block.timestamp for critical logic",
            "transaction-ordering": "Use commit-reveal scheme or other mitigation",
            "integer-overflow": "Use SafeMath or Solidity 0.8+ built-in checks",
            "integer-underflow": "Use SafeMath or Solidity 0.8+ built-in checks",
            "callstack-depth": "Limit call depth or use alternative patterns",
            "parity-multisig": "Review multisig implementation carefully",
        }
        
        return recommendations.get(vuln_id, "Review and apply security best practices")
