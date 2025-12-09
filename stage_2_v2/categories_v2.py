"""
Categories for Dynamic Classification System

Simplified categories that work with LLM classification.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SpecCoverage:
    """Maps specification elements to implementation strategies"""
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
    """Contract profile with template/custom distinction"""
    category: str  # "ERC20", "ERC721", "Custom", etc.
    base_standard: str  # "ERC20", "Governor", "Custom"
    extensions: List[str]
    access_control: str  # "single_owner", "role_based", "none"
    security_features: List[str]  # ["ReentrancyGuard", "Pausable"]
    subtype: Optional[str] = None  # "election", "certificate", etc. (for Custom)
    is_template: bool = False  # True for ERC20, Governor, etc.
    
    def describe(self):
        ext_str = ", ".join(self.extensions) if self.extensions else "None"
        sec_str = ", ".join(self.security_features) if self.security_features else "None"
        return (
            f"Category: {self.category}\n"
            f"Base Standard: {self.base_standard}\n"
            f"Extensions: {ext_str}\n"
            f"Access Control: {self.access_control}\n"
            f"Security Features: {sec_str}\n"
            f"Is Template: {self.is_template}\n"
            f"Subtype: {self.subtype or 'N/A'}\n"
        )


@dataclass
class GenerationResult:
    """Result of code generation"""
    solidity_code: str
    profile: ContractProfile
    coverage: SpecCoverage
    validation_errors: List[str]
    security_summary: str
    imports_used: List[str]
    inheritance_chain: List[str]
    classification: Optional[Dict] = None
    fixes_applied: List[Dict] = field(default_factory=list)  # Track repair attempts
    
    def to_metadata_dict(self):
        return {
            "category": self.profile.category,
            "base_standard": self.profile.base_standard,
            "extensions": self.profile.extensions,
            "access_control": self.profile.access_control,
            "security_features": self.profile.security_features,
            "coverage": self.coverage.to_dict(),
            "validation_errors": self.validation_errors,
            "security_summary": self.security_summary,
            "imports_used": self.imports_used,
            "inheritance_chain": self.inheritance_chain,
            "is_template": self.profile.is_template,
            "subtype": self.profile.subtype,
            "classification": self.classification,
            "fixes_applied": self.fixes_applied,
        }
