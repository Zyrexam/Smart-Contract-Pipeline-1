"""
Enhanced Stage 2: Advanced Solidity Code Generation
==================================================

This enhanced version includes:
1. Deep JSON spec utilization with coverage reporting
2. Smart profile/pattern selection
3. Comprehensive validation and error handling
4. Security-aware code generation
5. Rich documentation generation
6. Modular, extensible architecture
"""

from openai import OpenAI
import json
import os
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError("OpenAI API key not found.")

client = OpenAI(api_key=API_KEY)


# ============================================================================
# ENHANCED TYPE DEFINITIONS
# ============================================================================

class ContractCategory(Enum):
    ERC20 = "ERC20"
    ERC721 = "ERC721"
    ERC1155 = "ERC1155"
    GOVERNANCE = "GOVERNANCE"
    CUSTOM = "CUSTOM"


class AccessControlType(Enum):
    SINGLE_OWNER = "single_owner"
    ROLE_BASED = "role_based"
    MULTI_SIG = "multi_sig"


class SecurityFeature(Enum):
    REENTRANCY_GUARD = "ReentrancyGuard"
    PAUSABLE = "Pausable"
    TIMELOCK = "TimelockController"
    RATE_LIMIT = "RateLimit"


@dataclass
class SpecCoverage:
    """Tracks how JSON spec items map to generated code"""
    state_variables: Dict[str, str] = field(default_factory=dict)  # name -> implementation note
    functions: Dict[str, str] = field(default_factory=dict)
    events: Dict[str, str] = field(default_factory=dict)
    roles: Dict[str, str] = field(default_factory=dict)
    modifiers: Dict[str, str] = field(default_factory=dict)
    unimplemented: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "state_variables": self.state_variables,
            "functions": self.functions,
            "events": self.events,
            "roles": self.roles,
            "modifiers": self.modifiers,
            "unimplemented": self.unimplemented
        }


@dataclass
class ContractProfile:
    """Detailed contract generation profile"""
    category: ContractCategory
    base_standard: str  # e.g., "ERC20", "ERC721Enumerable"
    extensions: List[str]  # e.g., ["Mintable", "Burnable", "Pausable"]
    access_control: AccessControlType
    security_features: List[SecurityFeature]
    supply_semantics: Optional[Dict] = None  # {"type": "capped", "cap": 1000000}
    
    def describe(self) -> str:
        """Human-readable profile description"""
        ext_str = ", ".join(self.extensions) if self.extensions else "None"
        sec_str = ", ".join([f.value for f in self.security_features]) if self.security_features else "None"
        return f"""
Profile: {self.category.value}
Base: {self.base_standard}
Extensions: {ext_str}
Access Control: {self.access_control.value}
Security Features: {sec_str}
Supply: {self.supply_semantics or 'Standard'}
"""


@dataclass
class GenerationResult:
    """Complete Stage 2 output with metadata"""
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
            "security_features": [f.value for f in self.profile.security_features],
            "coverage": self.coverage.to_dict(),
            "validation_errors": self.validation_errors,
            "security_summary": self.security_summary,
            "imports_used": self.imports_used,
            "inheritance_chain": self.inheritance_chain
        }


# ============================================================================
# ENHANCED PATTERN DEFINITIONS
# ============================================================================

TOKEN_PROFILES = {
    "erc20_basic": {
        "imports": [
            '@openzeppelin/contracts/token/ERC20/ERC20.sol',
            '@openzeppelin/contracts/access/Ownable.sol'
        ],
        "inheritance": ["ERC20", "Ownable"],
        "features": []
    },
    "erc20_mintable": {
        "imports": [
            '@openzeppelin/contracts/token/ERC20/ERC20.sol',
            '@openzeppelin/contracts/access/Ownable.sol'
        ],
        "inheritance": ["ERC20", "Ownable"],
        "features": ["Mintable"]
    },
    "erc20_burnable": {
        "imports": [
            '@openzeppelin/contracts/token/ERC20/ERC20.sol',
            '@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol',
            '@openzeppelin/contracts/access/Ownable.sol'
        ],
        "inheritance": ["ERC20", "ERC20Burnable", "Ownable"],
        "features": ["Burnable"]
    },
    "erc20_capped": {
        "imports": [
            '@openzeppelin/contracts/token/ERC20/ERC20.sol',
            '@openzeppelin/contracts/token/ERC20/extensions/ERC20Capped.sol',
            '@openzeppelin/contracts/access/Ownable.sol'
        ],
        "inheritance": ["ERC20", "ERC20Capped", "Ownable"],
        "features": ["Capped"]
    },
    "erc20_pausable": {
        "imports": [
            '@openzeppelin/contracts/token/ERC20/ERC20.sol',
            '@openzeppelin/contracts/security/Pausable.sol',
            '@openzeppelin/contracts/access/Ownable.sol'
        ],
        "inheritance": ["ERC20", "Pausable", "Ownable"],
        "features": ["Pausable"]
    }
}


