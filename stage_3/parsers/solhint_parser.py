"""
Solhint Parser - Extracted from SmartBugs tools/solhint-6.0.0/parser.py
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

from .parse_utils import errors_fails

VERSION = "2025/09/14"

# All possible Solhint findings (from SmartBugs)
FINDINGS = {
    "avoid-call-value",
    "avoid-low-level-calls",
    "avoid-sha3",
    "avoid-suicide",
    "avoid-throw",
    "avoid-tx-origin",
    "check-send-result",
    "code-complexity",
    "compiler-version",
    "comprehensive-interface",
    "const-name-snakecase",
    "constructor-syntax",
    "contract-name-capwords",
    "duplicated-imports",
    "event-name-capwords",
    "explicit-types",
    "foundry-test-functions",
    "func-named-parameters",
    "func-name-mixedcase",
    "func-param-name-mixedcase",
    "function-max-lines",
    "func-visibility",
    "gas-calldata-parameters",
    "gas-custom-errors",
    "gas-increment-by-one",
    "gas-indexed-events",
    "gas-length-in-loops",
    "gas-multitoken1155",
    "gas-named-return-values",
    "gas-small-strings",
    "gas-strict-inequalities",
    "gas-struct-packing",
    "immutable-vars-naming",
    "import-path-check",
    "imports-on-top",
    "imports-order",
    "interface-starts-with-i",
    "max-line-length",
    "max-states-count",
    "modifier-name-mixedcase",
    "multiple-sends",
    "named-parameters-mapping",
    "no-complex-fallback",
    "no-console",
    "no-empty-blocks",
    "no-global-import",
    "no-inline-assembly",
    "not-rely-on-block-hash",
    "not-rely-on-time",
    "no-unused-import",
    "no-unused-vars",
    "one-contract-per-file",
    "ordering",
    "payable-fallback",
    "private-vars-leading-underscore",
    "quotes",
    "reason-string",
    "reentrancy",
    "state-visibility",
    "use-forbidden-name",
    "use-natspec",
    "var-name-mixedcase",
    "visibility-modifier-order",
}

# Exact regex from SmartBugs
REPORT = re.compile(
    r"""
    ^(?P<filename>[^:]*)
    :(?P<line>\d+)
    :(?P<column>\d+)
    :\s*(?P<message>.*?)
    \s*\[(?P<level>[^\[/\]]*)/
    (?P<name>[^\[/\]]*)\]$
""",
    re.VERBOSE,
)


class SolhintParser:
    """Parse Solhint output using SmartBugs logic"""
    
    @staticmethod
    def parse(exit_code: int, log: List[str], output: bytes) -> List[SecurityIssue]:
        """
        Main parse function matching SmartBugs interface
        
        Args:
            exit_code: Process exit code
            log: Log lines (stdout/stderr)
            output: Binary output (not used for Solhint)
            
        Returns:
            List of SecurityIssue objects
        """
        issues = []
        errors, fails = errors_fails(exit_code, log)
        errors.discard("EXIT_CODE_1")  # Solhint returns 1 when issues found
        
        for line in log:
            match = REPORT.match(line)
            if match:
                finding = match.groupdict()
                finding["line"] = int(finding["line"])
                finding["column"] = int(finding["column"])
                finding["level"] = finding["level"].lower()
                
                # Map severity
                severity_map = {
                    "error": Severity.HIGH,
                    "warning": Severity.MEDIUM,
                    "info": Severity.LOW
                }
                severity = severity_map.get(finding["level"], Severity.MEDIUM)
                
                issues.append(SecurityIssue(
                    tool="solhint",
                    severity=severity,
                    title=finding["name"],
                    description=finding["message"],
                    line=finding["line"],
                    recommendation=f"Rule: {finding['name']}"
                ))
        
        return issues

