"""
Security Tool Parsers
=====================

Parsers inspired by SmartBugs but adapted for direct CLI execution.
Each parser converts tool output into standardized SecurityIssue objects.
"""

from .base import Parser, ParseResult
from .slither_parser import SlitherParser
from .mythril_parser import MythrilParser
from .semgrep_parser import SemgrepParser
from .solhint_parser import SolhintParser

__all__ = [
    "Parser",
    "ParseResult",
    "SlitherParser",
    "MythrilParser",
    "SemgrepParser",
    "SolhintParser",
]
