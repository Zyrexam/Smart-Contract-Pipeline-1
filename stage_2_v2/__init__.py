# stage_2_v2 package
"""
Stage 2 V2 - LLM-Powered Generalized Code Generation

This version uses LLM classification instead of hardcoded category detection,
making it truly generalized for any contract type.

Features:
- LLM-powered classification (no hardcoded keywords)
- Profile-aware code generation (templates vs custom)
- Robust JSON parsing and error handling
- Fixes tracking and auditability
- Platform detection and tool fallbacks
"""

from .generator_v2 import generate_solidity_v2, generate_solidity
from .llm_classifier import classify_contract
from .profile_selector_v2 import select_profile_dynamic
from .categories_v2 import ContractProfile, SpecCoverage, GenerationResult
from .llm_utils import safe_parse_json, call_chat_completion, validate_classification_schema
from .platform_utils import detect_platform, get_available_tools, get_tool_warnings

__all__ = [
    'generate_solidity_v2',
    'generate_solidity',
    'classify_contract',
    'select_profile_dynamic',
    'ContractProfile',
    'SpecCoverage',
    'GenerationResult',
    'safe_parse_json',
    'call_chat_completion',
    'validate_classification_schema',
    'detect_platform',
    'get_available_tools',
    'get_tool_warnings',
]