# ============================================================================
# STAGE 2.1: COMPREHENSIVE VALIDATION
# ============================================================================

class SpecValidator:
    """Validates Stage 1 JSON specification"""
    
    REQUIRED_FIELDS = ["contract_name", "contract_type"]
    VALID_VISIBILITIES = {"public", "private", "internal", "external"}
    VALID_SOLIDITY_TYPES = {
        "uint", "uint8", "uint16", "uint32", "uint64", "uint128", "uint256",
        "int", "int8", "int16", "int32", "int64", "int128", "int256",
        "address", "bool", "string", "bytes", "bytes32"
    }
    
    @staticmethod
    def validate(json_spec: Dict) -> List[str]:
        """
        Validate JSON spec and return list of errors.
        Empty list means valid.
        """
        errors = []
        
        # Check required fields
        for field in SpecValidator.REQUIRED_FIELDS:
            if field not in json_spec or not json_spec[field]:
                errors.append(f"Missing required field: '{field}'")
        
        # Validate state variables
        for var in json_spec.get("state_variables", []):
            if "name" not in var or "type" not in var:
                errors.append(f"State variable missing 'name' or 'type': {var}")
            elif var.get("visibility") not in SpecValidator.VALID_VISIBILITIES:
                errors.append(f"Invalid visibility '{var.get('visibility')}' for variable '{var.get('name')}'")
            
            # Basic type validation
            var_type = var.get("type", "")
            if not SpecValidator._is_valid_type(var_type):
                errors.append(f"Potentially invalid Solidity type: '{var_type}' in variable '{var.get('name')}'")
        
        # Validate functions
        for func in json_spec.get("functions", []):
            if "name" not in func:
                errors.append(f"Function missing 'name': {func}")
            if func.get("visibility") not in SpecValidator.VALID_VISIBILITIES:
                errors.append(f"Invalid visibility for function '{func.get('name')}'")
            
            # Check role restrictions
            restricted_to = func.get("restricted_to")
            if restricted_to:
                roles = [r.get("name") for r in json_spec.get("roles", [])]
                if restricted_to not in roles and restricted_to != "owner":
                    errors.append(f"Function '{func.get('name')}' restricted to undefined role '{restricted_to}'")
        
        # Validate roles
        roles = json_spec.get("roles", [])
        if not roles:
            errors.append("Warning: No roles defined. Consider adding access control.")
        
        return errors
    
    @staticmethod
    def _is_valid_type(type_str: str) -> bool:
        """Check if type looks like valid Solidity"""
        # Remove array brackets and mapping syntax for basic check
        base_type = type_str.split('[')[0].split('(')[0].strip()
        
        if base_type in SpecValidator.VALID_SOLIDITY_TYPES:
            return True
        if base_type.startswith("mapping"):
            return True
        if base_type.startswith("uint") or base_type.startswith("int"):
            return True
        
        return False


# ============================================================================
# STAGE 2.2: INTELLIGENT PROFILE SELECTION
# ============================================================================

