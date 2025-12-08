"""
Stage 3: Enhanced Security Analysis with SmartBugs Parser Integration
======================================================================
Integrates 5 tools with SmartBugs-style parsing
"""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from openai import OpenAI
from dotenv import load_dotenv

# Import parsers from separate files
from .parsers import (
    SlitherParser,
    MythrilParser,
    SemgrepParser,
    SolhintParser,
    OyenteParser,
    SmartCheckParser
)

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY"))


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class SecurityIssue:
    """Single security issue"""
    tool: str
    severity: Severity
    title: str
    description: str
    line: Optional[int] = None
    recommendation: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "tool": self.tool,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "line": self.line,
            "recommendation": self.recommendation
        }


@dataclass
class AnalysisResult:
    """Analysis results"""
    contract_name: str
    tools_used: List[str]
    issues: List[SecurityIssue]
    success: bool
    error: Optional[str] = None
    
    def get_critical_high(self) -> List[SecurityIssue]:
        return [i for i in self.issues if i.severity in [Severity.CRITICAL, Severity.HIGH]]
    
    def to_dict(self) -> Dict:
        return {
            "contract_name": self.contract_name,
            "tools_used": self.tools_used,
            "total_issues": len(self.issues),
            "critical": len([i for i in self.issues if i.severity == Severity.CRITICAL]),
            "high": len([i for i in self.issues if i.severity == Severity.HIGH]),
            "medium": len([i for i in self.issues if i.severity == Severity.MEDIUM]),
            "low": len([i for i in self.issues if i.severity == Severity.LOW]),
            "issues": [i.to_dict() for i in self.issues],
            "success": self.success,
            "error": self.error
        }


@dataclass
class Stage3Result:
    """Complete Stage 3 results"""
    original_code: str
    final_code: str
    iterations: int
    initial_analysis: AnalysisResult
    final_analysis: Optional[AnalysisResult]
    fixes_applied: List[Dict]
    issues_resolved: int
    
    def to_dict(self) -> Dict:
        return {
            "iterations": self.iterations,
            "issues_resolved": self.issues_resolved,
            "initial_analysis": self.initial_analysis.to_dict(),
            "final_analysis": self.final_analysis.to_dict() if self.final_analysis else None,
            "fixes_applied": self.fixes_applied
        }


# ============================================================================
# TOOL INSTALLERS & CHECKERS
# ============================================================================

