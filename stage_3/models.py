"""
Data Models for Stage 3
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class Severity(Enum):
    """Issue severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"
    
    @classmethod
    def from_string(cls, s: str) -> "Severity":
        """Convert string to Severity"""
        s_upper = s.upper()
        for sev in cls:
            if sev.value == s_upper:
                return sev
        # Fallback mapping
        if "critical" in s_upper or "high" in s_upper:
            return cls.HIGH
        elif "medium" in s_upper:
            return cls.MEDIUM
        elif "low" in s_upper:
            return cls.LOW
        else:
            return cls.INFO


@dataclass
class SecurityIssue:
    """A single security issue detected by a tool"""
    tool: str
    severity: Severity
    title: str
    description: str
    line: Optional[int] = None
    line_end: Optional[int] = None
    filename: Optional[str] = None
    contract: Optional[str] = None
    function: Optional[str] = None
    recommendation: str = ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "tool": self.tool,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "line": self.line,
            "line_end": self.line_end,
            "filename": self.filename,
            "contract": self.contract,
            "function": self.function,
            "recommendation": self.recommendation,
        }


@dataclass
class AnalysisResult:
    """Results from security analysis"""
    contract_name: str
    tools_used: List[str]
    issues: List[SecurityIssue]
    success: bool
    error: Optional[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []
    
    def get_critical_high(self) -> List[SecurityIssue]:
        """Get only CRITICAL and HIGH severity issues"""
        return [
            i for i in self.issues 
            if i.severity in [Severity.CRITICAL, Severity.HIGH]
        ]
    
    def get_by_severity(self, severity: Severity) -> List[SecurityIssue]:
        """Get issues by severity"""
        return [i for i in self.issues if i.severity == severity]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "contract_name": self.contract_name,
            "tools_used": self.tools_used,
            "total_issues": len(self.issues),
            "critical": len(self.get_by_severity(Severity.CRITICAL)),
            "high": len(self.get_by_severity(Severity.HIGH)),
            "medium": len(self.get_by_severity(Severity.MEDIUM)),
            "low": len(self.get_by_severity(Severity.LOW)),
            "info": len(self.get_by_severity(Severity.INFO)),
            "issues": [i.to_dict() for i in self.issues],
            "success": self.success,
            "error": self.error,
            "warnings": self.warnings,
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
    stage2_metadata: Optional[Dict] = None
    compiles: Optional[bool] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "iterations": self.iterations,
            "issues_resolved": self.issues_resolved,
            "initial_analysis": self.initial_analysis.to_dict(),
            "final_analysis": self.final_analysis.to_dict() if self.final_analysis else None,
            "fixes_applied": self.fixes_applied,
            "stage2_metadata": self.stage2_metadata,
            "compiles": self.compiles,
        }

