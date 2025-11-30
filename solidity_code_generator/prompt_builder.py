"""Prompt construction for Stage 2 Solidity generation.

Takes:
- Stage 1 JSON spec
- ContractProfile selected from the spec
- SpecCoverage mapping

and returns:
- system_prompt
- user_prompt
- imports_used (list of OpenZeppelin imports to mention)
- inheritance_chain (base contracts to inherit from)
"""

from __future__ import annotations

import json
from typing import Dict, List, Tuple

from .categories import ContractProfile, ContractCategory, AccessControlType, SecurityFeature, SpecCoverage


# ---------------------------------------------------------------------------
# Category-specific high-level generation rules
# ---------------------------------------------------------------------------

_CATEGORY_RULES = {
    ContractCategory.STAKING: """
STAKING CONTRACT REQUIREMENTS:
- Use SafeERC20 for all token transfers: `using SafeERC20 for IERC20;`
- Protect stake/unstake/claim functions with nonReentrant modifier
- Track user stakes: struct UserStake { uint256 amount; uint256 rewardDebt; uint256 timestamp; }
- Calculate rewards: pendingReward = (user.amount * accRewardPerShare / 1e12) - user.rewardDebt
- Emit events: Staked(user, amount), Unstaked(user, amount), RewardsClaimed(user, amount)
- Implement emergencyWithdraw() without rewards
- Provide owner functions: setRewardRate, pause/unpause, recoverERC20
""",
    ContractCategory.VAULT: """
VAULT CONTRACT REQUIREMENTS:
- Prefer ERC4626 standard if base_standard is ERC4626
- Implement: deposit, withdraw, redeem, mint (or minimal subset if custom)
- Use SafeERC20 for asset transfers
- Implement totalAssets(), convertToShares(), convertToAssets()
- Emit standard Deposit/Withdraw style events with caller/owner/assets/shares
- Protect state-changing functions with nonReentrant
""",
    ContractCategory.GOVERNANCE: """
GOVERNANCE CONTRACT REQUIREMENTS:
- Inherit from OpenZeppelin Governor + extensions (GovernorSettings, GovernorVotes, GovernorVotesQuorumFraction)
- Implement required virtuals: votingDelay(), votingPeriod(), proposalThreshold(), quorum(uint256)
- Use an ERC20Votes-compatible token for voting power
- Use Governor's built-in propose/castVote/execute flows
- Integrate TimelockController for execution if security_features include TimelockController
""",
    ContractCategory.NFT_MARKETPLACE: """
NFT MARKETPLACE REQUIREMENTS:
- Use ReentrancyGuard on all purchase/offer functions
- Track listings: struct Listing { address seller; uint256 price; bool isActive; }
- Use mapping(address => mapping(uint256 => Listing)) listings for (nftContract, tokenId)
- Implement listItem, buyItem, cancelListing functions
- Support marketplace fee and optional ERC2981 royalties
- Validate NFT ownership and approvals before listing/sale
- Emit: ItemListed, ItemSold, ListingCanceled
""",
    ContractCategory.AUCTION: """
AUCTION CONTRACT REQUIREMENTS:
- Use ReentrancyGuard and pull-payment pattern for refunds
- Track auctions: struct Auction { address seller; address highestBidder; uint256 highestBid; uint256 endTime; bool ended; }
- Implement createAuction, bid, endAuction, withdrawRefund
- Enforce minimum bid increments and auction end time
- Transfer NFT and funds only when auction successfully ends
- Emit: AuctionCreated, NewBid, AuctionEnded
""",
}