class ProfileSelector:
    """Selects optimal contract profile based on JSON spec"""
    
    @staticmethod
    def select_token_profile(json_spec: Dict) -> ContractProfile:
        """Select best ERC20 profile"""
        functions = json_spec.get("functions", [])
        func_names = {f.get("name", "").lower() for f in functions}
        roles = json_spec.get("roles", [])
        state_vars = json_spec.get("state_variables", [])
        
        # Detect features
        has_mint = "mint" in func_names
        has_burn = "burn" in func_names
        has_pause = "pause" in func_names or "unpause" in func_names
        
        # Detect supply cap
        supply_semantics = None
        for var in state_vars:
            if "cap" in var.get("name", "").lower() or "max" in var.get("name", "").lower():
                supply_semantics = {"type": "capped", "cap": var.get("initial_value")}
                break
        
        # Build profile
        extensions = []
        imports = set(TOKEN_PROFILES["erc20_basic"]["imports"])
        inheritance = ["ERC20"]
        security_features = []
        
        if has_mint:
            extensions.append("Mintable")
        
        if has_burn:
            extensions.append("Burnable")
            imports.update(TOKEN_PROFILES["erc20_burnable"]["imports"])
            inheritance.append("ERC20Burnable")
        
        if has_pause:
            extensions.append("Pausable")
            imports.update(TOKEN_PROFILES["erc20_pausable"]["imports"])
            inheritance.append("Pausable")
            security_features.append(SecurityFeature.PAUSABLE)
        
        if supply_semantics and supply_semantics["type"] == "capped":
            extensions.append("Capped")
            imports.update(TOKEN_PROFILES["erc20_capped"]["imports"])
            # Note: ERC20Capped goes before other extensions in inheritance
        
        # Access control
        access_control = AccessControlType.ROLE_BASED if len(roles) > 1 else AccessControlType.SINGLE_OWNER
        if access_control == AccessControlType.SINGLE_OWNER:
            inheritance.append("Ownable")
        else:
            imports.add('@openzeppelin/contracts/access/AccessControl.sol')
            inheritance.append("AccessControl")
        
        # Check for reentrancy-sensitive operations
        for func in functions:
            if func.get("payable") or "external" in func.get("description", "").lower():
                security_features.append(SecurityFeature.REENTRANCY_GUARD)
                imports.add('@openzeppelin/contracts/security/ReentrancyGuard.sol')
                inheritance.append("ReentrancyGuard")
                break
        
        base_standard = "ERC20"
        if "Capped" in extensions:
            base_standard = "ERC20Capped"
        elif "Burnable" in extensions:
            base_standard = "ERC20Burnable"
        
        return ContractProfile(
            category=ContractCategory.ERC20,
            base_standard=base_standard,
            extensions=extensions,
            access_control=access_control,
            security_features=security_features,
            supply_semantics=supply_semantics
        )
    
    @staticmethod
    def select_nft_profile(json_spec: Dict) -> ContractProfile:
        """Select best ERC721 profile"""
        functions = json_spec.get("functions", [])
        func_names = {f.get("name", "").lower() for f in functions}
        
        extensions = []
        imports = [
            '@openzeppelin/contracts/token/ERC721/ERC721.sol',
            '@openzeppelin/contracts/access/Ownable.sol'
        ]
        inheritance = ["ERC721", "Ownable"]
        
        # Detect enumerable
        if "tokenofownerbyindex" in func_names or "enumerate" in json_spec.get("description", "").lower():
            extensions.append("Enumerable")
            imports.append('@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol')
            inheritance.insert(1, "ERC721Enumerable")
        
        # Detect URI storage
        if "tokenuri" in func_names or "metadata" in json_spec.get("description", "").lower():
            extensions.append("URIStorage")
            imports.append('@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol')
            inheritance.insert(1, "ERC721URIStorage")
        
        return ContractProfile(
            category=ContractCategory.ERC721,
            base_standard="ERC721Enumerable" if "Enumerable" in extensions else "ERC721",
            extensions=extensions,
            access_control=AccessControlType.SINGLE_OWNER,
            security_features=[],
            supply_semantics=None
        )


# ============================================================================
# STAGE 2.3: COVERAGE MAPPING
# ============================================================================

