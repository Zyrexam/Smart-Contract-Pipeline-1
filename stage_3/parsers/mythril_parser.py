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
        
        # If exit_code is None (timeout) but we successfully parse issues, don't mark as timeout failure
        # This allows partial results from timeouts to be accepted
        timeout_fail = "TIMEOUT" in fails
        
        # Check for exceptions in output
        for line in stdout_lines + stderr_lines:
            if "Exception occurred, aborting analysis." in line:
                infos.add("analysis incomplete")
                if not fails and not errors:
                    fails.add("execution failed")
        
        # Try to parse JSON - Mythril outputs JSON, but it might be anywhere in output
        result = None
        try:
            # Debug: Log what we're receiving (first 500 chars and last 500 chars)
            debug_info = []
            if stdout:
                debug_info.append(f"stdout length: {len(stdout)}")
                debug_info.append(f"stdout first 500: {stdout[:500]}")
                if len(stdout) > 500:
                    debug_info.append(f"stdout last 500: {stdout[-500:]}")
                debug_info.append(f"stdout_lines count: {len(stdout_lines)}")
                if stdout_lines:
                    debug_info.append(f"first line (first 200): {stdout_lines[0][:200]}")
                    debug_info.append(f"last line (first 200): {stdout_lines[-1][:200]}")
            
            # Strategy 1: Find JSON by looking for { and } in the entire stdout
            # This handles both single-line and multi-line JSON
            json_start = stdout.find('{')
            if json_start >= 0:
                debug_info.append(f"Found {{ at position: {json_start}")
                # Find the matching closing brace (need to handle nested braces)
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
                    json_str = stdout[json_start:json_end+1]
                    debug_info.append(f"Extracted JSON length: {len(json_str)}")
                    debug_info.append(f"JSON first 200 chars: {json_str[:200]}")
                    
                    # Fix: Escape control characters that are invalid in JSON strings
                    # Mythril sometimes outputs unescaped newlines in description fields
                    # We need to escape them properly: \n -> \\n, but only within string values
                    # Simple approach: replace control chars that appear outside of already-escaped sequences
                    import re
                    # Build a fixed string by processing character by character within string contexts
                    json_str_fixed = ""
                    in_string = False
                    escape_next = False
                    i = 0
                    while i < len(json_str):
                        char = json_str[i]
                        if escape_next:
                            json_str_fixed += char
                            escape_next = False
                        elif char == '\\':
                            json_str_fixed += char
                            escape_next = True
                        elif char == '"' and (i == 0 or json_str[i-1] != '\\' or (i > 1 and json_str[i-2] == '\\')):
                            json_str_fixed += char
                            in_string = not in_string
                        elif in_string and char == '\n':
                            json_str_fixed += '\\n'
                        elif in_string and char == '\r':
                            json_str_fixed += '\\r'
                        elif in_string and char == '\t':
                            json_str_fixed += '\\t'
                        elif in_string and ord(char) < 32:  # Other control characters
                            json_str_fixed += f'\\u{ord(char):04x}'
                        else:
                            json_str_fixed += char
                        i += 1
                    
                    try:
                        parsed = json.loads(json_str_fixed)
                        debug_info.append(f"JSON parsed successfully, keys: {list(parsed.keys())}")
                        # Check if it's a valid Mythril result
                        if isinstance(parsed, dict) and ('issues' in parsed or 'error' in parsed):
                            result = parsed
                            debug_info.append(f"Valid Mythril result found! Issues: {len(parsed.get('issues', []))}")
                        else:
                            debug_info.append(f"Not a valid Mythril result (missing 'issues' or 'error' key)")
                    except json.JSONDecodeError as e:
                        debug_info.append(f"JSON decode error after fixing: {str(e)[:200]}")
                        # Try a simpler fix: just replace newlines in the middle of the string
                        try:
                            # More aggressive: replace all unescaped control chars
                            simple_fix = json_str.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                            parsed = json.loads(simple_fix)
                            if isinstance(parsed, dict) and ('issues' in parsed or 'error' in parsed):
                                result = parsed
                                debug_info.append("Parsed with simple fix")
                        except:
                            pass
                else:
                    debug_info.append(f"Could not find matching closing brace (json_end: {json_end})")
            else:
                debug_info.append("No '{' found in stdout")
            
            # Strategy 2: Try parsing lines that start with {
            if result is None:
                json_candidates = []
                for line in stdout_lines:
                    line_stripped = line.strip()
                    if line_stripped.startswith('{'):
                        json_candidates.append(line_stripped)
                
                # Try parsing candidates (prefer last one, as it's usually the final result)
                for candidate in reversed(json_candidates):
                    try:
                        parsed = json.loads(candidate)
                        # Check if it's a valid Mythril result
                        if isinstance(parsed, dict) and ('issues' in parsed or 'error' in parsed):
                            result = parsed
                            break
                    except json.JSONDecodeError:
                        continue
            
            # Strategy 3: Try parsing entire stdout as JSON
            if result is None:
                try:
                    parsed = json.loads(stdout.strip())
                    if isinstance(parsed, dict) and ('issues' in parsed or 'error' in parsed):
                        result = parsed
                except json.JSONDecodeError:
                    pass
            
            # If still no result, mark as failed and include debug info
            if result is None:
                debug_msg = "error parsing JSON output - no valid JSON found"
                if debug_info:
                    debug_msg += f" | Debug: {'; '.join(debug_info[:5])}"  # Limit to first 5 debug messages
                fails.add(debug_msg)
                # Print debug info to stderr for troubleshooting (when verbose mode is on)
                import sys
                if hasattr(sys, 'stderr'):
                    print(f"[MYTHRIL PARSER DEBUG] {' | '.join(debug_info)}", file=sys.stderr)
        except Exception as e:
            fails.add(f"error parsing JSON output: {str(e)}")
            import sys
            if hasattr(sys, 'stderr'):
                print(f"[MYTHRIL PARSER DEBUG] Exception: {str(e)}", file=sys.stderr)
                if debug_info:
                    print(f"[MYTHRIL PARSER DEBUG] {' | '.join(debug_info)}", file=sys.stderr)
        
        if result:
            error = result.get("error")
            if error:
                errors.add(error.split(".")[0])
            
            # Parse issues
            for issue in result.get("issues", []):
                security_issue = self._parse_issue(issue)
                if security_issue:
                    issues.append(security_issue)
            
            # If we successfully parsed issues, remove TIMEOUT from fails
            # This allows partial results from timeouts to be accepted
            if issues and timeout_fail:
                fails.discard("TIMEOUT")
                infos.add("analysis completed with timeout (partial results)")
        
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
