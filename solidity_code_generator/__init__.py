"""Stage 2 Solidity code generation package.

This package exposes a single high-level API:

    from solidity_code_generator import generate_solidity

which takes a Stage 1 JSON specification and returns a GenerationResult
containing the Solidity source code plus rich metadata.
"""

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
