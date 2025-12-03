# solidity_code_generator/__init__.py
"""Stage 2 Solidity code generation package (modular)."""

from .generator import generate_solidity
from .categories import ContractCategory, ContractProfile, GenerationResult, SpecCoverage, AccessControlType, SecurityFeature

__all__ = [
    "generate_solidity",
    "ContractCategory",
    "ContractProfile",
    "GenerationResult",
    "SpecCoverage",
    "AccessControlType",
    "SecurityFeature",
]
