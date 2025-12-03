"""
Stage 3: Security Analysis & Auto-Fix Pipeline
==============================================

This module integrates SmartBugs for multi-tool vulnerability detection
and uses LLM to automatically fix security issues.

Dependencies:
- SmartBugs: https://github.com/smartbugs/smartbugs.git
- Docker (for running analysis tools)
"""

import json
import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY"))


# ============================================================================
# TYPE DEFINITIONS
# ============================================================================

class VulnerabilitySeverity(Enum):
    """Severity levels for vulnerabilities"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class VulnerabilityCategory(Enum):
    """Common vulnerability categories"""
    REENTRANCY = "reentrancy"
    ACCESS_CONTROL = "access_control"
    ARITHMETIC = "arithmetic"
    UNCHECKED_CALL = "unchecked_call"
    DENIAL_OF_SERVICE = "denial_of_service"
    FRONT_RUNNING = "front_running"
    TIMESTAMP_DEPENDENCE = "timestamp_dependence"
    TX_ORIGIN = "tx_origin"
    UNINITIALIZED_STORAGE = "uninitialized_storage"
    DELEGATECALL = "delegatecall"
    OTHER = "other"


@dataclass
class NormalizedIssue:
    """Unified vulnerability representation across all tools"""
    tool: str                           # e.g., "slither", "mythril"
    category: VulnerabilityCategory
    severity: VulnerabilitySeverity
    title: str
    description: str
    location: Optional[Dict] = None     # {"file": "...", "line": 123}
    recommendation: str = ""
    raw_output: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "tool": self.tool,
            "category": self.category.value,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "recommendation": self.recommendation
        }


@dataclass
class SecurityAnalysisResult:
    """Results from SmartBugs analysis"""
    contract_name: str
    tools_run: List[str]
    issues_found: List[NormalizedIssue]
    analysis_logs: Dict[str, str]  # tool -> log output
    success: bool
    error_message: Optional[str] = None
    
    def get_issues_by_severity(self, severity: VulnerabilitySeverity) -> List[NormalizedIssue]:
        """Get all issues of a specific severity"""
        return [issue for issue in self.issues_found if issue.severity == severity]
    
    def get_high_severity_count(self) -> int:
        """Count critical and high severity issues"""
        return len([i for i in self.issues_found if i.severity in 
                   [VulnerabilitySeverity.CRITICAL, VulnerabilitySeverity.HIGH]])
    
    def to_dict(self) -> Dict:
        return {
            "contract_name": self.contract_name,
            "tools_run": self.tools_run,
            "issues_found": [issue.to_dict() for issue in self.issues_found],
            "success": self.success,
            "error_message": self.error_message,
            "summary": {
                "total_issues": len(self.issues_found),
                "critical": len(self.get_issues_by_severity(VulnerabilitySeverity.CRITICAL)),
                "high": len(self.get_issues_by_severity(VulnerabilitySeverity.HIGH)),
                "medium": len(self.get_issues_by_severity(VulnerabilitySeverity.MEDIUM)),
                "low": len(self.get_issues_by_severity(VulnerabilitySeverity.LOW)),
            }
        }


@dataclass
class Stage3Result:
    """Complete Stage 3 output with security analysis and fixes"""
    original_code: str
    final_code: str
    iterations: int
    initial_analysis: SecurityAnalysisResult
    final_analysis: Optional[SecurityAnalysisResult]
    fixes_applied: List[Dict]  # List of {iteration, issues_fixed, patch_description}
    remaining_issues: List[NormalizedIssue]
    
    def to_dict(self) -> Dict:
        return {
            "iterations": self.iterations,
            "initial_analysis": self.initial_analysis.to_dict(),
            "final_analysis": self.final_analysis.to_dict() if self.final_analysis else None,
            "fixes_applied": self.fixes_applied,
            "remaining_issues": [issue.to_dict() for issue in self.remaining_issues],
            "summary": {
                "initial_issues": len(self.initial_analysis.issues_found),
                "final_issues": len(self.final_analysis.issues_found) if self.final_analysis else 0,
                "issues_resolved": len(self.initial_analysis.issues_found) - 
                                  (len(self.final_analysis.issues_found) if self.final_analysis else 0)
            }
        }


# ============================================================================
# SMARTBUGS INTEGRATION
# ============================================================================

class SmartBugsRunner:
    """Wrapper for running SmartBugs analysis tools"""
    
    # Default tools to run (fast + comprehensive)
    DEFAULT_TOOLS = ["slither", "mythril"]
    STRICT_TOOLS = ["slither", "mythril", "oyente"]
    
    def __init__(self, smartbugs_path: str = "./smartbugs"):
        """
        Initialize SmartBugs runner.
        
        Args:
            smartbugs_path: Path to SmartBugs repository clone
        """
        self.smartbugs_path = Path(smartbugs_path)
        if not self.smartbugs_path.exists():
            raise RuntimeError(
                f"SmartBugs not found at {smartbugs_path}. "
                f"Clone it: git clone https://github.com/smartbugs/smartbugs.git"
            )
    
    def run_analysis(
        self,
        solidity_code: str,
        contract_name: str,
        tools: Optional[List[str]] = None,
        timeout: int = 300
    ) -> SecurityAnalysisResult:
        """
        Run SmartBugs analysis on Solidity code.
        
        Args:
            solidity_code: Solidity source code
            contract_name: Name of the contract
            tools: List of tools to run (default: slither, mythril)
            timeout: Timeout per tool in seconds
        
        Returns:
            SecurityAnalysisResult with all findings
        """
        if tools is None:
            tools = self.DEFAULT_TOOLS
        
        print(f"  🔍 Running SmartBugs with tools: {', '.join(tools)}")
        
        # Create temporary workspace
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Write contract to file
            contract_file = tmpdir / "dataset" / f"{contract_name}.sol"
            contract_file.parent.mkdir(parents=True, exist_ok=True)
            contract_file.write_text(solidity_code)
            
            # Results directory
            results_dir = tmpdir / "results"
            results_dir.mkdir(exist_ok=True)
            
            # Run SmartBugs
            try:
                cmd = [
                    "python3",
                    str(self.smartbugs_path / "smartbugs.py"),
                    "--tool", ",".join(tools),
                    "--file", str(contract_file),
                    "--processes", "1",
                    "--timeout", str(timeout),
                    "--results", str(results_dir)
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout * len(tools) + 60,
                    cwd=str(self.smartbugs_path)
                )
                
                print(f"  ✓ SmartBugs completed (exit code: {result.returncode})")
                
                # Parse results
                issues = self._parse_results(results_dir, contract_name, tools)
                
                return SecurityAnalysisResult(
                    contract_name=contract_name,
                    tools_run=tools,
                    issues_found=issues,
                    analysis_logs={},
                    success=True
                )
                
            except subprocess.TimeoutExpired:
                print(f"  ⚠️  SmartBugs timeout after {timeout}s")
                return SecurityAnalysisResult(
                    contract_name=contract_name,
                    tools_run=tools,
                    issues_found=[],
                    analysis_logs={},
                    success=False,
                    error_message="Analysis timeout"
                )
            except Exception as e:
                print(f"  ❌ SmartBugs error: {e}")
                return SecurityAnalysisResult(
                    contract_name=contract_name,
                    tools_run=tools,
                    issues_found=[],
                    analysis_logs={},
                    success=False,
                    error_message=str(e)
                )
    
    def _parse_results(
        self,
        results_dir: Path,
        contract_name: str,
        tools: List[str]
    ) -> List[NormalizedIssue]:
        """Parse SmartBugs result files into normalized issues"""
        all_issues = []
        
        for tool in tools:
            tool_results = results_dir / tool / contract_name
            
            if not tool_results.exists():
                continue
            
            # Each tool has different output formats
            if tool == "slither":
                issues = self._parse_slither(tool_results)
            elif tool == "mythril":
                issues = self._parse_mythril(tool_results)
            elif tool == "oyente":
                issues = self._parse_oyente(tool_results)
            else:
                issues = self._parse_generic(tool_results, tool)
            
            all_issues.extend(issues)
        
        return all_issues
    
    def _parse_slither(self, results_path: Path) -> List[NormalizedIssue]:
        """Parse Slither JSON output"""
        issues = []
        
        # Slither typically outputs JSON
        json_files = list(results_path.glob("*.json"))
        if not json_files:
            return issues
        
        try:
            with open(json_files[0]) as f:
                data = json.load(f)
            
            for detector in data.get("results", {}).get("detectors", []):
                severity = self._map_slither_severity(detector.get("impact", ""))
                category = self._map_slither_category(detector.get("check", ""))
                
                issues.append(NormalizedIssue(
                    tool="slither",
                    category=category,
                    severity=severity,
                    title=detector.get("check", "Unknown"),
                    description=detector.get("description", ""),
                    recommendation=detector.get("recommendation", ""),
                    raw_output=detector
                ))
        except Exception as e:
            print(f"    ⚠️  Error parsing Slither: {e}")
        
        return issues
    
    def _parse_mythril(self, results_path: Path) -> List[NormalizedIssue]:
        """Parse Mythril JSON output"""
        issues = []
        
        json_files = list(results_path.glob("*.json"))
        if not json_files:
            return issues
        
        try:
            with open(json_files[0]) as f:
                data = json.load(f)
            
            for issue in data.get("issues", []):
                severity = self._map_mythril_severity(issue.get("severity", ""))
                category = self._map_mythril_category(issue.get("swc-id", ""))
                
                issues.append(NormalizedIssue(
                    tool="mythril",
                    category=category,
                    severity=severity,
                    title=issue.get("title", "Unknown"),
                    description=issue.get("description", ""),
                    location={"line": issue.get("lineno", 0)},
                    raw_output=issue
                ))
        except Exception as e:
            print(f"    ⚠️  Error parsing Mythril: {e}")
        
        return issues
    
    def _parse_oyente(self, results_path: Path) -> List[NormalizedIssue]:
        """Parse Oyente output"""
        # Oyente outputs text, needs custom parsing
        return []
    
    def _parse_generic(self, results_path: Path, tool: str) -> List[NormalizedIssue]:
        """Generic parser for unknown tools"""
        return []
    
    @staticmethod
    def _map_slither_severity(impact: str) -> VulnerabilitySeverity:
        """Map Slither impact to our severity"""
        mapping = {
            "High": VulnerabilitySeverity.HIGH,
            "Medium": VulnerabilitySeverity.MEDIUM,
            "Low": VulnerabilitySeverity.LOW,
            "Informational": VulnerabilitySeverity.INFO,
        }
        return mapping.get(impact, VulnerabilitySeverity.MEDIUM)
    
    @staticmethod
    def _map_slither_category(check: str) -> VulnerabilityCategory:
        """Map Slither check to vulnerability category"""
        if "reentrancy" in check.lower():
            return VulnerabilityCategory.REENTRANCY
        elif "access" in check.lower() or "authorization" in check.lower():
            return VulnerabilityCategory.ACCESS_CONTROL
        elif "arithmetic" in check.lower() or "overflow" in check.lower():
            return VulnerabilityCategory.ARITHMETIC
        elif "call" in check.lower():
            return VulnerabilityCategory.UNCHECKED_CALL
        elif "timestamp" in check.lower():
            return VulnerabilityCategory.TIMESTAMP_DEPENDENCE
        elif "tx.origin" in check.lower():
            return VulnerabilityCategory.TX_ORIGIN
        else:
            return VulnerabilityCategory.OTHER
    
    @staticmethod
    def _map_mythril_severity(severity: str) -> VulnerabilitySeverity:
        """Map Mythril severity to our severity"""
        mapping = {
            "High": VulnerabilitySeverity.HIGH,
            "Medium": VulnerabilitySeverity.MEDIUM,
            "Low": VulnerabilitySeverity.LOW,
        }
        return mapping.get(severity, VulnerabilitySeverity.MEDIUM)
    
    @staticmethod
    def _map_mythril_category(swc_id: str) -> VulnerabilityCategory:
        """Map Mythril SWC-ID to category"""
        # SWC Registry mapping
        swc_mapping = {
            "SWC-107": VulnerabilityCategory.REENTRANCY,
            "SWC-105": VulnerabilityCategory.ACCESS_CONTROL,
            "SWC-115": VulnerabilityCategory.TX_ORIGIN,
            "SWC-101": VulnerabilityCategory.ARITHMETIC,
            "SWC-113": VulnerabilityCategory.DENIAL_OF_SERVICE,
            "SWC-114": VulnerabilityCategory.TIMESTAMP_DEPENDENCE,
        }
        return swc_mapping.get(swc_id, VulnerabilityCategory.OTHER)


# ============================================================================
# LLM-BASED VULNERABILITY FIXER
# ============================================================================

class VulnerabilityFixer:
    """Uses LLM to automatically fix security vulnerabilities"""
    
    @staticmethod
    def generate_fix(
        solidity_code: str,
        issues: List[NormalizedIssue],
        contract_name: str,
        iteration: int = 1
    ) -> str:
        """
        Generate fixed Solidity code addressing the vulnerabilities.
        
        Args:
            solidity_code: Current contract code
            issues: List of vulnerabilities to fix
            contract_name: Name of the contract
            iteration: Current fix iteration number
        
        Returns:
            Fixed Solidity code
        """
        if not issues:
            return solidity_code
        
        print(f"\n  🔧 Iteration {iteration}: Generating fixes for {len(issues)} issues...")
        
        # Build issue summary
        issues_summary = VulnerabilityFixer._build_issue_summary(issues)
        
        system_prompt = """You are a senior Solidity security engineer and auditor.

