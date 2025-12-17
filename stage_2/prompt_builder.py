# solidity_code_generator/prompt_builder.py
import json
from typing import Dict, List, Tuple
from .categories import ContractProfile, ContractCategory, SpecCoverage, AccessControlType, SecurityFeature

_CATEGORY_RULES = {
    ContractCategory.STAKING: """STAKING: Use SafeERC20 + ReentrancyGuard, track stakes, emit events, provide emergencyWithdraw, setRewardRate onlyOwner.""",
    ContractCategory.VAULT: """VAULT: Prefer ERC4626, implement deposit/withdraw, use SafeERC20.""",
    ContractCategory.GOVERNANCE: """GOVERNANCE: Inherit Governor + extensions, implement votingDelay/votingPeriod/proposalThreshold/quorum.""",
    ContractCategory.NFT_MARKETPLACE: """MARKETPLACE: Use ReentrancyGuard, listings mapping, royalties (ERC2981) support.""",
    ContractCategory.AUCTION: """AUCTION: ReentrancyGuard, pull refunds, auction lifecycle functions.""",
    ContractCategory.ERC721: """ERC721 RENTAL PATTERN:
- MUST have mint/safeMint function (onlyOwner) - NFTs must be minted before rental
- Use actual token transfers (_transfer or transferFrom) for rental, NOT just state variables
- rental functions (rentNFT) should be payable if they accept ETH payments
- Track rental metadata in separate mapping (startTime, duration, originalOwner)
- Use ERC721.ownerOf() for ownership checks - DO NOT create redundant owner state variables
- Return/reclaim functions should transfer NFT back to original owner
- Constructor: ERC721("name", "symbol") Ownable(msg.sender)""",
}

# OpenZeppelin v5 specific guidance
OZ_V5_RULES = """
OPENZEPPELIN V5 CRITICAL RULES:
1. _beforeTokenTransfer and _afterTokenTransfer hooks are REMOVED
   - Override _update(address from, address to, uint256 value) instead
   - All transfer customization must happen in _update
   
2. Ownable constructor REQUIRES initialOwner parameter
   - Constructor must be: constructor(...) Ownable(msg.sender) {...}
   - Or pass a specific address: Ownable(initialOwner)
   
3. Use AccessControl for role-based permissions (not custom modifiers)
   - Define roles: bytes32 public constant ROLE_NAME = keccak256("ROLE_NAME");
   - Grant in constructor: _grantRole(DEFAULT_ADMIN_ROLE, owner);
   - Use modifier: onlyRole(ROLE_NAME)
   
4. Use custom errors (not require strings)
   - Define: error InvalidAddress();
   - Use: if (addr == address(0)) revert InvalidAddress();
   
5. SafeERC20 for all ERC20 token interactions
   - import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
   - using SafeERC20 for IERC20;
"""

def _build_imports(profile: ContractProfile) -> List[str]:
    imports = []
    if profile.category == ContractCategory.ERC20:
        imports.append("@openzeppelin/contracts/token/ERC20/ERC20.sol")
        if "Burnable" in profile.extensions:
            imports.append("@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol")
        if "Capped" in profile.extensions:
            imports.append("@openzeppelin/contracts/token/ERC20/extensions/ERC20Capped.sol")
        if "Pausable" in profile.extensions:
            imports.append("@openzeppelin/contracts/utils/Pausable.sol")  # Changed path for v5
        if "Snapshot" in profile.extensions:
            imports.append("@openzeppelin/contracts/token/ERC20/extensions/ERC20Snapshot.sol")
        if "Votes" in profile.extensions:
            imports.append("@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol")
        if "Permit" in profile.extensions:
            imports.append("@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol")
    elif profile.category == ContractCategory.ERC721:
        imports.append("@openzeppelin/contracts/token/ERC721/ERC721.sol")
        if "URIStorage" in profile.extensions:
            imports.append("@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol")
        if "Enumerable" in profile.extensions:
            imports.append("@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol")
    elif profile.category == ContractCategory.STAKING:
        imports.extend([
            "@openzeppelin/contracts/token/ERC20/IERC20.sol",
            "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol",
            "@openzeppelin/contracts/utils/ReentrancyGuard.sol",  # Changed path for v5
        ])
    elif profile.category == ContractCategory.VAULT:
        if profile.base_standard == "ERC4626":
            imports.extend([
                "@openzeppelin/contracts/token/ERC20/ERC20.sol",
                "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol"
            ])
        imports.append("@openzeppelin/contracts/utils/ReentrancyGuard.sol")
    elif profile.category == ContractCategory.GOVERNANCE:
        imports.extend([
            "@openzeppelin/contracts/governance/Governor.sol",
            "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol",
            "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol",
            "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol",
        ])
    
    # Access control imports
    if profile.access_control == AccessControlType.SINGLE_OWNER:
        imports.append("@openzeppelin/contracts/access/Ownable.sol")
    else:
        imports.append("@openzeppelin/contracts/access/AccessControl.sol")
    
    # Security feature imports
    if SecurityFeature.REENTRANCY_GUARD in profile.security_features:
        if "@openzeppelin/contracts/utils/ReentrancyGuard.sol" not in imports:
            imports.append("@openzeppelin/contracts/utils/ReentrancyGuard.sol")
    
    # Dedupe preserving order
    seen = set()
    dedup = []
    for i in imports:
        if i not in seen:
            seen.add(i)
            dedup.append(i)
    return dedup