class CoverageMapper:
    """Maps JSON spec to implementation details"""
    
    @staticmethod
    def map_specification(json_spec: Dict, profile: ContractProfile) -> SpecCoverage:
        """Create detailed coverage map"""
        coverage = SpecCoverage()
        
        # Map state variables
        for var in json_spec.get("state_variables", []):
            var_name = var.get("name")
            
            if profile.category == ContractCategory.ERC20:
                if var_name in ["name", "symbol"]:
                    coverage.state_variables[var_name] = f"Implemented via ERC20 constructor"
                elif var_name == "totalSupply":
                    coverage.state_variables[var_name] = f"Dynamic via ERC20.totalSupply()"
                elif var_name == "balances":
                    coverage.state_variables[var_name] = f"Internal ERC20 mapping"
                elif var_name == "owner":
                    coverage.state_variables[var_name] = f"Via Ownable.owner()"
                else:
                    coverage.state_variables[var_name] = f"Custom state variable"
            else:
                coverage.state_variables[var_name] = f"Custom implementation"
        
        # Map functions
        for func in json_spec.get("functions", []):
            func_name = func.get("name")
            
            if profile.category == ContractCategory.ERC20:
                if func_name in ["transfer", "transferFrom", "approve", "balanceOf", "allowance"]:
                    coverage.functions[func_name] = f"Inherited from ERC20"
                elif func_name == "mint":
                    coverage.functions[func_name] = f"Custom mint() with {profile.access_control.value} restriction"
                elif func_name == "burn":
                    coverage.functions[func_name] = f"Via ERC20Burnable.burn()" if "Burnable" in profile.extensions else "Custom burn()"
                else:
                    coverage.functions[func_name] = f"Custom function"
            else:
                coverage.functions[func_name] = f"Custom implementation"
        
        # Map events
        for event in json_spec.get("events", []):
            event_name = event.get("name")
            if event_name in ["Transfer", "Approval"]:
                coverage.events[event_name] = f"Automatic via ERC20"
            else:
                coverage.events[event_name] = f"Custom event"
        
        # Map roles
        for role in json_spec.get("roles", []):
            role_name = role.get("name")
            if role_name == "owner" and profile.access_control == AccessControlType.SINGLE_OWNER:
                coverage.roles[role_name] = f"Via Ownable"
            else:
                coverage.roles[role_name] = f"Via AccessControl role constant"
        
        return coverage


# ============================================================================
# STAGE 2.4: ENHANCED CODE GENERATION
# ============================================================================

