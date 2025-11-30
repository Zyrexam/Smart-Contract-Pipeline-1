"""Profile selection and category detection for Stage 2.

This module looks at the Stage 1 JSON spec and decides:
- which high-level ContractCategory applies (ERC20, STAKING, etc.)
- which ContractProfile (base standard, extensions, security features).

It is intentionally heuristic-based: as you expand Stage 1, you can
make this stricter and more data-driven.
"""

from __future__ import annotations

from typing import Dict, List, Set

from .categories import ContractCategory, ContractProfile, AccessControlType, SecurityFeature


# ---------------------------------------------------------------------------
# Keyword-based detection for non-token categories
# ---------------------------------------------------------------------------

_DETECTION_KEYWORDS = {
    ContractCategory.STAKING: {
        "primary": ["stake", "staking", "unstake"],
        "secondary": ["reward", "rewards", "earn", "yield", "farm"],
    },
    ContractCategory.VAULT: {
        "primary": ["vault", "erc4626"],
        "secondary": ["deposit", "withdraw", "shares", "assets"],
    },
    ContractCategory.GOVERNANCE: {
        "primary": ["governor", "governance", "dao"],
        "secondary": ["proposal", "vote", "voting", "quorum"],
    },
    ContractCategory.NFT_MARKETPLACE: {
        "primary": ["marketplace", "market"],
        "secondary": ["listing", "buy", "sell", "offer"],
    },
    ContractCategory.AUCTION: {
        "primary": ["auction"],
        "secondary": ["bid", "bidder", "highest bidder"],
    },
}


def detect_category(json_spec: Dict) -> ContractCategory:
    """Detect the most appropriate contract category from the spec.

    Signals used (in order):
    1. contract_type field (e.g. "erc20", "token", "nft", ...)
    2. description keywords (e.g. "staking", "vault", "governance")
    3. function names (e.g. stake/unstake, deposit/withdraw, etc.)
    """

    contract_type = json_spec.get("contract_type", "").lower()
    description = json_spec.get("description", "").lower()
    functions = json_spec.get("functions", [])
    func_names: Set[str] = {f.get("name", "").lower() for f in functions}

    text = f"{contract_type} {description}"

    # Direct token standard detection
    if "erc20" in contract_type or "token" in contract_type:
        return ContractCategory.ERC20
    if "erc721" in contract_type or "nft" in contract_type:
        return ContractCategory.ERC721
    if "erc1155" in contract_type:
        return ContractCategory.ERC1155

    # Keyword-based detection for DeFi / governance / marketplace
    for category, kw in _DETECTION_KEYWORDS.items():
        primary_matches = sum(1 for word in kw["primary"] if word in text)
        secondary_matches = sum(1 for word in kw["secondary"] if word in text)
        if primary_matches >= 1 or secondary_matches >= 2:
            return category

    # Function-signature based detection fallbacks
    if {"stake", "unstake"}.issubset(func_names):
        return ContractCategory.STAKING
    if {"deposit", "withdraw", "totalassets"}.issubset(func_names):
        return ContractCategory.VAULT
    if {"propose", "castvote", "execute"}.issubset(func_names):
        return ContractCategory.GOVERNANCE
    if {"listitem", "buyitem"}.issubset(func_names):
        return ContractCategory.NFT_MARKETPLACE
    if {"bid", "endauction"}.issubset(func_names):
        return ContractCategory.AUCTION

    return ContractCategory.CUSTOM


# ---------------------------------------------------------------------------
# ERC20 profile selection (basic + advanced features)
# ---------------------------------------------------------------------------


def _select_erc20_profile(json_spec: Dict) -> ContractProfile:
    functions = json_spec.get("functions", [])
    func_names: Set[str] = {f.get("name", "").lower() for f in functions}
    description = json_spec.get("description", "").lower()

    extensions: List[str] = []
    security_features: List[SecurityFeature] = []

    # Basic ERC20 feature hints
    if "mint" in func_names:
        extensions.append("Mintable")
    if "burn" in func_names:
        extensions.append("Burnable")
    if "pause" in func_names or "unpause" in func_names:
        extensions.append("Pausable")
        security_features.append(SecurityFeature.PAUSABLE)

    # Supply semantics (simple heuristic: any state var with cap/max in name)
    supply_semantics = None
    for var in json_spec.get("state_variables", []):
        name = var.get("name", "").lower()
        if "cap" in name or "max" in name:
            supply_semantics = {"type": "capped", "cap": var.get("initial_value")}
            extensions.append("Capped")
            break

    # Advanced ERC20 features from description / functions
    text = f"{description} {' '.join(func_names)}"
    if "snapshot" in text:
        extensions.append("Snapshot")
    if "vote" in text or "voting" in text or "delegate" in text:
        extensions.append("Votes")
    if "permit" in text or "gasless" in text:
        extensions.append("Permit")
    if "flashloan" in text or "flashmint" in text or "flash mint" in text:
        extensions.append("FlashMint")

    # Access control: single owner vs roles
    roles = json_spec.get("roles", [])
    access = AccessControlType.ROLE_BASED if len(roles) > 1 else AccessControlType.SINGLE_OWNER

    # Reentrancy: if any function is payable, assume external calls
    for func in functions:
        if func.get("payable"):
            security_features.append(SecurityFeature.REENTRANCY_GUARD)
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
        access_control=access,
        security_features=security_features,
        supply_semantics=supply_semantics,
    )