def _build_inheritance(profile: ContractProfile) -> List[str]:
    parts = []
    if profile.category == ContractCategory.ERC20:
        parts.append("ERC20")
        if "Burnable" in profile.extensions:
            parts.append("ERC20Burnable")
        if "Pausable" in profile.extensions:
            parts.append("Pausable")
        # Note: Capped is handled differently in constructor
    elif profile.category == ContractCategory.ERC721:
        parts.append("ERC721")
        if "Enumerable" in profile.extensions:
            parts.append("ERC721Enumerable")
        if "URIStorage" in profile.extensions:
            parts.append("ERC721URIStorage")
    elif profile.category == ContractCategory.STAKING:
        parts.append("ReentrancyGuard")
    elif profile.category == ContractCategory.VAULT:
        if profile.base_standard == "ERC4626":
            parts.append("ERC4626")
        parts.append("ReentrancyGuard")
    elif profile.category == ContractCategory.GOVERNANCE:
        parts.extend(["Governor", "GovernorSettings", "GovernorVotes", "GovernorVotesQuorumFraction"])
    
    # Access control
    if profile.access_control == AccessControlType.SINGLE_OWNER:
        parts.append("Ownable")
    else:
        parts.append("AccessControl")
    
    # Security features
    if SecurityFeature.REENTRANCY_GUARD in profile.security_features and "ReentrancyGuard" not in parts:
        parts.append("ReentrancyGuard")
    
    return parts

def build_prompts(json_spec: Dict, profile: ContractProfile, coverage: SpecCoverage) -> Tuple[str, str, List[str], List[str]]:
    """Build system and user prompts with enhanced OpenZeppelin v5 guidance"""
    
    # Enhanced system prompt with v5 specifics
    system_prompt = f"""You are an expert Solidity developer specializing in OpenZeppelin v5 contracts.

TARGET: Solidity ^0.8.20 with OpenZeppelin v5

{OZ_V5_RULES}

PROFILE:
{profile.describe()}

GENERAL REQUIREMENTS:
- Use natSpec documentation for all public functions
- Use custom errors (not require strings)
- Follow checks-effects-interactions pattern
- Emit events for all state changes
- Optimize for gas efficiency
- Single-file output only
- NO explanations, ONLY Solidity code"""

    # Add category-specific rules
    if profile.category in _CATEGORY_RULES:
        system_prompt += "\n\nCATEGORY-SPECIFIC RULES:\n" + _CATEGORY_RULES[profile.category]
    
    # Add ERC20 specific guidance
    if profile.category == ContractCategory.ERC20:
        system_prompt += """

ERC20 IMPLEMENTATION RULES:
- Inherit from OpenZeppelin ERC20 base contract
- DO NOT reimplement transfer, balanceOf, approve, etc.
- Custom logic goes in _update override
- Constructor must call ERC20(name, symbol) and Ownable(initialOwner)
- For minting: implement mint() with access control
- For burning: inherit ERC20Burnable or implement custom burn
- For transfer restrictions: override _update function"""

    # Add ERC721 specific guidance (especially for rentals)
    if profile.category == ContractCategory.ERC721:
        system_prompt += """

ERC721 IMPLEMENTATION RULES:
- MUST implement mint/safeMint function if managing NFTs (onlyOwner)
- Use actual token transfers (_transfer) for ownership changes, NOT just state variables
- For rental systems:
  * rentNFT() should be payable if accepting ETH payments
  * Use _transfer(owner, renter, tokenId) to change ownership
  * Track rental metadata separately (mapping(uint256 => Rental))
  * Use ownerOf(tokenId) for ownership checks - DO NOT create redundant owner variables
- Constructor: ERC721("name", "symbol") Ownable(msg.sender)"""

    # Build imports and inheritance
    imports = _build_imports(profile)
    inheritance = _build_inheritance(profile)
    
    # Coverage summary
    coverage_summary = json.dumps({
        "state_variables": coverage.state_variables,
        "functions": coverage.functions,
        "events": coverage.events,
        "roles": coverage.roles,
    }, indent=2)
    
    # Format imports
    imports_str = "\n".join(f'import "{i}";' for i in imports)
    inheritance_str = ", ".join(inheritance) if inheritance else "Ownable"
    
    # Build user prompt with examples
    contract_name = json_spec.get('contract_name', 'GeneratedContract')
    
    user_prompt = f"""Generate a complete, compilable Solidity contract file.

SPECIFICATION FROM STAGE 1:
{json.dumps(json_spec, indent=2)}

IMPLEMENTATION MAPPING:
{coverage_summary}

REQUIRED STRUCTURE:

// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

{imports_str}

contract {contract_name} is {inheritance_str} {{
    // Custom errors
    // State variables
    // Events
    
    // Constructor with proper OpenZeppelin v5 initialization
    constructor(...) ERC20("name", "symbol") Ownable(msg.sender) {{
        // initialization
    }}
    
    // Custom functions from spec
    // Override _update if needed for transfer logic
}}

CRITICAL REQUIREMENTS:
1. If Ownable is inherited: constructor must pass initialOwner (use msg.sender or add parameter)
2. If ERC20/ERC721 is inherited: use _update override for transfer customization, NOT _beforeTokenTransfer
3. For roles: use AccessControl with proper role definitions and grants
4. All external/public functions need natSpec comments
5. Use custom errors exclusively (no require strings)
6. Emit events for all state changes

OUTPUT: Only the complete Solidity source code, no markdown fences, no explanations."""

    return system_prompt, user_prompt, imports, inheritance