def generate_enhanced_prompt(json_spec: Dict, profile: ContractProfile, coverage: SpecCoverage) -> Tuple[str, str]:
    """Generate system and user prompts with full context.

    IMPORTANT: This function uses ONLY the JSON specification from Stage 1.
    No original user input is needed or used.

    The prompts are written to strongly bias the model towards returning a
    single, self-contained Solidity file that **compiles without syntax
    errors** under Solidity ^0.8.20 (e.g. in Remix).

    Args:
        json_spec: Structured JSON from Stage 1 intent extraction
        profile: Selected contract profile
        coverage: Specification coverage mapping

    Returns:
        Tuple of (system_prompt, user_prompt)
    """

    system_prompt = f"""You are an expert Solidity smart contract developer specializing in secure, production-ready code.

Your PRIMARY objective is to output Solidity that **compiles without any
syntax errors** under Solidity ^0.8.20 (for example in Remix) while following
best practices.

GENERATION PROFILE:
{profile.describe()}

REQUIREMENTS:
1. Use Solidity ^0.8.20
2. Follow OpenZeppelin best practices
3. Implement comprehensive NatSpec documentation
4. Use custom errors instead of require strings
5. Follow checks-effects-interactions pattern
6. Emit events for all state changes
7. Optimize for gas efficiency
8. Ensure the output is a single, self-contained, compilable Solidity contract
   with no Markdown fences or extraneous text.

CATEGORY-SPECIFIC RULES ({profile.category.value}):
"""
    
    if profile.category == ContractCategory.ERC20:
        system_prompt += """
- MUST inherit from specified OpenZeppelin contracts
- DO NOT reimplement inherited functions (transfer, balanceOf, etc.)
- Use _mint() and _burn() internal functions
- Constructor MUST call base constructors properly
- Only implement custom/extended functionality
"""
    elif profile.category == ContractCategory.ERC721:
        system_prompt += """
- MUST inherit from specified OpenZeppelin contracts
- DO NOT reimplement inherited functions (transferFrom, ownerOf, etc.)
- Use _safeMint() for minting tokens
- Constructor MUST call base constructors properly
- Implement custom metadata/tokenURI logic as needed
"""
    elif profile.category == ContractCategory.ERC1155:
        system_prompt += """
- MUST inherit from OpenZeppelin ERC1155 contracts
- Use _mint() and _mintBatch() for minting
- DO NOT reimplement safeTransferFrom/safeBatchTransferFrom
- Constructor MUST call base constructors properly
"""
    
    system_prompt += f"""

ACCESS CONTROL ({profile.access_control.value}):
"""
    
    if profile.access_control == AccessControlType.SINGLE_OWNER:
        system_prompt += """- Use Ownable pattern
- Restricted functions use onlyOwner modifier
- Constructor automatically sets deployer as owner
"""
    else:
        system_prompt += """- Use AccessControl pattern
- Define role constants with keccak256
- Grant DEFAULT_ADMIN_ROLE to deployer in constructor
- Use onlyRole or hasRole for restrictions
"""
    
    if profile.security_features:
        system_prompt += f"\nSECURITY FEATURES:\n"
        for feature in profile.security_features:
            system_prompt += f"- Include {feature.value}\n"
    
    # Build imports list from profile
    imports_list = []
    if profile.category == ContractCategory.ERC20:
        imports_list.append('@openzeppelin/contracts/token/ERC20/ERC20.sol')
        if "Burnable" in profile.extensions:
            imports_list.append('@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol')
        if "Capped" in profile.extensions:
            imports_list.append('@openzeppelin/contracts/token/ERC20/extensions/ERC20Capped.sol')
        if "Pausable" in profile.extensions:
            imports_list.append('@openzeppelin/contracts/security/Pausable.sol')
    elif profile.category == ContractCategory.ERC721:
        imports_list.append('@openzeppelin/contracts/token/ERC721/ERC721.sol')
        if "Enumerable" in profile.extensions:
            imports_list.append('@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol')
        if "URIStorage" in profile.extensions:
            imports_list.append('@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol')
    
    # Add access control import
    if profile.access_control == AccessControlType.SINGLE_OWNER:
        imports_list.append('@openzeppelin/contracts/access/Ownable.sol')
    else:
        imports_list.append('@openzeppelin/contracts/access/AccessControl.sol')
    
    # Add security feature imports
    if SecurityFeature.REENTRANCY_GUARD in profile.security_features:
        imports_list.append('@openzeppelin/contracts/security/ReentrancyGuard.sol')
    
    # Build inheritance chain
    inheritance_parts = []
    if profile.category == ContractCategory.ERC20:
        inheritance_parts.append("ERC20")
        if "Burnable" in profile.extensions:
            inheritance_parts.append("ERC20Burnable")
        if "Capped" in profile.extensions:
            inheritance_parts.append("ERC20Capped")
        if "Pausable" in profile.extensions:
            inheritance_parts.append("Pausable")
    elif profile.category == ContractCategory.ERC721:
        inheritance_parts.append("ERC721")
        if "Enumerable" in profile.extensions:
            inheritance_parts.append("ERC721Enumerable")
        if "URIStorage" in profile.extensions:
            inheritance_parts.append("ERC721URIStorage")
    
    # Add access control to inheritance
    if profile.access_control == AccessControlType.SINGLE_OWNER:
        inheritance_parts.append("Ownable")
    else:
        inheritance_parts.append("AccessControl")
    
    # Add security features to inheritance
    if SecurityFeature.REENTRANCY_GUARD in profile.security_features:
        inheritance_parts.append("ReentrancyGuard")
    
    # User prompt with ONLY Stage 1 JSON specification
    coverage_summary = json.dumps({
        "state_variables": coverage.state_variables,
        "functions": coverage.functions,
        "events": coverage.events,
        "roles": coverage.roles
    }, indent=2)
    
    imports_str = '\n'.join(f'import "{imp}";' for imp in imports_list)
    inheritance_str = ', '.join(inheritance_parts)
    
    user_prompt = f"""Generate a complete Solidity smart contract based on the following Stage 1 specification.
The output MUST be valid Solidity code that compiles under Solidity ^0.8.20
(e.g. in Remix) **without any syntax errors**. Do not include Markdown code
fences or explanations, only the Solidity source.

STAGE 1 JSON SPECIFICATION:
{json.dumps(json_spec, indent=2)}

IMPLEMENTATION MAPPING (how spec maps to code):
{coverage_summary}

REQUIRED IMPORTS:
{imports_str}

CONTRACT DECLARATION:
contract {json_spec.get('contract_name', 'GeneratedContract')} is {inheritance_str}

IMPLEMENTATION REQUIREMENTS:
1. Follow the profile specifications exactly ({profile.base_standard})
2. Implement ALL custom functions listed in the specification
3. DO NOT reimplement inherited functions (they come from base contracts)
4. Include comprehensive NatSpec documentation for contract and all custom functions
5. Use custom errors for all validations (not require strings)
6. Add security checks: zero address validation, zero amount checks, etc.
7. Emit appropriate events for all state-changing operations
8. Constructor must properly initialize all base contracts
9. Use appropriate access control modifiers for restricted functions

WHAT TO IMPLEMENT:
- Custom functions not provided by base contracts
- Custom events if specified and not covered by base contracts
- Proper constructor with base contract initialization
- Custom state variables only if needed beyond base contracts
- Access control setup (owner assignment or role grants)

WHAT NOT TO IMPLEMENT:
- Standard ERC20/ERC721 functions (transfer, balanceOf, etc.) - these are inherited
- Standard events (Transfer, Approval) - these are automatic from base contracts

Output ONLY the complete, ready-to-deploy Solidity contract code. No explanations or comments outside the code."""
    
    return system_prompt, user_prompt


