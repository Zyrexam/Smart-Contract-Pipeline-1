"""
Slither Parser - Extracted from SmartBugs tools/slither-0.11.3/parser.py
Adapted for direct CLI execution (no Docker dependency)
"""

import io
import json
import re
import tarfile
from typing import List, Optional

# Import our data structures - use TYPE_CHECKING to avoid circular imports
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from security_integration import SecurityIssue, Severity
else:
    # Runtime import
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from security_integration import SecurityIssue, Severity

from .parse_utils import errors_fails


VERSION = "2025/09/14"

# All possible Slither findings (from SmartBugs)
FINDINGS = {
    "abiencoderv2-array",
    "arbitrary-send-erc20",
    "arbitrary-send-erc20-permit",
    "arbitrary-send-eth",
    "array-by-reference",
    "assembly",
    "assert-state-change",
    "backdoor",
    "boolean-cst",
    "boolean-equal",
    "cache-array-length",
    "calls-loop",
    "chainlink-feed-registry",
    "chronicle-unchecked-price",
    "codex",
    "constable-states",
    "constant-function-asm",
    "constant-function-state",
    "controlled-array-length",
    "controlled-delegatecall",
    "costly-loop",
    "cyclomatic-complexity",
    "dead-code",
    "delegatecall-loop",
    "deprecated-standards",
    "divide-before-multiply",
    "domain-separator-collision",
    "encode-packed-collision",
    "enum-conversion",
    "erc20-indexed",
    "erc20-interface",
    "erc721-interface",
    "events-access",
    "events-maths",
    "external-function",
    "function-init-state",
    "gelato-unprotected-randomness",
    "immutable-states",
    "incorrect-equality",
    "incorrect-exp",
    "incorrect-modifier",
    "incorrect-return",
    "incorrect-shift",
    "incorrect-unary",
    "incorrect-using-for",
    "locked-ether",
    "low-level-calls",
    "mapping-deletion",
    "missing-inheritance",
    "missing-zero-check",
    "msg-value-loop",
    "multiple-constructors",
    "name-reused",
    "naming-convention",
    "optimism-deprecation",
    "out-of-order-retryable",
    "pragma",
    "protected-vars",
    "public-mappings-nested",
    "pyth-deprecated-functions",
    "pyth-unchecked-confidence",
    "pyth-unchecked-publishtime",
    "redundant-statements",
    "reentrancy-benign",
    "reentrancy-eth",
    "reentrancy-events",
    "reentrancy-no-eth",
    "reentrancy-unlimited-gas",
    "return-bomb",
    "return-leave",
    "reused-constructor",
    "rtlo",
    "shadowing-abstract",
    "shadowing-builtin",
    "shadowing-local",
    "shadowing-state",
    "solc-version",
    "storage-array",
    "suicidal",
    "tautological-compare",
    "tautology",
    "timestamp",
    "token-reentrancy",
    "too-many-digits",
    "tx-origin",
    "unchecked-lowlevel",
    "unchecked-send",
    "unchecked-transfer",
    "unimplemented-functions",
    "uninitialized-fptr-cst",
    "uninitialized-local",
    "uninitialized-state",
    "uninitialized-storage",
    "unprotected-upgrade",
    "unused-import",
    "unused-return",
    "unused-state",
    "variable-scope",
    "var-read-using-this",
    "void-cst",
    "weak-prng",
    "write-after-write",
}

LOCATION = re.compile(r"/sb/(.*?)#([0-9-]*)")


