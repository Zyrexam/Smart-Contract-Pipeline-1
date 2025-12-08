"""
Oyente Parser - Extracted from SmartBugs tools/oyente/parser.py
Adapted for direct CLI execution (no Docker dependency)
"""

import re
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

from .parse_utils import errors_fails, add_match

VERSION = "2025/06/04"

# All possible Oyente findings (from SmartBugs)
FINDINGS = {
    "Callstack Depth Attack Vulnerability",
    "Transaction-Ordering Dependence (TOD)",
    "Timestamp Dependency",
    "Re-Entrancy Vulnerability",
    "Integer Overflow",
    "Integer Underflow",
    "Parity Multisig Bug 2",
}

# Regex patterns from SmartBugs
CONTRACT = re.compile(r"^INFO:root:[Cc]ontract ([^:]*):([^:]*):")
WEAKNESS = re.compile(r"^INFO:symExec:[\s└>]*([^:]*):\s*True")  # Note: SmartBugs uses └
LOCATION1 = re.compile(r"^INFO:symExec:([^:]*):([0-9]+):([0-9]+):\s*([^:]*):\s*(.*)\.")
LOCATION2 = re.compile(r"^([^:]*):([^:]*):([0-9]+):([0-9]+)")
COMPLETED = re.compile(r"^INFO:symExec:\s*====== Analysis Completed ======")
COVERAGE = re.compile(r"^INFO:symExec:\s*EVM Code Coverage:\s+([0-9]+(?:\.[0-9]+)?%)$")

# Info patterns
INFOS = (re.compile(r"(incomplete push instruction) at [0-9]+"),)

# Error patterns
ERRORS = (
    re.compile(r"!!! (SYMBOLIC EXECUTION TIMEOUT) !!!"),
    re.compile(r"(UNKNOWN INSTRUCTION: .*)"),
    re.compile(r"CRITICAL:root:(Solidity compilation failed)"),
)


def is_relevant(line: str) -> bool:
    """Identify lines interfering with exception parsing (from SmartBugs)"""
    return not (
        line.startswith("888")
        or line.startswith("`88b")
        or line.startswith("!!! ")
        or line.startswith("UNKNOWN INSTRUCTION:")
    )


class OyenteParser:
    """Parse Oyente output using SmartBugs logic"""
    
    @staticmethod
    def parse(exit_code: int, log: List[str], output: bytes) -> List[SecurityIssue]:
        """
        Main parse function matching SmartBugs interface
        
        Args:
            exit_code: Process exit code
            log: Log lines (stdout/stderr)
            output: Binary output (not used for Oyente)
            
        Returns:
            List of SecurityIssue objects
        """
        issues = []
        infos = set()
        
        # Filter relevant lines
        cleaned_log = list(filter(is_relevant, log))
        errors, fails = errors_fails(exit_code, cleaned_log)
        errors.discard("EXIT_CODE_1")  # redundant: indicates error or vulnerability reported below
        
        analysis_completed = False
        filename, contract, weakness = None, None, None
        weaknesses: set = set()
        
        for line in log:
            # Check for infos
            if add_match(infos, re.sub(r"[ \t]+", " ", line).strip(), list(INFOS)):
                continue
            
            # Check for errors
            if add_match(errors, line, list(ERRORS)):
                continue
            
            # Check for fails
            if add_match(fails, line, []):
                continue
            
            # Match contract
            m = CONTRACT.match(line)
            if m:
                filename, contract = m[1], m[2]
                analysis_completed = False
                continue
            
            # Match weakness
            m = WEAKNESS.match(line)
            if m:
                weakness = m[1]
                if weakness == "Arithmetic bugs":
                    # Osiris: superfluous, will also report a sub-category
                    continue
                weaknesses.add((filename, contract, weakness, None, None))
                continue
            
            # Match location (type 1)
            m = LOCATION1.match(line)
            if m:
                fn, lineno, column, _, weakness = m[1], m[2], m[3], m[4], m[5]
                weaknesses.discard((filename, contract, weakness, None, None))
                weaknesses.add((filename, contract, weakness, int(lineno), int(column)))
                continue
            
            # Match location (type 2)
            m = LOCATION2.match(line)
            if m:
                fn, ct, lineno, column = m[1], m[2], m[3], m[4]
                if fn == filename and ct == contract and weakness is not None:
                    weaknesses.discard((filename, contract, weakness, None, None))
                    weaknesses.add((filename, contract, weakness, int(lineno), int(column)))
                continue
            
            # Match coverage
            m = COVERAGE.match(line)
            if m:
                coverage = m[1]
                info = f"coverage {contract+' ' if contract else ''}{coverage}"
                infos.add(info)
                continue
            
            # Match completion
            m = COMPLETED.match(line)
            if m:
                analysis_completed = True
                continue
        
        # Convert weaknesses to issues
        for filename, contract, weakness, lineno, column in sorted(weaknesses):
            finding = {"name": weakness}
            if filename:
                finding["filename"] = filename
            if contract:
                finding["contract"] = contract
            if lineno:
                finding["line"] = lineno
            if column:
                finding["column"] = column
            
            # Map severity based on vulnerability type
            severity = Severity.HIGH
            if "Callstack Depth" in weakness or "Transaction-Ordering" in weakness:
                severity = Severity.MEDIUM
            elif "Timestamp Dependency" in weakness:
                severity = Severity.LOW
            
            issues.append(SecurityIssue(
                tool="oyente",
                severity=severity,
                title=finding["name"],
                description=f"Found in {finding.get('contract', '')}" if finding.get("contract") else finding["name"],
                line=finding.get("line"),
                recommendation=""
            ))
        
        return issues