# ============================================================================
# STAGE 2.5: POST-PROCESSING & SELF-CHECK REPAIR
# ============================================================================

def _strip_markdown_fences(solidity_code: str) -> str:
    """Remove common Markdown code fences from the model output."""
    code = solidity_code.strip()
    if code.startswith("```solidity"):
        code = code[len("```solidity"):]
    if code.startswith("```"):
        code = code[len("```"):]
    if code.endswith("```"):
        code = code[: -len("```")]
    return code.strip()


def _ensure_headers(solidity_code: str) -> str:
    """Normalize SPDX + pragma at the very top, exactly once."""
    code = solidity_code.strip()
    code = code.replace("\r\n", "\n").replace("\r", "\n")

    lines = code.split("\n")
    body_lines = []

    for line in lines:
        stripped = line.strip()
        # Drop any existing SPDX or pragma lines anywhere in the file
        if stripped.startswith("// SPDX-License-Identifier"):
            continue
        if stripped.startswith("pragma solidity"):
            continue
        body_lines.append(line)

    header = [
        "// SPDX-License-Identifier: MIT",
        "pragma solidity ^0.8.20;",
        "",
    ]

    normalized = "\n".join(header + body_lines).strip() + "\n"
    return normalized

def _repair_with_model_if_needed(solidity_code: str) -> str:
    """Use a second, strict pass to fix syntax issues."""

    
    system = (
        "You are a strict Solidity compiler and formatter. "
        "Return Solidity that compiles under ^0.8.20 with OpenZeppelin v5. "
        "Fix ONLY syntax, inheritance, and constructor issues. "
        "If the contract inherits from Ownable, replace `Ownable()` with "
        "`Ownable(msg.sender)` because OZ v5 requires an initialOwner. "
        "If the contract inherits from ERC20, ensure the constructor calls "
        "ERC20(name, symbol). Insert correct initializer lists automatically. "
        "Output ONLY the corrected Solidity file, no Markdown, no commentary."
    )


    user = (
        "Here is a Solidity contract that may contain syntax or constructor "
        "errors. Return a fixed version that compiles under Solidity ^0.8.20, "
        "preserving the same structure and intent as much as possible:\n\n"
        + solidity_code
    )

    resp = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.0,
    )

    fixed = resp.choices[0].message.content or ""
    fixed = _strip_markdown_fences(fixed)
    fixed = _ensure_headers(fixed)
    return fixed