def _build_imports(profile: ContractProfile) -> List[str]:
    """Derive OpenZeppelin imports from the ContractProfile.

    This is intentionally approximate; the repair step will fix minor
    inconsistencies if needed.
    """

    imports: List[str] = []

    if profile.category == ContractCategory.ERC20:
        imports.append("@openzeppelin/contracts/token/ERC20/ERC20.sol")
        # Advanced extensions
        if "Burnable" in profile.extensions:
            imports.append("@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol")
        if "Capped" in profile.extensions:
            imports.append("@openzeppelin/contracts/token/ERC20/extensions/ERC20Capped.sol")
        if "Pausable" in profile.extensions:
            imports.append("@openzeppelin/contracts/security/Pausable.sol")
        if "Snapshot" in profile.extensions:
            imports.append("@openzeppelin/contracts/token/ERC20/extensions/ERC20Snapshot.sol")
        if "Votes" in profile.extensions:
            imports.append("@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol")
        if "Permit" in profile.extensions:
            imports.append("@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol")
        if "FlashMint" in profile.extensions:
            imports.append("@openzeppelin/contracts/token/ERC20/extensions/ERC20FlashMint.sol")

    elif profile.category == ContractCategory.ERC721:
        imports.append("@openzeppelin/contracts/token/ERC721/ERC721.sol")
        if "Enumerable" in profile.extensions:
            imports.append("@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol")
        if "URIStorage" in profile.extensions:
            imports.append("@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol")
        if "Royalty" in profile.extensions:
            imports.append("@openzeppelin/contracts/token/common/ERC2981.sol")
        if "Burnable" in profile.extensions:
            imports.append("@openzeppelin/contracts/token/ERC721/extensions/ERC721Burnable.sol")

    elif profile.category == ContractCategory.STAKING:
        imports.extend([
            "@openzeppelin/contracts/token/ERC20/IERC20.sol",
            "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol",
            "@openzeppelin/contracts/security/ReentrancyGuard.sol",
        ])

    elif profile.category == ContractCategory.VAULT:
        imports.append("@openzeppelin/contracts/token/ERC20/IERC20.sol")
        if profile.base_standard == "ERC4626":
            imports.extend([
                "@openzeppelin/contracts/token/ERC20/ERC20.sol",
                "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol",
            ])
        imports.append("@openzeppelin/contracts/security/ReentrancyGuard.sol")

    elif profile.category == ContractCategory.GOVERNANCE:
        imports.extend([
            "@openzeppelin/contracts/governance/Governor.sol",
            "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol",
            "@openzeppelin/contracts/governance/extensions/GovernorCountingSimple.sol",
            "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol",
            "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol",
        ])

    elif profile.category == ContractCategory.NFT_MARKETPLACE:
        imports.extend([
            "@openzeppelin/contracts/token/ERC721/IERC721.sol",
            "@openzeppelin/contracts/token/ERC20/IERC20.sol",
            "@openzeppelin/contracts/security/ReentrancyGuard.sol",
            "@openzeppelin/contracts/interfaces/IERC2981.sol",
        ])

    elif profile.category == ContractCategory.AUCTION:
        imports.extend([
            "@openzeppelin/contracts/token/ERC721/IERC721.sol",
            "@openzeppelin/contracts/security/ReentrancyGuard.sol",
        ])

    # Access control imports
    if profile.access_control == AccessControlType.SINGLE_OWNER:
        imports.append("@openzeppelin/contracts/access/Ownable.sol")
    else:
        imports.append("@openzeppelin/contracts/access/AccessControl.sol")

    # Security feature imports
    if SecurityFeature.REENTRANCY_GUARD in profile.security_features:
        imports.append("@openzeppelin/contracts/security/ReentrancyGuard.sol")

    # Deduplicate while preserving order
    seen = set()
    deduped: List[str] = []
    for imp in imports:
        if imp not in seen:
            seen.add(imp)
            deduped.append(imp)

    return deduped


