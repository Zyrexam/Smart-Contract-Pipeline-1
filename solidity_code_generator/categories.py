"""Core enums and data structures for Stage 2 Solidity generation.

This module is intentionally dependency-light so it can be imported
everywhere else in the Stage 2 pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class ContractCategory(Enum):
    """All supported contract categories.

    This merges basic token standards with DeFi, governance and
    marketplace categories so the rest of the pipeline only needs one
    category enum.
    """

    # Token standards
    ERC20 = "ERC20"
    ERC721 = "ERC721"
    ERC1155 = "ERC1155"

    # DeFi primitives
    STAKING = "STAKING"
    VAULT = "VAULT"
    AMM = "AMM"
    LENDING = "LENDING"

    # Governance / DAO
    GOVERNANCE = "GOVERNANCE"
    TIMELOCK = "TIMELOCK"

    # Marketplaces / trading
    NFT_MARKETPLACE = "NFT_MARKETPLACE"
    AUCTION = "AUCTION"

    # Advanced patterns
    UPGRADEABLE = "UPGRADEABLE"
    MULTISIG = "MULTISIG"

    # Generic fallback
    CUSTOM = "CUSTOM"


class AccessControlType(Enum):
    """High-level access control model used by generated contracts."""

    SINGLE_OWNER = "single_owner"  # Ownable
    ROLE_BASED = "role_based"      # AccessControl


class SecurityFeature(Enum):
    """Optional security patterns that may be enabled per profile."""

    REENTRANCY_GUARD = "ReentrancyGuard"
    PAUSABLE = "Pausable"
    TIMELOCK = "TimelockController"


@dataclass
class SpecCoverage:
    """Tracks how Stage 1 JSON spec items map to generated code.

    Each dict maps the spec item name to a short implementation note.
    """

    state_variables: Dict[str, str] = field(default_factory=dict)
    functions: Dict[str, str] = field(default_factory=dict)
    events: Dict[str, str] = field(default_factory=dict)
    roles: Dict[str, str] = field(default_factory=dict)
    modifiers: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "state_variables": self.state_variables,
            "functions": self.functions,
            "events": self.events,
            "roles": self.roles,
            "modifiers": self.modifiers,
        }


@dataclass
class ContractProfile:
    """Detailed contract generation profile selected from JSON spec.

    This is the central abstraction that tells the prompt builder and
    code generator *what kind* of contract to build.
    """

    category: ContractCategory
    base_standard: str  # e.g. "ERC20", "ERC721", "Staking", "NFTMarketplace"
    extensions: List[str]
    access_control: AccessControlType
    security_features: List[SecurityFeature]
    supply_semantics: Optional[Dict] = None  # e.g. {"type": "capped", "cap": 1_000_000}

    def describe(self) -> str:
        """Human-readable profile description for prompts/logging."""

        ext_str = ", ".join(self.extensions) if self.extensions else "None"
        sec_str = ", ".join(sf.value for sf in self.security_features) if self.security_features else "None"
        return (
            f"Profile: {self.category.value}\n"
            f"Base: {self.base_standard}\n"
            f"Extensions: {ext_str}\n"
            f"Access Control: {self.access_control.value}\n"
            f"Security Features: {sec_str}\n"
            f"Supply: {self.supply_semantics or 'Standard'}\n"
        )


@dataclass
class GenerationResult:
    """High-level Stage 2 output with metadata.

    This is what `generate_solidity` returns.
    """

    solidity_code: str
    profile: ContractProfile
    coverage: SpecCoverage
    validation_errors: List[str]
    security_summary: str
    imports_used: List[str]
    inheritance_chain: List[str]

    def to_metadata_dict(self) -> Dict:
        return {
            "category": self.profile.category.value,
            "base_standard": self.profile.base_standard,
            "extensions": self.profile.extensions,
            "access_control": self.profile.access_control.value,
            "security_features": [sf.value for sf in self.profile.security_features],
            "coverage": self.coverage.to_dict(),
            "validation_errors": self.validation_errors,
            "security_summary": self.security_summary,
            "imports_used": self.imports_used,
            "inheritance_chain": self.inheritance_chain,
        }
