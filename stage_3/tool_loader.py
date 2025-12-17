"""
Tool Loader
===========

Load tool configurations from YAML files (SmartBugs-style)
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional


class ToolConfig:
    """Tool configuration loaded from YAML"""
    
    def __init__(self, tool_id: str, config: dict):
        self.id = tool_id
        self.name = config.get("name", tool_id)
        self.version = config.get("version", "")
        self.image = config.get("image")
        # bin can be at top level or inside solidity section
        self.bin = config.get("bin") or config.get("solidity", {}).get("bin")
        self.output = config.get("output")
        
        # Solidity mode config
        solidity = config.get("solidity", {})
        self.solidity_entrypoint = solidity.get("entrypoint")
        self.solidity_solc = solidity.get("solc", False)
        
        # Store full config
        self.config = config
    
    def to_dict(self) -> dict:
        """Convert to dictionary for Docker executor"""
        return {
            "id": self.id,
            "name": self.name,
            "image": self.image,
            "bin": self.bin,
            "output": self.output,
            "solidity": {
                "entrypoint": self.solidity_entrypoint,
                "solc": self.solidity_solc,
            }
        }


def load_tool(tool_id: str) -> Optional[ToolConfig]:
    """
    Load tool configuration from YAML file
    
    Args:
        tool_id: Tool identifier (e.g., "slither", "mythril")
    
    Returns:
        ToolConfig or None if not found
    """
    tools_dir = Path(__file__).parent / "tools"
    tool_dir = tools_dir / tool_id
    config_path = tool_dir / "config.yaml"
    
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, "r", encoding="utf8") as f:
            config = yaml.safe_load(f)
        
        # Handle aliases
        if "alias" in config:
            return load_tool(config["alias"])
        
        return ToolConfig(tool_id, config)
    
    except Exception as e:
        print(f"  ⚠️  Failed to load tool {tool_id}: {e}")
        return None


def load_tools(tool_ids: List[str]) -> List[ToolConfig]:
    """Load multiple tool configurations"""
    tools = []
    for tool_id in tool_ids:
        tool = load_tool(tool_id)
        if tool:
            tools.append(tool)
        else:
            print(f"  ⚠️  Tool {tool_id} not found")
    return tools

