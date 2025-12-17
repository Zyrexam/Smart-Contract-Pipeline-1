"""
Stage 3: Security Analysis & Auto-Fix
======================================

SmartBugs-Lite: Lightweight security analysis with Docker support for Windows compatibility.
Uses SmartBugs-inspired architecture (YAML configs, Docker execution) but rewritten for our pipeline.
"""

from .runner import run_stage3
from .models import SecurityIssue, Severity, AnalysisResult, Stage3Result

__all__ = [
    "run_stage3",
    "SecurityIssue",
    "Severity",
    "AnalysisResult",
    "Stage3Result",
]