Your task is to fix security vulnerabilities in smart contracts while:
1. Preserving the contract's functionality and public API
2. Maintaining OpenZeppelin v5 compatibility (Solidity ^0.8.20)
3. Following security best practices
4. Not introducing new bugs

SECURITY PATTERNS TO APPLY:
- Reentrancy: Add ReentrancyGuard, use checks-effects-interactions
- Access Control: Add onlyOwner or role-based modifiers
- Unchecked Calls: Check return values, use SafeERC20
- tx.origin: Replace with msg.sender
- Timestamp Dependence: Add warnings or use block.number
- Arithmetic: Ensure ^0.8.20 overflow protection is used

Return ONLY the complete fixed Solidity contract. No markdown, no explanations."""

        user_prompt = f"""Fix the following security vulnerabilities in this contract:

CONTRACT NAME: {contract_name}

CURRENT CODE:
{solidity_code}

VULNERABILITIES TO FIX:
{issues_summary}

REQUIREMENTS:
1. Fix all HIGH and CRITICAL severity issues
2. Fix MEDIUM issues if possible without breaking functionality
3. Add necessary imports (ReentrancyGuard, SafeERC20, etc.)
4. Add security modifiers where needed
5. Preserve all public functions and their signatures
6. Ensure the contract compiles under Solidity ^0.8.20

