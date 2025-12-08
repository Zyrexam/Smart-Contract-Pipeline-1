"""
Semgrep Parser - Extracted from SmartBugs tools/semgrep-1.131.0-1.2.1/parser.py
Adapted for direct CLI execution (no Docker dependency)
"""

import json
import re
from collections.abc import Iterator
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

VERSION = "2025/08/06"

# All possible Semgrep findings (from SmartBugs)
FINDINGS = [
    "accessible-selfdestruct",
    "arbitrary-low-level-call",
    "array-length-outside-loop",
    "bad-transferfrom-access-control",
    "balancer-readonly-reentrancy-getpooltokens",
    "balancer-readonly-reentrancy-getrate",
    "basic-arithmetic-underflow",
    "basic-oracle-manipulation",
    "compound-borrowfresh-reentrancy",
    "compound-precision-loss",
    "compound-sweeptoken-not-restricted",
    "curve-readonly-reentrancy",
    "delegatecall-to-arbitrary-address",
    "encode-packed-collision",
    "erc20-public-burn",
    "erc20-public-transfer",
    "erc677-reentrancy",
    "erc721-arbitrary-transferfrom",
    "erc721-reentrancy",
    "erc777-reentrancy",
    "exact-balance-check",
    "gearbox-tokens-path-confusion",
    "incorrect-use-of-blockhash",
    "inefficient-state-variable-increment",
    "init-variables-with-default-value",
    "keeper-network-oracle-manipulation",
    "missing-assignment",
    "msg-value-multicall",
    "no-bidi-characters",
    "non-optimal-variables-swap",
    "non-payable-constructor",
    "no-slippage-check",
    "olympus-dao-staking-incorrect-call-order",
    "openzeppelin-ecdsa-recover-malleable",
    "oracle-price-update-not-restricted",
    "oracle-uses-curve-spot-price",
    "proxy-storage-collision",
    "public-transfer-fees-supporting-tax-tokens",
    "redacted-cartel-custom-approval-bug",
    "rigoblock-missing-access-control",
    "sense-missing-oracle-access-control",
    "state-variable-read-in-a-loop",
    "superfluid-ctx-injection",
    "tecra-coin-burnfrom-bug",
    "thirdweb-vulnerability",
    "uniswap-callback-not-protected",
    "uniswap-v4-callback-not-protected",
    "unnecessary-checked-arithmetic-in-loop",
    "unrestricted-transferownership",
    "use-abi-encodecall-instead-of-encodewithselector",
    "use-custom-error-not-require",
    "use-multiple-require",
    "use-nested-if",
    "use-ownable2step",
    "use-prefix-decrement-not-postfix",
    "use-prefix-increment-not-postfix",
    "use-short-revert-string",
]


def message_lines(log_iterator: Iterator[str]) -> str:
    """Extract message lines from iterator (from SmartBugs)"""
    msg_lines: list[str] = []
    while True:
        next_line = next(log_iterator, "").strip()
        if not next_line:
            break
        msg_lines.append(next_line)
    return " ".join(msg_lines)


class SemgrepParser:
    """Parse Semgrep output using SmartBugs logic"""
    
    @staticmethod
    def parse_from_regex(log_lines: List[str]) -> List[SecurityIssue]:
        """
        Parse Semgrep output using regex (SmartBugs style)
        
        Args:
            log_lines: Log lines from stdout
            
        Returns:
            List of SecurityIssue objects
        """
        issues = []
        finding: dict = {}
        log_iterator = iter(log_lines)
        
        for line in log_iterator:
            line = line.strip()
            
            # Match category and rule name
            if re.search(r"solidity\.(performance|best-practice|security)\.", line):
                match = re.search(r"solidity\.(performance|best-practice|security)\.(\S+)", line)
                if match:
                    category = match.group(1)
                    name = match.group(2)
                    finding["name"] = name
                    finding["category"] = category
                    finding["message"] = message_lines(log_iterator)
            
            # Match line number (format: "123┆")
            elif re.search(r"\d+┆", line):
                line_location = line.strip().split("┆", 1)
                if len(line_location) > 0:
                    cline_number = int(line_location[0])
                    finding["line"] = cline_number
                
                # Map severity based on category
                category = finding.get("category", "security")
                severity_map = {
                    "security": Severity.HIGH,
                    "performance": Severity.MEDIUM,
                    "best-practice": Severity.LOW
                }
                severity = severity_map.get(category, Severity.MEDIUM)
                
                issues.append(SecurityIssue(
                    tool="semgrep",
                    severity=severity,
                    title=finding.get("name", "Unknown"),
                    description=finding.get("message", ""),
                    line=finding.get("line"),
                    recommendation=""
                ))
                finding = {}
        
        return issues
    
    @staticmethod
    def parse_from_json(data: dict) -> List[SecurityIssue]:
        """
        Parse Semgrep JSON output (fallback)
        
        Args:
            data: Semgrep JSON output as dictionary
            
        Returns:
            List of SecurityIssue objects
        """
        issues = []
        
        for finding in data.get("results", []):
            severity_str = finding.get("extra", {}).get("severity", "WARNING")
            severity_map = {
                "ERROR": Severity.HIGH,
                "WARNING": Severity.MEDIUM,
                "INFO": Severity.LOW
            }
            severity = severity_map.get(severity_str, Severity.MEDIUM)
            
            issues.append(SecurityIssue(
                tool="semgrep",
                severity=severity,
                title=finding.get("check_id", "Unknown"),
                description=finding.get("extra", {}).get("message", ""),
                line=finding.get("start", {}).get("line"),
                recommendation=""
            ))
        
        return issues
    
    @staticmethod
    def parse(exit_code: int, log: List[str], output: bytes) -> List[SecurityIssue]:
        """
        Main parse function matching SmartBugs interface
        
        Args:
            exit_code: Process exit code
            log: Log lines (stdout/stderr)
            output: Binary output (not used for Semgrep)
            
        Returns:
            List of SecurityIssue objects
        """
        errors, fails = errors_fails(exit_code, log)
        
        # Try regex parsing first (SmartBugs style)
        issues = SemgrepParser.parse_from_regex(log)
        
        # Fallback to JSON parsing if regex didn't find anything
        if not issues:
            for line in reversed(log):
                try:
                    data = json.loads(line)
                    if "results" in data:
                        return SemgrepParser.parse_from_json(data)
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return issues

