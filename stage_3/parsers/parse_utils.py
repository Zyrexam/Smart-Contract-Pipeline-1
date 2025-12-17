"""
Parser utilities extracted from SmartBugs
Adapted to work without SmartBugs dependencies
"""

import re
from typing import Optional, Set, Tuple, List, Dict, Pattern


# Docker exit codes mapping
DOCKER_CODES: Dict[int, str] = {
    125: "DOCKER_INVOCATION_PROBLEM",
    126: "DOCKER_CMD_NOT_EXECUTABLE",
    127: "DOCKER_CMD_NOT_FOUND",
    137: "DOCKER_KILL_OOM",
    139: "DOCKER_SEGV",
    143: "DOCKER_TERM",
}

# ANSI escape sequence removal
ANSI: Pattern[str] = re.compile("\x1b\\[[^m]*m")


def discard_ansi(lines) -> List[str]:
    """Remove ANSI escape sequences from log lines"""
    return [ANSI.sub("", line) for line in lines]


# Exception patterns
TRACEBACK: str = "Traceback (most recent call last):"

EXCEPTIONS: Tuple[Pattern[str], ...] = (
    re.compile(".*line [0-9: ]*(Segmentation fault|Killed)"),
    re.compile('Exception in thread "[^"]*" (.*)'),
    re.compile(r"^(?:[a-zA-Z0-9]+\.)+[a-zA-Z0-9]*Exception: (.*)$"),
    re.compile("thread '[^']*' panicked at '([^']*)'"),
)


def exceptions(lines: List[str]) -> Set[str]:
    """Extract exceptions from log lines"""
    exceptions_set = set()
    traceback = False
    for line in lines:
        if traceback:
            if line and line[0] != " ":
                exceptions_set.add(f"exception ({line})")
                traceback = False
        elif line.endswith(TRACEBACK):
            traceback = True
        else:
            for re_exception in EXCEPTIONS:
                if m := re_exception.match(line):
                    exceptions_set.add(f"exception ({m[1]})")
    return exceptions_set


def add_match(matches: Set[str], line: str, patterns: List[Pattern[str]]) -> bool:
    """Add match to set if pattern matches line"""
    for pattern in patterns:
        m = pattern.match(line)
        if m:
            matches.add(m[1])
            return True
    return False


def errors_fails(
    exit_code: Optional[int], log: Optional[List[str]], log_expected: bool = True
) -> Tuple[Set[str], Set[str]]:
    """
    Extract errors and fails from exit code and log
    
    Returns:
        Tuple of (errors, fails) sets
    """
    errors = set()  # errors detected and handled by the tool
    fails = set()  # exceptions not caught by the tool
    
    if exit_code is None:
        fails.add("DOCKER_TIMEOUT")
    elif exit_code == 0:
        pass
    elif exit_code == 127:
        fails.add(
            "SmartBugs was invoked with option 'main', but the filename did not match any contract"
        )
    elif exit_code in DOCKER_CODES:
        fails.add(DOCKER_CODES[exit_code])
    elif 128 <= exit_code <= 128 + 64:
        fails.add(f"DOCKER_RECEIVED_SIGNAL_{exit_code-128}")
    else:
        errors.add(f"EXIT_CODE_{exit_code}")
    
    if log:
        fails.update(exceptions(log))
    elif log_expected and not fails:
        fails.add("execution failed")
    
    return errors, fails