Output the complete fixed contract (no markdown, no explanations)."""

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1  # Low temperature for consistent security fixes
            )
            
            fixed_code = response.choices[0].message.content
            if not fixed_code:
                raise RuntimeError("No content returned from LLM")
            
            # Clean up
            fixed_code = VulnerabilityFixer._clean_code(fixed_code)
            
            print(f"  ✓ Fixes generated")
            return fixed_code
            
        except Exception as e:
            print(f"  ❌ Fix generation failed: {e}")
            return solidity_code  # Return original if fix fails
    
    @staticmethod
    def _build_issue_summary(issues: List[NormalizedIssue]) -> str:
        """Build a formatted summary of issues for the LLM"""
        summary_parts = []
        
        # Group by severity
        by_severity = {}
        for issue in issues:
            if issue.severity not in by_severity:
                by_severity[issue.severity] = []
            by_severity[issue.severity].append(issue)
        
        issue_num = 1
        for severity in [VulnerabilitySeverity.CRITICAL, VulnerabilitySeverity.HIGH, 
                         VulnerabilitySeverity.MEDIUM, VulnerabilitySeverity.LOW]:
            if severity not in by_severity:
                continue
            
            for issue in by_severity[severity]:
                location = f"Line {issue.location.get('line')}" if issue.location else "Unknown location"
                summary_parts.append(
                    f"{issue_num}. [{severity.value}] [{issue.category.value}] {issue.title}\n"
                    f"   Tool: {issue.tool}\n"
                    f"   Location: {location}\n"
                    f"   Description: {issue.description}\n"
                    f"   Recommendation: {issue.recommendation or 'Apply security best practices'}\n"
                )
                issue_num += 1
        
        return "\n".join(summary_parts)
    
    @staticmethod
    def _clean_code(code: str) -> str:
        """Clean LLM output"""
        code = code.strip()
        
        # Remove markdown fences
        if code.startswith("```solidity"):
            code = code[len("```solidity"):].strip()
        elif code.startswith("```"):
            code = code[len("```"):].strip()
        
        if code.endswith("```"):
            code = code[:-len("```")].strip()
        
        # Ensure headers
        if "// SPDX-License-Identifier" not in code:
            code = "// SPDX-License-Identifier: MIT\n" + code
        
        if "pragma solidity" not in code:
            lines = code.split('\n')
            for i, line in enumerate(lines):
                if line.startswith("// SPDX"):
                    lines.insert(i + 1, "pragma solidity ^0.8.20;\n")
                    break
            code = '\n'.join(lines)
        
        return code


# ============================================================================
# STAGE 3 MAIN PIPELINE
# ============================================================================

def analyze_and_fix(
    solidity_code: str,
    contract_name: str,
    max_iterations: int = 3,
    smartbugs_path: str = "./smartbugs",
    tools: Optional[List[str]] = None
) -> Stage3Result:
    """
    Complete Stage 3: Security analysis and automatic fixing.
    
    Args:
        solidity_code: Solidity contract from Stage 2
        contract_name: Name of the contract
        max_iterations: Maximum fix iterations
        smartbugs_path: Path to SmartBugs installation
        tools: Analysis tools to run
    
    Returns:
        Stage3Result with analysis and fixes
    """
    print("\n" + "=" * 80)
    print("STAGE 3: SECURITY ANALYSIS & AUTO-FIX")
    print("=" * 80)
    
    runner = SmartBugsRunner(smartbugs_path)
    fixer = VulnerabilityFixer()
    
    original_code = solidity_code
    current_code = solidity_code
    fixes_applied = []
    
    # Initial analysis
    print("\n[1/3] Running initial security analysis...")
    initial_analysis = runner.run_analysis(current_code, contract_name, tools)
    
    if not initial_analysis.success:
        print(f"  ❌ Initial analysis failed: {initial_analysis.error_message}")
        return Stage3Result(
            original_code=original_code,
            final_code=current_code,
            iterations=0,
            initial_analysis=initial_analysis,
            final_analysis=None,
            fixes_applied=[],
            remaining_issues=[]
        )
    
    print(f"  ✓ Found {len(initial_analysis.issues_found)} issues")
    print(f"    • Critical: {len(initial_analysis.get_issues_by_severity(VulnerabilitySeverity.CRITICAL))}")
    print(f"    • High: {len(initial_analysis.get_issues_by_severity(VulnerabilitySeverity.HIGH))}")
    print(f"    • Medium: {len(initial_analysis.get_issues_by_severity(VulnerabilitySeverity.MEDIUM))}")
    
    # Iterative fixing
    print("\n[2/3] Applying automatic fixes...")
    
    iteration = 0
    current_analysis = initial_analysis
    
    while iteration < max_iterations:
        # Get high-priority issues
        high_priority = [
            issue for issue in current_analysis.issues_found
            if issue.severity in [VulnerabilitySeverity.CRITICAL, VulnerabilitySeverity.HIGH]
        ]
        
        if not high_priority:
            print(f"  ✓ No high-priority issues remaining after {iteration} iterations")
            break
        
        iteration += 1
        
        # Generate fix
        fixed_code = fixer.generate_fix(current_code, high_priority, contract_name, iteration)
        
        if fixed_code == current_code:
            print(f"  ⚠️  No changes made in iteration {iteration}")
            break
        
        current_code = fixed_code
        
        # Re-analyze
        print(f"  🔍 Re-analyzing after iteration {iteration}...")
        current_analysis = runner.run_analysis(current_code, contract_name, tools)
        
        if not current_analysis.success:
            print(f"  ⚠️  Re-analysis failed, keeping previous version")
            current_code = original_code
            break
        
        fixes_applied.append({
            "iteration": iteration,
            "issues_targeted": len(high_priority),
            "issues_remaining": len(current_analysis.issues_found)
        })
        
        print(f"  ✓ Iteration {iteration} complete: {len(current_analysis.issues_found)} issues remaining")
    
    # Final analysis
    print("\n[3/3] Final security check...")
    final_analysis = current_analysis if iteration > 0 else initial_analysis
    
    remaining_issues = final_analysis.issues_found if final_analysis else []
    
    print(f"\n✅ Stage 3 Complete:")
    print(f"  • Iterations: {iteration}")
    print(f"  • Initial issues: {len(initial_analysis.issues_found)}")
    print(f"  • Final issues: {len(remaining_issues)}")
    print(f"  • Issues resolved: {len(initial_analysis.issues_found) - len(remaining_issues)}")
    
    result = Stage3Result(
        original_code=original_code,
        final_code=current_code,
        iterations=iteration,
        initial_analysis=initial_analysis,
        final_analysis=final_analysis,
        fixes_applied=fixes_applied,
        remaining_issues=remaining_issues
    )
    
    print("=" * 80)
    
    return result


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test with a deliberately vulnerable contract
    test_contract = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VulnerableContract {
    mapping(address => uint256) public balances;
    address public owner;
    
    constructor() {
        owner = msg.sender;
    }
    
    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }
    
    // Vulnerable: reentrancy
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount);
        
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        
        balances[msg.sender] -= amount;
    }
    
    // Vulnerable: no access control
    function emergencyWithdraw() external {
        payable(msg.sender).transfer(address(this).balance);
    }
}
"""
    
    result = analyze_and_fix(
        solidity_code=test_contract,
        contract_name="VulnerableContract",
        max_iterations=2,
        smartbugs_path="./smartbugs"
    )
    
    print("\n" + "=" * 80)
    print("STAGE 3 RESULTS SUMMARY")
    print("=" * 80)
    print(json.dumps(result.to_dict(), indent=2))