class SlitherParser:
    """Parse Slither output using SmartBugs logic"""
    
    @staticmethod
    def parse_from_json(output_dict: dict) -> List[SecurityIssue]:
        """
        Parse Slither JSON output (SmartBugs style)
        
        Args:
            output_dict: Slither JSON output as dictionary
            
        Returns:
            List of SecurityIssue objects
        """
        issues = []
        
        if not output_dict.get("success", False):
            return issues
        
        if output_dict.get("error", None):
            # Error reported but continue parsing
            pass
        
        results = output_dict.get("results", {})
        detectors = results.get("detectors", [])
        
        for issue in detectors:
            finding = {}
            # Map SmartBugs fields
            for i, f in (
                ("check", "name"),
                ("impact", "impact"),
                ("confidence", "confidence"),
                ("description", "message"),
            ):
                if i in issue:
                    finding[f] = issue[i]
            
            # Clean message
            if "message" in finding:
                finding["message"] = finding["message"].replace("../../sb/", "")
            
            # Extract location from message or elements
            elements = issue.get("elements", [])
            m = LOCATION.search(finding.get("message", ""))
            if m:
                finding["filename"] = m[1]
                if "-" in m[2]:
                    start, end = m[2].split("-")
                    finding["line"] = int(start)
                    finding["line_end"] = int(end)
                else:
                    finding["line"] = int(m[2])
            elif len(elements) > 0 and "source_mapping" in elements[0]:
                source_mapping = elements[0]["source_mapping"]
                lines = sorted(source_mapping.get("lines", []))
                if len(lines) > 0:
                    finding["line"] = lines[0]
                    if len(lines) > 1:
                        finding["line_end"] = lines[-1]
                if "filename_absolute" in source_mapping:
                    finding["filename"] = source_mapping["filename_absolute"].replace("/sb/", "")
            
            # Extract function and contract
            for element in elements:
                if element.get("type") == "function":
                    finding["function"] = element["name"]
                    type_specific_fields = element.get("type_specific_fields", {})
                    parent = type_specific_fields.get("parent", {})
                    if parent.get("type", None) == "contract":
                        finding["contract"] = parent.get("name", "")
                    break
            
            # Map severity
            impact = finding.get("impact", "Medium")
            severity_map = {
                "High": Severity.HIGH,
                "Medium": Severity.MEDIUM,
                "Low": Severity.LOW,
                "Informational": Severity.INFO,
                "Optimization": Severity.INFO
            }
            severity = severity_map.get(impact, Severity.MEDIUM)
            
            # Get recommendation from markdown if available
            recommendation = issue.get("markdown", "")
            
            issues.append(SecurityIssue(
                tool="slither",
                severity=severity,
                title=finding.get("name", "Unknown"),
                description=finding.get("message", ""),
                line=finding.get("line"),
                recommendation=recommendation
            ))
        
        return issues
    
    @staticmethod
    def parse_from_tar(output_bytes: bytes) -> List[SecurityIssue]:
        """
        Parse Slither tar.gz output (SmartBugs Docker style)
        
        Args:
            output_bytes: Tar.gz file content as bytes
            
        Returns:
            List of SecurityIssue objects
        """
        try:
            with io.BytesIO(output_bytes) as o, tarfile.open(fileobj=o) as tar:
                output_json = tar.extractfile("output.json").read()
                output_dict = json.loads(output_json)
                return SlitherParser.parse_from_json(output_dict)
        except Exception:
            return []
    
    @staticmethod
    def parse(exit_code: int, log: List[str], output: bytes) -> List[SecurityIssue]:
        """
        Main parse function matching SmartBugs interface (from tools/slither-0.11.3/parser.py)
        
        Args:
            exit_code: Process exit code
            log: Log lines (stdout/stderr)
            output: Binary output (tar.gz for Docker, empty for direct)
            
        Returns:
            List of SecurityIssue objects
        """
        # SmartBugs logic: handle errors and fails
        errors, fails = errors_fails(exit_code, log)
        errors.discard("EXIT_CODE_255")  # this code seems to be returned in any case
        
        # Try parsing from tar.gz first (Docker output - SmartBugs style)
        output_dict = {}
        if output:
            try:
                with io.BytesIO(output) as o, tarfile.open(fileobj=o) as tar:
                    output_json = tar.extractfile("output.json").read()
                    output_dict = json.loads(output_json)
            except Exception:
                # If tar parsing fails, try JSON from log
                pass
        
        # Fallback: try parsing JSON from log (direct CLI execution)
        if not output_dict:
            for line in reversed(log):
                try:
                    data = json.loads(line)
                    if "results" in data or "detectors" in data:
                        output_dict = data
                        break
                except (json.JSONDecodeError, ValueError):
                    continue
        
        # Parse the output dictionary
        if output_dict:
            return SlitherParser.parse_from_json(output_dict)
        
        return []