# ---------------------------------------------------------------------------
# ERC721 / NFT profile selection
# ---------------------------------------------------------------------------


def _select_erc721_profile(json_spec: Dict) -> ContractProfile:
    functions = json_spec.get("functions", [])
    func_names: Set[str] = {f.get("name", "").lower() for f in functions}
    description = json_spec.get("description", "").lower()

    extensions: List[str] = []

    if "tokenofownerbyindex" in func_names or "enumerate" in description:
        extensions.append("Enumerable")
    if "tokenuri" in func_names or "metadata" in description:
        extensions.append("URIStorage")
    if "royalty" in description or "erc2981" in description:
        extensions.append("Royalty")
    if "burn" in func_names:
        extensions.append("Burnable")

    return ContractProfile(
        category=ContractCategory.ERC721,
        base_standard="ERC721",
        extensions=extensions,
        access_control=AccessControlType.SINGLE_OWNER,
        security_features=[],
        supply_semantics=None,
    )


# ---------------------------------------------------------------------------
# DeFi / governance / marketplace profiles (high level)
# ---------------------------------------------------------------------------


def _select_staking_profile(json_spec: Dict) -> ContractProfile:
    """Single-asset staking with rewards, ReentrancyGuard + Ownable."""
    return ContractProfile(
        category=ContractCategory.STAKING,
        base_standard="Staking",
        extensions=[],
        access_control=AccessControlType.SINGLE_OWNER,
        security_features=[SecurityFeature.REENTRANCY_GUARD],
        supply_semantics=None,
    )


def _select_vault_profile(json_spec: Dict) -> ContractProfile:
    """Vault profile; if ERC4626 is mentioned, prefer that standard."""
    description = json_spec.get("description", "").lower()
    if "erc4626" in description or "erc-4626" in description:
        return ContractProfile(
            category=ContractCategory.VAULT,
            base_standard="ERC4626",
            extensions=["ERC4626"],
            access_control=AccessControlType.SINGLE_OWNER,
            security_features=[SecurityFeature.REENTRANCY_GUARD],
            supply_semantics=None,
        )

    return ContractProfile(
        category=ContractCategory.VAULT,
        base_standard="Vault",
        extensions=[],
        access_control=AccessControlType.SINGLE_OWNER,
        security_features=[SecurityFeature.REENTRANCY_GUARD],
        supply_semantics=None,
    )


def _select_governance_profile(json_spec: Dict) -> ContractProfile:
    """Governor-style governance profile."""
    return ContractProfile(
        category=ContractCategory.GOVERNANCE,
        base_standard="Governor",
        extensions=["GovernorVotes", "GovernorSettings"],
        access_control=AccessControlType.SINGLE_OWNER,
        security_features=[SecurityFeature.TIMELOCK],
        supply_semantics=None,
    )


def _select_marketplace_profile(json_spec: Dict) -> ContractProfile:
    return ContractProfile(
        category=ContractCategory.NFT_MARKETPLACE,
        base_standard="NFTMarketplace",
        extensions=[],
        access_control=AccessControlType.SINGLE_OWNER,
        security_features=[SecurityFeature.REENTRANCY_GUARD],
        supply_semantics=None,
    )


def _select_auction_profile(json_spec: Dict) -> ContractProfile:
    return ContractProfile(
        category=ContractCategory.AUCTION,
        base_standard="Auction",
        extensions=[],
        access_control=AccessControlType.SINGLE_OWNER,
        security_features=[SecurityFeature.REENTRANCY_GUARD],
        supply_semantics=None,
    )


def _select_custom_profile(json_spec: Dict) -> ContractProfile:
    return ContractProfile(
        category=ContractCategory.CUSTOM,
        base_standard="Custom",
        extensions=[],
        access_control=AccessControlType.SINGLE_OWNER,
        security_features=[],
        supply_semantics=None,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def select_profile(json_spec: Dict) -> ContractProfile:
    """Detect category and return a filled ContractProfile.

    This is the only function generator.py should call.
    """

    category = detect_category(json_spec)

    if category == ContractCategory.ERC20:
        return _select_erc20_profile(json_spec)
    if category == ContractCategory.ERC721:
        return _select_erc721_profile(json_spec)
    if category == ContractCategory.STAKING:
        return _select_staking_profile(json_spec)
    if category == ContractCategory.VAULT:
        return _select_vault_profile(json_spec)
    if category == ContractCategory.GOVERNANCE:
        return _select_governance_profile(json_spec)
    if category == ContractCategory.NFT_MARKETPLACE:
        return _select_marketplace_profile(json_spec)
    if category == ContractCategory.AUCTION:
        return _select_auction_profile(json_spec)

    return _select_custom_profile(json_spec)
