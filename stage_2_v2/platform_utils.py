"""
Platform Detection and Tooling Utilities

Detects platform and provides fallbacks for platform-specific tools.
"""

import platform
import os
from typing import Optional, List


def detect_platform() -> str:
    """
    Detect the current platform.
    
    Returns:
        "windows", "linux", or "darwin" (macOS)
    """
    system = platform.system().lower()
    if system == "windows":
        return "windows"
    elif system == "darwin":
        return "darwin"
    elif system == "linux":
        return "linux"
    else:
        return "unknown"


def get_available_tools() -> List[str]:
    """
    Get list of available security tools based on platform.
    
    Returns:
        List of available tool names
    """
    current_platform = detect_platform()
    available = []
    
    # Solidity compiler (should work on all platforms)
    if _check_command("solc"):
        available.append("solc")
    
    # Platform-specific tools
    if current_platform != "windows":
        # These tools typically don't work on Windows
        if _check_command("slither"):
            available.append("slither")
        if _check_command("mythril"):
            available.append("mythril")
        if _check_command("semgrep"):
            available.append("semgrep")
    else:
        # Windows-specific alternatives or WSL detection
        if _check_command("wsl"):
            available.append("wsl_slither")  # Can run via WSL
            available.append("wsl_mythril")
    
    return available


def _check_command(cmd: str) -> bool:
    """Check if a command is available in PATH"""
    import shutil
    return shutil.which(cmd) is not None


def get_tool_warnings() -> List[str]:
    """
    Get warnings about unavailable tools for current platform.
    
    Returns:
        List of warning messages
    """
    warnings = []
    current_platform = detect_platform()
    
    if current_platform == "windows":
        warnings.append("Windows detected: Some security tools (Semgrep, Mythril) may not be available.")
        warnings.append("Consider using WSL or Docker for full tool support.")
    
    return warnings


def should_skip_tool(tool_name: str) -> bool:
    """
    Determine if a tool should be skipped on current platform.
    
    Args:
        tool_name: Name of the tool
    
    Returns:
        True if tool should be skipped
    """
    current_platform = detect_platform()
    
    # Tools that don't work on Windows
    windows_incompatible = ["semgrep", "mythril"]
    
    if current_platform == "windows" and tool_name.lower() in windows_incompatible:
        return True
    
    return False