class ToolSetup:
    """Manage security tool installations"""
    
    @staticmethod
    def check_slither() -> bool:
        """Check if Slither is installed"""
        try:
            result = subprocess.run(
                ["slither", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def check_mythril() -> bool:
        """Check if Mythril is installed"""
        try:
            result = subprocess.run(
                ["myth", "version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def check_semgrep() -> bool:
        """Check if Semgrep is installed"""
        try:
            result = subprocess.run(
                ["semgrep", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def check_solhint() -> bool:
        """Check if Solhint is installed"""
        try:
            result = subprocess.run(
                ["solhint", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def check_oyente() -> bool:
        """Check if Oyente is installed"""
        try:
            result = subprocess.run(
                ["oyente", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def check_smartcheck() -> bool:
        """Check if SmartCheck is installed"""
        try:
            result = subprocess.run(
                ["smartcheck", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def install_slither():
        """Install Slither via pip"""
        print("  📦 Installing Slither...")
        try:
            subprocess.run(
                ["pip", "install", "slither-analyzer"],
                check=True,
                capture_output=True
            )
            print("  ✓ Slither installed")
            return True
        except:
            print("  ✗ Slither installation failed")
            return False
    
    @staticmethod
    def install_mythril():
        """Install Mythril via pip"""
        print("  📦 Installing Mythril...")
        try:
            subprocess.run(
                ["pip", "install", "mythril"],
                check=True,
                capture_output=True
            )
            print("  ✓ Mythril installed")
            return True
        except:
            print("  ✗ Mythril installation failed")
            return False
    
    @staticmethod
    def install_semgrep():
        """Install Semgrep via pip"""
        print("  📦 Installing Semgrep...")
        try:
            subprocess.run(
                ["pip", "install", "semgrep"],
                check=True,
                capture_output=True
            )
            print("  ✓ Semgrep installed")
            return True
        except:
            print("  ✗ Semgrep installation failed")
            return False
    
    @staticmethod
    def install_solhint():
        """Install Solhint via npm"""
        print("  📦 Installing Solhint...")
        try:
            subprocess.run(
                ["npm", "install", "-g", "solhint"],
                check=True,
                capture_output=True
            )
            print("  ✓ Solhint installed")
            return True
        except:
            print("  ✗ Solhint installation failed")
            return False
    
    @staticmethod
    def install_oyente():
        """Install Oyente (requires manual setup)"""
        print("  ⚠️  Oyente requires manual installation")
        print("  See: https://github.com/melonproject/oyente")
        return False
    
    @staticmethod
    def install_smartcheck():
        """Install SmartCheck (requires manual setup)"""
        print("  ⚠️  SmartCheck requires manual installation")
        print("  See: https://github.com/smartdec/smartcheck")
        return False
    
    @staticmethod
    def ensure_tools(tools: List[str]) -> List[str]:
        """Ensure tools are installed, return available ones"""
        available = []
        
        for tool in tools:
            if tool == "slither":
                if ToolSetup.check_slither():
                    available.append("slither")
                else:
                    print(f"\n⚠️  Slither not found")
                    if ToolSetup.install_slither():
                        available.append("slither")
            
            elif tool == "mythril":
                if ToolSetup.check_mythril():
                    available.append("mythril")
                else:
                    print(f"\n⚠️  Mythril not found")
                    if ToolSetup.install_mythril():
                        available.append("mythril")
            
            elif tool == "semgrep":
                if ToolSetup.check_semgrep():
                    available.append("semgrep")
                else:
                    print(f"\n⚠️  Semgrep not found")
                    if ToolSetup.install_semgrep():
                        available.append("semgrep")
            
            elif tool == "solhint":
                if ToolSetup.check_solhint():
                    available.append("solhint")
                else:
                    print(f"\n⚠️  Solhint not found")
                    if ToolSetup.install_solhint():
                        available.append("solhint")
            
            elif tool == "oyente":
                if ToolSetup.check_oyente():
                    available.append("oyente")
                else:
                    print(f"\n⚠️  Oyente not found")
                    ToolSetup.install_oyente()  # Manual install only
            
            elif tool == "smartcheck":
                if ToolSetup.check_smartcheck():
                    available.append("smartcheck")
                else:
                    print(f"\n⚠️  SmartCheck not found")
                    ToolSetup.install_smartcheck()  # Manual install only
        
        return available


# ============================================================================
# SECURITY ANALYZERS
# ============================================================================
# Note: Parsers are now in separate files in parsers/ directory

class SlitherAnalyzer:
    """Run Slither analysis with SmartBugs parser"""
    
    @staticmethod
    def analyze(contract_file: Path, timeout: int = 60) -> List[SecurityIssue]:
        """Run Slither and parse results (SmartBugs style)"""
        try:
            # SmartBugs command: slither "$FILENAME" --json /output.json
            result = subprocess.run(
                ["slither", str(contract_file), "--json", "-"],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Use SmartBugs parser interface: parse(exit_code, log, output)
            log_lines = result.stdout.split('\n') if result.stdout else []
            output_bytes = result.stdout.encode() if result.stdout else b''
            
            return SlitherParser.parse(result.returncode, log_lines, output_bytes)
        
        except subprocess.TimeoutExpired:
            print(f"      ⏱ Slither timeout")
            return SlitherParser.parse(None, [], b'')  # Timeout = None exit_code
        except Exception as e:
            print(f"      ✗ Slither error: {str(e)[:30]}")
            return []


class MythrilAnalyzer:
    """Run Mythril analysis with SmartBugs parser"""
    
    @staticmethod
    def analyze(contract_file: Path, timeout: int = 120) -> List[SecurityIssue]:
        """Run Mythril and parse results (SmartBugs style)"""
        try:
            # SmartBugs: myth analyze with JSON output (last line is JSON)
            result = subprocess.run(
                ["myth", "analyze", str(contract_file), "-o", "json"],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Use SmartBugs parser interface: parse(exit_code, log, output)
            log_lines = result.stdout.split('\n') if result.stdout else []
            output_bytes = b''
            
            return MythrilParser.parse(result.returncode, log_lines, output_bytes)
        
        except subprocess.TimeoutExpired:
            print(f"      ⏱ Mythril timeout")
            return MythrilParser.parse(None, [], b'')
        except Exception as e:
            print(f"      ✗ Mythril error: {str(e)[:30]}")
            return []


class SemgrepAnalyzer:
    """Run Semgrep analysis with SmartBugs parser"""
    
    @staticmethod
    def analyze(contract_file: Path, timeout: int = 60) -> List[SecurityIssue]:
        """Run Semgrep and parse results (SmartBugs style)"""
        try:
            # SmartBugs uses semgrep with config
            result = subprocess.run(
                [
                    "semgrep",
                    "--config=auto",
                    "--json",
                    str(contract_file)
                ],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Use SmartBugs parser interface: parse(exit_code, log, output)
            log_lines = result.stdout.split('\n') if result.stdout else []
            output_bytes = b''
            
            return SemgrepParser.parse(result.returncode, log_lines, output_bytes)
        
        except subprocess.TimeoutExpired:
            print(f"      ⏱ Semgrep timeout")
            return SemgrepParser.parse(None, [], b'')
        except Exception as e:
            print(f"      ✗ Semgrep error: {str(e)[:30]}")
            return []


class SolhintAnalyzer:
    """Run Solhint with SmartBugs parser"""
    
    @staticmethod
    def analyze(contract_file: Path, timeout: int = 30) -> List[SecurityIssue]:
        """Run Solhint and parse results (SmartBugs style)"""
        try:
            # SmartBugs command: solhint -f unix "$FILENAME"
            result = subprocess.run(
                ["solhint", "-f", "unix", str(contract_file)],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Use SmartBugs parser interface: parse(exit_code, log, output)
            log_lines = result.stdout.split('\n') if result.stdout else []
            output_bytes = b''
            
            return SolhintParser.parse(result.returncode, log_lines, output_bytes)
        
        except subprocess.TimeoutExpired:
            print(f"      ⏱ Solhint timeout")
            return SolhintParser.parse(None, [], b'')
        except Exception as e:
            print(f"      ✗ Solhint error: {str(e)[:30]}")
            return []


class OyenteAnalyzer:
    """Run Oyente with SmartBugs parser"""
    
    @staticmethod
    def analyze(contract_file: Path, timeout: int = 60) -> List[SecurityIssue]:
        """Run Oyente and parse results"""
        try:
            result = subprocess.run(
                ["oyente", "-s", str(contract_file)],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Use SmartBugs parser interface: parse(exit_code, log, output)
            log_lines = result.stdout.split('\n') if result.stdout else []
            output_bytes = b''
            
            return OyenteParser.parse(result.returncode, log_lines, output_bytes)
        
        except subprocess.TimeoutExpired:
            print(f"      ⏱ Oyente timeout")
            return OyenteParser.parse(None, [], b'')
        except Exception as e:
            print(f"      ✗ Oyente error: {str(e)[:30]}")
            return []


class SmartCheckAnalyzer:
    """Run SmartCheck with SmartBugs parser"""
    
    @staticmethod
    def analyze(contract_file: Path, timeout: int = 30) -> List[SecurityIssue]:
        """Run SmartCheck and parse results"""
        try:
            result = subprocess.run(
                ["smartcheck", "-p", str(contract_file)],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Use SmartBugs parser interface: parse(exit_code, log, output)
            log_lines = result.stdout.split('\n') if result.stdout else []
            output_bytes = b''
            
            return SmartCheckParser.parse(result.returncode, log_lines, output_bytes)
        
        except subprocess.TimeoutExpired:
            print(f"      ⏱ SmartCheck timeout")
            return SmartCheckParser.parse(None, [], b'')
        except Exception as e:
            print(f"      ✗ SmartCheck error: {str(e)[:30]}")
            return []


# ============================================================================
# MAIN ANALYZER
# ============================================================================

class SecurityAnalyzer:
    """Main security analyzer orchestrator"""
    
    DEFAULT_TOOLS = ["slither", "mythril", "semgrep", "solhint", "oyente", "smartcheck"]
    
    ANALYZERS = {
        "slither": SlitherAnalyzer,
        "mythril": MythrilAnalyzer,
        "semgrep": SemgrepAnalyzer,
        "solhint": SolhintAnalyzer,
        "oyente": OyenteAnalyzer,
        "smartcheck": SmartCheckAnalyzer
    }
    
    def __init__(self, auto_install: bool = True):
        self.auto_install = auto_install
    
    def analyze(
        self,
        solidity_code: str,
        contract_name: str,
        tools: Optional[List[str]] = None,
        timeout: int = 120
    ) -> AnalysisResult:
        """
        Run security analysis
        
        Args:
            solidity_code: Solidity source
            contract_name: Contract name
            tools: Tools to use
            timeout: Timeout per tool
        
        Returns:
            AnalysisResult
        """
        if tools is None:
            tools = self.DEFAULT_TOOLS
        
        # Ensure tools are installed
        if self.auto_install:
            available_tools = ToolSetup.ensure_tools(tools)
        else:
            available_tools = [
                t for t in tools
                if (t == "slither" and ToolSetup.check_slither()) or
                   (t == "mythril" and ToolSetup.check_mythril()) or
                   (t == "semgrep" and ToolSetup.check_semgrep()) or
                   (t == "solhint" and ToolSetup.check_solhint()) or
                   (t == "oyente" and ToolSetup.check_oyente()) or
                   (t == "smartcheck" and ToolSetup.check_smartcheck())
            ]
        
        if not available_tools:
            return AnalysisResult(
                contract_name=contract_name,
                tools_used=[],
                issues=[],
                success=False,
                error="No security tools available"
            )
        
        print(f"\n  🔍 Running: {', '.join(available_tools)}")
        
        # Create temporary contract file
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.sol',
            delete=False
        ) as f:
            f.write(solidity_code)
            contract_file = Path(f.name)
        
        try:
            all_issues = []
            tools_succeeded = []
            
            # Run each tool with its SmartBugs parser
            for tool in available_tools:
                print(f"    • {tool}...", end=" ", flush=True)
                
                analyzer = self.ANALYZERS.get(tool)
                if analyzer:
                    issues = analyzer.analyze(contract_file, timeout)
                    if issues is not None:
                        all_issues.extend(issues)
                        tools_succeeded.append(tool)
                        print(f"✓ ({len(issues)} issues)")
                    else:
                        print(f"✗")
                else:
                    print(f"✗ (not implemented)")
            
            return AnalysisResult(
                contract_name=contract_name,
                tools_used=tools_succeeded,
                issues=all_issues,
                success=len(tools_succeeded) > 0
            )
        
        finally:
            # Cleanup
            try:
                contract_file.unlink()
            except:
                pass


# ============================================================================
# LLM FIXER
# ============================================================================

class SecurityFixer:
    """LLM-based vulnerability fixer"""
    
    @staticmethod
    def fix_issues(
        solidity_code: str,
        issues: List[SecurityIssue],
        contract_name: str,
        iteration: int = 1
    ) -> str:
        """Generate fixed code"""
        if not issues:
            return solidity_code
        
        print(f"\n  🔧 Iteration {iteration}: Fixing {len(issues)} issues")
        
        issues_text = SecurityFixer._format_issues(issues)
        
        system_prompt = """You are a Solidity security expert.

Fix security vulnerabilities while:
1. Preserving functionality and public API
2. Maintaining OpenZeppelin v5 compatibility (^0.8.20)
3. Not introducing new bugs

COMMON FIXES:
- Reentrancy: Add ReentrancyGuard, checks-effects-interactions pattern
- Access Control: Add onlyOwner or AccessControl modifiers
- Unchecked Calls: Check return values, use SafeERC20
- Integer Issues: Use SafeMath or ^0.8.20 built-in checks
- tx.origin: Replace with msg.sender

Return ONLY the fixed Solidity code (no markdown, no explanations)."""

        user_prompt = f"""Fix these security issues:

CONTRACT: {contract_name}

CODE:
{solidity_code}

ISSUES:
{issues_text}

Fix all CRITICAL and HIGH issues. Return complete fixed contract."""

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            
            fixed_code = response.choices[0].message.content or ""
            fixed_code = SecurityFixer._clean_code(fixed_code)
            
            print(f"  ✓ Fixes generated")
            return fixed_code
        
        except Exception as e:
            print(f"  ✗ Fix failed: {e}")
            return solidity_code
    
    @staticmethod
    def _format_issues(issues: List[SecurityIssue]) -> str:
        """Format issues for LLM"""
        lines = []
        for i, issue in enumerate(issues, 1):
            line_info = f"Line {issue.line}" if issue.line else "Unknown location"
            lines.append(
                f"{i}. [{issue.severity.value}] {issue.title}\n"
                f"   Tool: {issue.tool}\n"
                f"   Location: {line_info}\n"
                f"   {issue.description}\n"
                f"   Fix: {issue.recommendation or 'Apply security best practices'}\n"
            )
        return "\n".join(lines)
    
    @staticmethod
    def _clean_code(code: str) -> str:
        """Clean LLM output"""
        code = code.strip()
        
        # Remove markdown
        if code.startswith("```solidity"):
            code = code[11:].strip()
        elif code.startswith("```"):
            code = code[3:].strip()
        if code.endswith("```"):
            code = code[:-3].strip()
        
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
# MAIN STAGE 3 FUNCTION
# ============================================================================

def run_stage3(
    solidity_code: str,
    contract_name: str,
    max_iterations: int = 2,
    tools: Optional[List[str]] = None,
    auto_install: bool = True
) -> Stage3Result:
    """
    Run Stage 3: Security Analysis & Auto-Fix
    
    Args:
        solidity_code: Solidity code from Stage 2
        contract_name: Contract name
        max_iterations: Max fix iterations
        tools: Tools to use (default: slither, mythril, semgrep, solhint, oyente, smartcheck)
        auto_install: Auto-install missing tools
    
    Returns:
        Stage3Result
    """
    print("\n" + "="*80)
    print("STAGE 3: SECURITY ANALYSIS & AUTO-FIX (6 TOOLS)")
    print("="*80)
    
    analyzer = SecurityAnalyzer(auto_install=auto_install)
    fixer = SecurityFixer()
    
    original_code = solidity_code
    current_code = solidity_code
    fixes_applied = []
    
    # Initial analysis
    print("\n[1/3] Initial security analysis")
    initial_analysis = analyzer.analyze(current_code, contract_name, tools)
    
    if not initial_analysis.success:
        print(f"\n  ✗ Analysis failed: {initial_analysis.error}")
        return Stage3Result(
            original_code=original_code,
            final_code=current_code,
            iterations=0,
            initial_analysis=initial_analysis,
            final_analysis=None,
            fixes_applied=[],
            issues_resolved=0
        )
    
    print(f"\n  Found {len(initial_analysis.issues)} total issues:")
    print(f"    • Critical: {len([i for i in initial_analysis.issues if i.severity == Severity.CRITICAL])}")
    print(f"    • High: {len([i for i in initial_analysis.issues if i.severity == Severity.HIGH])}")
    print(f"    • Medium: {len([i for i in initial_analysis.issues if i.severity == Severity.MEDIUM])}")
    print(f"    • Low: {len([i for i in initial_analysis.issues if i.severity == Severity.LOW])}")
    print(f"    • Info: {len([i for i in initial_analysis.issues if i.severity == Severity.INFO])}")
    
    # Iterative fixing
    print("\n[2/3] Applying automatic fixes")
    
    iteration = 0
    current_analysis = initial_analysis
    
    while iteration < max_iterations:
        high_priority = current_analysis.get_critical_high()
        
        if not high_priority:
            print(f"\n  ✓ No critical/high issues after {iteration} iterations")
            break
        
        iteration += 1
        
        fixed_code = fixer.fix_issues(
            current_code, high_priority, contract_name, iteration
        )
        
        if fixed_code == current_code:
            print(f"  ⚠️ No changes in iteration {iteration}")
            break
        
        current_code = fixed_code
        
        print(f"\n  🔍 Re-analyzing...")
        current_analysis = analyzer.analyze(current_code, contract_name, tools)
        
        if not current_analysis.success:
            print(f"  ⚠️ Re-analysis failed")
            current_code = original_code
            break
        
        fixes_applied.append({
            "iteration": iteration,
            "issues_before": len(high_priority),
            "issues_after": len(current_analysis.get_critical_high())
        })
        
        print(f"  ✓ Iteration {iteration}: {len(current_analysis.issues)} issues remain")
    
    # Final check
    print("\n[3/3] Final verification")
    final_analysis = current_analysis if iteration > 0 else initial_analysis
    
    issues_resolved = len(initial_analysis.issues) - len(final_analysis.issues)
    
    print(f"\n✅ Stage 3 Complete:")
    print(f"  • Iterations: {iteration}")
    print(f"  • Initial issues: {len(initial_analysis.issues)}")
    print(f"  • Final issues: {len(final_analysis.issues)}")
    print(f"  • Issues resolved: {issues_resolved}")
    
    return Stage3Result(
        original_code=original_code,
        final_code=current_code,
        iterations=iteration,
        initial_analysis=initial_analysis,
        final_analysis=final_analysis,
        fixes_applied=fixes_applied,
        issues_resolved=issues_resolved
    )


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    test_code = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract TestVulnerable {
    mapping(address => uint256) public balances;
    
    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }
    
    // VULNERABLE: Reentrancy
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount);
        (bool success,) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] -= amount;
    }
}
"""
    
    result = run_stage3(
        solidity_code=test_code,
        contract_name="TestVulnerable",
        max_iterations=2,
        tools=["slither", "solhint"]  # Test with Slither and Solhint
    )
    
    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(json.dumps(result.to_dict(), indent=2))