def generate_solidity_v3(json_spec: Dict) -> GenerationResult:
    """
    Enhanced Stage 2 with validation, profiling, and coverage tracking.
    """
    print("=" * 80)
    print("ENHANCED STAGE 2: SMART CONTRACT GENERATION")
    print("=" * 80)
    
    # Step 1: Validation
    print("\n[1/6] Validating specification...")
    validation_errors = SpecValidator.validate(json_spec)
    
    if validation_errors:
        print(f"⚠️  Found {len(validation_errors)} validation issues:")
        for error in validation_errors[:5]:  # Show first 5
            print(f"    • {error}")
        if len(validation_errors) > 5:
            print(f"    ... and {len(validation_errors) - 5} more")
    else:
        print("✓ Specification valid")
    
    # Step 2: Profile Selection
    print("\n[2/6] Selecting contract profile...")
    contract_type = json_spec.get("contract_type", "").upper()
    
    if "ERC20" in contract_type or "TOKEN" in contract_type:
        profile = ProfileSelector.select_token_profile(json_spec)
    elif "ERC721" in contract_type or "NFT" in contract_type:
        profile = ProfileSelector.select_nft_profile(json_spec)
    else:
        # Default custom profile
        profile = ContractProfile(
            category=ContractCategory.CUSTOM,
            base_standard="Custom",
            extensions=[],
            access_control=AccessControlType.SINGLE_OWNER,
            security_features=[]
        )
    
    print(f"✓ Profile selected: {profile.base_standard}")
    print(f"  Extensions: {', '.join(profile.extensions) or 'None'}")
    print(f"  Security: {', '.join(f.value for f in profile.security_features) or 'None'}")
    
    # Step 3: Coverage Mapping
    print("\n[3/6] Mapping specification to implementation...")
    coverage = CoverageMapper.map_specification(json_spec, profile)
    print(f"✓ Mapped {len(coverage.state_variables)} state variables")
    print(f"✓ Mapped {len(coverage.functions)} functions")
    print(f"✓ Mapped {len(coverage.events)} events")
    
    # Step 4: Generate Code
    print("\n[4/6] Generating Solidity code...")
    system_prompt, user_prompt = generate_enhanced_prompt(json_spec, profile, coverage)
    
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2,
    )

    solidity_code = response.choices[0].message.content
    if not solidity_code:
        raise RuntimeError("No content returned from model")

    # First-pass cleanup: strip Markdown fences and normalize headers
    solidity_code = _strip_markdown_fences(solidity_code)
    solidity_code = _ensure_headers(solidity_code)

    # Second-pass repair: ask model to fix any remaining syntax issues
    print("  ↪ Running syntax-repair pass...")
    solidity_code = _repair_with_model_if_needed(solidity_code)

    print("✓ Code generated")
    
    # Step 5: Security Summary
    print("\n[5/6] Generating security summary...")
    security_summary = f"""Security Analysis:
- Access Control: {profile.access_control.value}
- Security Features: {', '.join(f.value for f in profile.security_features) or 'Standard OpenZeppelin protections'}
- Overflow Protection: Built-in Solidity ^0.8.20
- Reentrancy: {'Protected with ReentrancyGuard' if SecurityFeature.REENTRANCY_GUARD in profile.security_features else 'No external calls detected'}
- Pausability: {'Implemented' if SecurityFeature.PAUSABLE in profile.security_features else 'Not required'}
"""
    print(security_summary)
    
    # Step 6: Build Result
    print("\n[6/6] Finalizing generation result...")
    
    imports_used = []
    if profile.category == ContractCategory.ERC20:
        imports_used = list(TOKEN_PROFILES["erc20_basic"]["imports"])
        if "Burnable" in profile.extensions:
            imports_used.extend(TOKEN_PROFILES["erc20_burnable"]["imports"])
        if "Pausable" in profile.extensions:
            imports_used.extend(TOKEN_PROFILES["erc20_pausable"]["imports"])
    
    inheritance = [profile.base_standard]
    if profile.extensions:
        inheritance.extend([f"ERC20{ext}" for ext in profile.extensions if ext != "Mintable"])
    inheritance.append(profile.access_control.value.replace("_", "").title())
    
    result = GenerationResult(
        solidity_code=solidity_code,
        profile=profile,
        coverage=coverage,
        validation_errors=validation_errors,
        security_summary=security_summary,
        imports_used=list(set(imports_used)),
        inheritance_chain=inheritance
    )
    
    print("\n✅ GENERATION COMPLETE")
    print("=" * 80)
    
    return result

