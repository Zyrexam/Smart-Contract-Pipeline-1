# solidity_code_generator/categories.py
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

class ContractCategory(Enum):
    ERC20 = "ERC20"
    ERC721 = "ERC721"
    ERC1155 = "ERC1155"
    STAKING = "STAKING"
    VAULT = "VAULT"
    AMM = "AMM"
    LENDING = "LENDING"
    GOVERNANCE = "GOVERNANCE"
    TIMELOCK = "TIMELOCK"
    NFT_MARKETPLACE = "NFT_MARKETPLACE"
    AUCTION = "AUCTION"
    UPGRADEABLE = "UPGRADEABLE"
    MULTISIG = "MULTISIG"
    CUSTOM = "CUSTOM"

class AccessControlType(Enum):
    SINGLE_OWNER = "single_owner"
    ROLE_BASED = "role_based"

class SecurityFeature(Enum):
    REENTRANCY_GUARD = "ReentrancyGuard"
    PAUSABLE = "Pausable"
    TIMELOCK = "TimelockController"

@dataclass
class SpecCoverage:
    state_variables: Dict[str, str] = field(default_factory=dict)
    functions: Dict[str, str] = field(default_factory=dict)
    events: Dict[str, str] = field(default_factory=dict)
    roles: Dict[str, str] = field(default_factory=dict)
    modifiers: Dict[str, str] = field(default_factory=dict)
    def to_dict(self):
        return {
            "state_variables": self.state_variables,
            "functions": self.functions,
            "events": self.events,
            "roles": self.roles,
            "modifiers": self.modifiers,
        }

@dataclass
class ContractProfile:
    category: ContractCategory
    base_standard: str
    extensions: List[str]
    access_control: AccessControlType
    security_features: List[SecurityFeature]
    supply_semantics: Optional[Dict] = None
    def describe(self):
        ext_str = ", ".join(self.extensions) if self.extensions else "None"
        sec_str = ", ".join([s.value for s in self.security_features]) if self.security_features else "None"
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
    solidity_code: str
    profile: ContractProfile
    coverage: SpecCoverage
    validation_errors: List[str]
    security_summary: str
    imports_used: List[str]
    inheritance_chain: List[str]
    def to_metadata_dict(self):
        return {
            "category": self.profile.category.value,
            "base_standard": self.profile.base_standard,
            "extensions": self.profile.extensions,
            "access_control": self.profile.access_control.value,
            "security_features": [s.value for s in self.profile.security_features],
            "coverage": self.coverage.to_dict(),
            "validation_errors": self.validation_errors,
            "security_summary": self.security_summary,
            "imports_used": self.imports_used,
            "inheritance_chain": self.inheritance_chain,
        }