def _build_inheritance(profile: ContractProfile) -> List[str]:
    """Derive inheritance chain from profile.

    This is high-level; the repair step can fix minor ordering issues.
    """

    parts: List[str] = []

    if profile.category == ContractCategory.ERC20:
        parts.append("ERC20")
        if "Burnable" in profile.extensions:
            parts.append("ERC20Burnable")
        if "Capped" in profile.extensions:
            parts.append("ERC20Capped")
        if "Pausable" in profile.extensions:
            parts.append("Pausable")
        if "Snapshot" in profile.extensions:
            parts.append("ERC20Snapshot")
        if "Votes" in profile.extensions:
            parts.append("ERC20Votes")
        if "Permit" in profile.extensions:
            parts.append("ERC20Permit")
        if "FlashMint" in profile.extensions:
            parts.append("ERC20FlashMint")

    elif profile.category == ContractCategory.ERC721:
        parts.append("ERC721")
        if "Enumerable" in profile.extensions:
            parts.append("ERC721Enumerable")
        if "URIStorage" in profile.extensions:
            parts.append("ERC721URIStorage")
        if "Royalty" in profile.extensions:
            parts.append("ERC2981")
        if "Burnable" in profile.extensions:
            parts.append("ERC721Burnable")

    elif profile.category == ContractCategory.STAKING:
        parts.append("ReentrancyGuard")

    elif profile.category == ContractCategory.VAULT:
        if profile.base_standard == "ERC4626":
            parts.append("ERC4626")
        parts.append("ReentrancyGuard")

    elif profile.category == ContractCategory.GOVERNANCE:
        parts.extend([
            "Governor",
            "GovernorSettings",
            "GovernorCountingSimple",
            "GovernorVotes",
            "GovernorVotesQuorumFraction",
        ])

    elif profile.category == ContractCategory.NFT_MARKETPLACE:
        parts.append("ReentrancyGuard")

    elif profile.category == ContractCategory.AUCTION:
        parts.append("ReentrancyGuard")

    # Access control base
    if profile.access_control == AccessControlType.SINGLE_OWNER:
        parts.append("Ownable")
    else:
        parts.append("AccessControl")

    # Security base
    if SecurityFeature.REENTRANCY_GUARD in profile.security_features and "ReentrancyGuard" not in parts:
        parts.append("ReentrancyGuard")

    return parts


def build_prompts(
    json_spec: Dict,
    profile: ContractProfile,
    coverage: SpecCoverage,
) -> Tuple[str, str, List[str], List[str]]:
    """Build (system_prompt, user_prompt, imports, inheritance_chain).

    The prompts are written to strongly bias the model towards returning a
    single, compilable Solidity file without Markdown fences.
    """

    system_prompt = f"""You are an expert Solidity smart contract developer specializing in secure, production-ready code.

Your PRIMARY objective is to output Solidity that **compiles without any
syntax errors** under Solidity ^0.8.20 (for example in Remix) while following
OpenZeppelin best practices.

GENERATION PROFILE:
{profile.describe()}

GLOBAL REQUIREMENTS:
1. Use Solidity ^0.8.20
2. Follow OpenZeppelin best practices
3. Implement comprehensive NatSpec documentation
4. Use custom errors instead of require strings
5. Follow checks-effects-interactions pattern
6. Emit events for all state changes
7. Optimize for gas efficiency
8. Ensure the output is a single, self-contained, compilable Solidity contract
   with no Markdown fences or extraneous text.
"""

    # Category-specific high-level rules
    if profile.category in _CATEGORY_RULES:
        system_prompt += "\n" + _CATEGORY_RULES[profile.category]

    # Additional rules for token standards
    if profile.category == ContractCategory.ERC20:
        system_prompt += """

ERC20-SPECIFIC RULES:
- MUST inherit from the specified ERC20 base and extensions
- DO NOT reimplement transfer/balanceOf/approve/allowance (use inherited versions)
- Use _mint() and _burn() internal functions from ERC20 base
- Constructor MUST call all base constructors properly (ERC20, extensions, Ownable)
- Only implement custom/extended functionality (mint, burn wrappers, etc.)
"""
    elif profile.category == ContractCategory.ERC721:
        system_prompt += """

ERC721-SPECIFIC RULES:
- MUST inherit from the specified ERC721 base and extensions
- DO NOT reimplement ownerOf/balanceOf/transferFrom/safeTransferFrom
- Use _safeMint() for minting
- Constructor MUST call all base constructors properly (ERC721, extensions, Ownable)
"""

    # Build imports and inheritance lists
    imports_list = _build_imports(profile)
    inheritance_parts = _build_inheritance(profile)

    coverage_summary = json.dumps(
        {
            "state_variables": coverage.state_variables,
            "functions": coverage.functions,
            "events": coverage.events,
            "roles": coverage.roles,
        },
        indent=2,
    )

    imports_str = "\n".join(f'import "{imp}";' for imp in imports_list)
    inheritance_str = ", ".join(inheritance_parts)

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

    return system_prompt, user_prompt, imports_list, inheritance_parts
