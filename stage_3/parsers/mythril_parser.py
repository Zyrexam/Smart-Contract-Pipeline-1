"""
Mythril Parser - Extracted from SmartBugs tools/mythril-0.24.7/parser.py
Adapted for direct CLI execution (no Docker dependency)
"""

import json
from typing import List

# Import our data structures
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from security_integration import SecurityIssue, Severity
else:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from security_integration import SecurityIssue, Severity

from .parse_utils import errors_fails

VERSION = "2025/08/29"

# All possible Mythril findings (from SmartBugs)
FINDINGS = {
    "Jump to an arbitrary instruction (SWC 127)",
    "Write to an arbitrary storage location (SWC 124)",
    "Delegatecall to user-supplied address (SWC 112)",
    "Dependence on tx.origin (SWC 115)",
    "Dependence on predictable environment variable (SWC 116)",
    "Dependence on predictable environment variable (SWC 120)",
    "Unprotected Ether Withdrawal (SWC 105)",
    "Exception State (SWC 110)",
    "External Call To User-Supplied Address (SWC 107)",
    "Integer Arithmetic Bugs (SWC 101)",
    "Multiple Calls in a Single Transaction (SWC 113)",
    "State access after external call (SWC 107)",
    "Unprotected Selfdestruct (SWC 106)",
    "Unchecked return value from external call. (SWC 104)",
    "Transaction Order Dependence (SWC 114)",
    "requirement violation (SWC 123)",
    "Strict Ether balance check (SWC 132)",
}


class MythrilParser:
    """Parse Mythril output using SmartBugs logic"""
    
    @staticmethod
    def parse_from_json(result: dict) -> List[SecurityIssue]:
        """
        Parse Mythril JSON output (SmartBugs style)
        
        Args:
            result: Mythril JSON output as dictionary
            
        Returns:
            List of SecurityIssue objects
        """
        issues = []
        
        # Check for errors
        error = result.get("error")
        if error:
            # Error is handled, continue parsing
            pass
        
        for issue in result.get("issues", []):
            finding = {"name": issue.get("title", "Unknown")}
            
            # Map SmartBugs fields
            for i, f in (
                ("filename", "filename"),
                ("contract", "contract"),
                ("function", "function"),
                ("address", "address"),
                ("lineno", "line"),
                ("tx_sequence", "exploit"),
                ("description", "message"),
                ("severity", "severity"),
            ):
                if i in issue:
                    finding[f] = issue[i]
            
            # Add SWC classification
            if "swc-id" in issue:
                finding["name"] += f" (SWC {issue['swc-id']})"
                classification = f"Classification: SWC-{issue['swc-id']}"
                if finding.get("message"):
                    finding["message"] += f"\n{classification}"
                else:
                    finding["message"] = classification
            
            # Workaround for utility.yul files
            if finding.get("filename", "").endswith("#utility.yul"):
                finding.pop("filename", None)
                finding.pop("line", None)
            
            # Map severity
            severity_str = finding.get("severity", "Medium")
            severity_map = {
                "High": Severity.HIGH,
                "Medium": Severity.MEDIUM,
                "Low": Severity.LOW
            }
            severity = severity_map.get(severity_str, Severity.MEDIUM)
            
            issues.append(SecurityIssue(
                tool="mythril",
                severity=severity,
                title=finding.get("name", "Unknown"),
                description=finding.get("message", ""),
                line=finding.get("line"),
                recommendation=f"SWC-{issue.get('swc-id', '')}"
            ))
        
        return issues
    
    @staticmethod
    def parse_from_log(log_lines: List[str]) -> List[SecurityIssue]:
        """
        Parse Mythril output from log (SmartBugs style - JSON in last line)
        
        Args:
            log_lines: Log lines from stdout/stderr
            
        Returns:
            List of SecurityIssue objects
        """
        try:
            # Mythril outputs JSON in the last line
            if log_lines:
                result = json.loads(log_lines[-1])
                return MythrilParser.parse_from_json(result)
        except (json.JSONDecodeError, IndexError):
            pass
        
        return []
    
    @staticmethod
    def parse(exit_code: int, log: List[str], output: bytes) -> List[SecurityIssue]:
        """
        Main parse function matching SmartBugs interface
        
        Args:
            exit_code: Process exit code
            log: Log lines (stdout/stderr)
            output: Binary output (not used for Mythril)
            
        Returns:
            List of SecurityIssue objects
        """
        # Handle exceptions (from SmartBugs logic)
        errors, fails = errors_fails(exit_code, log)
        errors.discard("EXIT_CODE_1")  # exit code = 1 just means vulnerability found
        
        # Check for analysis incomplete
        for line in log:
            if "Exception occurred, aborting analysis." in line:
                # Analysis incomplete, but continue parsing what we have
                break
        
        # Try parsing JSON from last log line
        return MythrilParser.parse_from_log(log)

