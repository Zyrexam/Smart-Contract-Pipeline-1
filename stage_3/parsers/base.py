from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

from ..models import SecurityIssue
from ..utils import errors_fails


@dataclass
class ParseResult:
    """Result from parsing tool output"""
    issues: List[SecurityIssue]
    errors: Set[str]
    fails: Set[str]
    infos: Set[str]


class Parser(ABC):
    """Base class for tool output parsers"""
    
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
    
    @abstractmethod
    def parse(
        self,
        exit_code: Optional[int],
        stdout: str,
        stderr: str
    ) -> ParseResult:
        """
        Parse tool output into SecurityIssue objects
        
        Args:
            exit_code: Process exit code (None = timeout)
            stdout: Standard output
            stderr: Standard error
        
        Returns:
            ParseResult with issues, errors, fails, infos
        """
        pass
    
    def _extract_errors_fails(
        self,
        exit_code: Optional[int],
        stdout_lines: List[str],
        stderr_lines: List[str]
    ) -> Tuple[Set[str], Set[str]]:
        """Extract errors and failures from output"""
        all_lines = stdout_lines + stderr_lines
        return errors_fails(exit_code, all_lines if all_lines else None)

