"""
Utility Functions
"""

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Optional, Set, Tuple


def ensure_dir(path: str) -> str:
    """Ensure directory exists"""
    Path(path).mkdir(parents=True, exist_ok=True)
    return str(Path(path))


def read_json(path: str) -> dict:
    """Read JSON file"""
    with open(path, "r", encoding="utf8") as f:
        return json.load(f)


def write_json(path: str, obj: dict) -> None:
    """Write JSON file"""
    ensure_dir(Path(path).parent)
    with open(path, "w", encoding="utf8") as f:
        json.dump(obj, f, indent=2)


def errors_fails(
    exit_code: Optional[int], 
    log: Optional[List[str]], 
    log_expected: bool = True
) -> Tuple[Set[str], Set[str]]:
    """
    Extract errors and failures from tool execution.
    Inspired by SmartBugs parse_utils.errors_fails
    """
    errors = set()  # Errors detected and handled by the tool
    fails = set()    # Exceptions or failures
    
    if exit_code is None:
        fails.add("TIMEOUT")
    elif exit_code == 0:
        pass  # Success
    elif exit_code == 127:
        fails.add("COMMAND_NOT_FOUND")
    else:
        errors.add(f"EXIT_CODE_{exit_code}")
    
    if log:
        # Check for exceptions in log
        traceback_started = False
        for line in log:
            if "Traceback (most recent call last):" in line:
                traceback_started = True
            elif traceback_started and line.strip() and not line.startswith(" "):
                errors.add(f"exception ({line.strip()})")
                traceback_started = False
            elif any(pattern in line.lower() for pattern in ["error", "failed", "exception"]):
                if "error" in line.lower() and "traceback" not in line.lower():
                    errors.add(f"error: {line.strip()[:100]}")
    
    elif log_expected and not fails:
        fails.add("execution failed")
    
    return errors, fails

