"""
SmartBugs-style parsers for security analysis tools
Extracted from SmartBugs repository and adapted for direct CLI execution
"""

from .slither_parser import SlitherParser
from .mythril_parser import MythrilParser
from .semgrep_parser import SemgrepParser
from .solhint_parser import SolhintParser
from .oyente_parser import OyenteParser
from .smartcheck_parser import SmartCheckParser

__all__ = [
    "SlitherParser",
    "MythrilParser",
    "SemgrepParser",
    "SolhintParser",
    "OyenteParser",
    "SmartCheckParser",
]

