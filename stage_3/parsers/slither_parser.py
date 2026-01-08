"""
Slither Parser
==============

Adapted from SmartBugs tools/slither-0.11.3/parser.py
Modified for direct CLI execution (JSON output to stdout, not tar file)
"""

import json
import re
from typing import List, Optional, Set

from ..models import SecurityIssue, Severity
from .base import Parser, ParseResult


class SlitherParser(Parser):
    """Parse Slither JSON output"""
    
    # Impact to Severity mapping
    IMPACT_TO_SEVERITY = {
        "High": Severity.HIGH,
        "Medium": Severity.MEDIUM,
        "Low": Severity.LOW,
        "Informational": Severity.INFO,
        "Optimization": Severity.INFO,
    }
    
    # Location pattern (adapted for direct paths, not /sb/ paths)
    LOCATION_PATTERN = re.compile(r"([^#]+)#(\d+)(?:-(\d+))?")
    
    def __init__(self):
        super().__init__("slither")
    
    def parse(
        self,
        exit_code: Optional[int],
        stdout: str,
        stderr: str
    ) -> ParseResult:
        """Parse Slither JSON output (from /output.json file)"""
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
        
        # Slither may return non-zero on errors, but we still try to parse
        if exit_code == 255:
            errors.discard("EXIT_CODE_255")  # Common non-error code
        
        # Slither writes to /output.json file (extracted by analyzer)
        # stdout should contain the JSON content from the file
        output_dict = {}
        
        if stdout.strip():
            # Try to parse JSON from stdout (which should be the file content)
            try:
                output_dict = json.loads(stdout)
            except json.JSONDecodeError as e:
                # Debug: log the error and stdout preview
                import sys
                if hasattr(sys, 'stderr'):
                    print(f"[SLITHER PARSER DEBUG] JSON decode error: {str(e)[:100]}", file=sys.stderr)
                    print(f"[SLITHER PARSER DEBUG] stdout length: {len(stdout)}", file=sys.stderr)
                    print(f"[SLITHER PARSER DEBUG] stdout first 500: {stdout[:500]}", file=sys.stderr)
                # Try to find JSON in lines
                json_lines = []
                in_json = False
                brace_count = 0
                for line in stdout_lines:
                    line_stripped = line.strip()
                    if line_stripped.startswith('{') or in_json:
                        in_json = True
                        json_lines.append(line)
                        # Count braces to find complete JSON
                        brace_count += line.count('{') - line.count('}')
                        if brace_count == 0 and in_json:
                            break
                
                if json_lines:
                    try:
                        json_str = '\n'.join(json_lines)
                        output_dict = json.loads(json_str)
                    except json.JSONDecodeError:
                        # Try to extract JSON from the middle of the string
                        # Sometimes there's extra text before/after JSON
                        json_start = stdout.find('{')
                        if json_start >= 0:
                            # Find matching closing brace
                            brace_count = 0
                            json_end = -1
                            for i in range(json_start, len(stdout)):
                                if stdout[i] == '{':
                                    brace_count += 1
                                elif stdout[i] == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        json_end = i
                                        break
                            
                            if json_end > json_start:
                                try:
                                    json_str = stdout[json_start:json_end+1]
                                    output_dict = json.loads(json_str)
                                except json.JSONDecodeError:
                                    fails.add(f"error parsing JSON output: {str(e)[:100]}")
                        else:
                            fails.add(f"error parsing JSON output: {str(e)[:100]}")
                else:
                    fails.add("no JSON output found")
        else:
            fails.add("no output received")
        
        # Check if we have a valid output dict
        if not output_dict:
            # Return early with fails
            return ParseResult(
                issues=issues,
                errors=errors,
                fails=fails,
                infos=infos
            )
        
        # Extract findings FIRST - check for detectors regardless of success flag
        # Slither may set success=false even when detectors are found
        results = output_dict.get("results", {})
        detectors = results.get("detectors", [])
        
        # Debug: log detector count
        import sys
        if hasattr(sys, 'stderr'):
            print(f"[SLITHER PARSER DEBUG] Found {len(detectors)} detectors", file=sys.stderr)
            if detectors:
                print(f"[SLITHER PARSER DEBUG] First detector: {detectors[0].get('check', 'unknown')}", file=sys.stderr)
        
        # Parse all detectors
        for detector in detectors:
            issue = self._parse_detector(detector)
            if issue:
                issues.append(issue)
        
        # Check success flag - but don't fail if success is False, just note it
        # IMPORTANT: We parse detectors FIRST, so even if success=false, we still get issues
        if not output_dict.get("success", False):
            error_msg = output_dict.get("error", "analysis unsuccessful")
            # If we found detectors, success=false is not a problem
            if len(detectors) > 0:
                # Slither found issues but marked success=false - this is OK
                infos.add("slither found detectors despite success=false")
            elif error_msg and error_msg not in ["analysis unsuccessful", "Slither execution failed"]:
                # No detectors and a specific error message
                infos.add(f"slither reported: {error_msg}")
        
        # Only add as error if there's a specific error message (not the generic fallback)
        # AND no detectors were found (if detectors exist, it's not really an error)
        if (output_dict.get("error") and 
            output_dict.get("error") not in ["Slither execution failed", "analysis unsuccessful"] and
            len(detectors) == 0):
            errors.add(f"slither error: {output_dict.get('error', 'unknown')[:50]}")
        
        return ParseResult(
            issues=issues,
            errors=errors,
            fails=fails,
            infos=infos
        )
    
    def _parse_detector(self, detector: dict) -> Optional[SecurityIssue]:
        """Parse a single detector result"""
        check = detector.get("check", "")
        impact = detector.get("impact", "Informational")
        confidence = detector.get("confidence", "Medium")
        description = detector.get("description", "")
        elements = detector.get("elements", [])
        
        # Map impact to severity
        severity = self.IMPACT_TO_SEVERITY.get(impact, Severity.INFO)
        
        # Extract location information
        line = None
        line_end = None
        filename = None
        contract = None
        function = None
        
        # Try to extract from description (location pattern)
        location_match = self.LOCATION_PATTERN.search(description)
        if location_match:
            filename = location_match.group(1).strip()
            line = int(location_match.group(2))
            if location_match.group(3):
                line_end = int(location_match.group(3))
        
        # Extract from elements
        for element in elements:
            if element.get("type") == "function":
                function = element.get("name")
                type_specific = element.get("type_specific_fields", {})
                parent = type_specific.get("parent", {})
                if parent.get("type") == "contract":
                    contract = parent.get("name")
            
            if "source_mapping" in element:
                source_mapping = element["source_mapping"]
                lines = sorted(source_mapping.get("lines", []))
                if lines:
                    if line is None:
                        line = lines[0]
                    if line_end is None and len(lines) > 1:
                        line_end = lines[-1]
                if filename is None:
                    filename_abs = source_mapping.get("filename_absolute", "")
                    if filename_abs:
                        # Clean up path
                        filename = filename_abs.split('/')[-1]
        
        # Build recommendation
        recommendation = self._get_recommendation(check, impact)
        
        return SecurityIssue(
            tool=self.tool_name,
            severity=severity,
            title=check or "Slither Finding",
            description=description or f"{check} detected",
            line=line,
            line_end=line_end,
            filename=filename,
            contract=contract,
            function=function,
            recommendation=recommendation
        )
    
    def _get_recommendation(self, check: str, impact: str) -> str:
        """Get fix recommendation based on check type"""
        recommendations = {
            "reentrancy-eth": "Use ReentrancyGuard and checks-effects-interactions pattern",
            "reentrancy-no-eth": "Use ReentrancyGuard and checks-effects-interactions pattern",
            "unchecked-transfer": "Check return value or use SafeERC20",
            "unchecked-send": "Check return value or use SafeERC20",
            "tx-origin": "Replace tx.origin with msg.sender",
            "arbitrary-send-eth": "Add access control and input validation",
            "suicidal": "Add access control to selfdestruct",
            "locked-ether": "Add withdrawal function or make contract payable",
        }
        
        return recommendations.get(check, "Review and apply security best practices")
