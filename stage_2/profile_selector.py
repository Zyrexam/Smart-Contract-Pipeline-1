# solidity_code_generator/profile_selector.py
from typing import Dict, List, Set
from .categories import ContractCategory, ContractProfile, AccessControlType, SecurityFeature

_DETECTION_KEYWORDS = {
    ContractCategory.STAKING: {"primary": ["stake", "staking", "unstake"], "secondary": ["reward", "rewards", "earn", "yield"]},
    ContractCategory.VAULT: {"primary": ["vault", "erc4626"], "secondary": ["deposit", "withdraw", "shares", "assets"]},
    ContractCategory.GOVERNANCE: {"primary": ["governor", "governance", "dao"], "secondary": ["proposal", "vote", "voting", "quorum"]},
    ContractCategory.NFT_MARKETPLACE: {"primary": ["marketplace", "market"], "secondary": ["listing", "buy", "sell", "offer"]},
    ContractCategory.AUCTION: {"primary": ["auction"], "secondary": ["bid", "bidder", "highest"]},
}

def detect_category(json_spec: Dict) -> ContractCategory:
    contract_type = json_spec.get("contract_type", "").lower()
    description = json_spec.get("description", "").lower()
    functions = json_spec.get("functions", [])
    func_names: Set[str] = {f.get("name", "").lower() for f in functions}
    text = f"{contract_type} {description}"

    if "erc20" in contract_type or "token" in contract_type:
        return ContractCategory.ERC20
    if "erc721" in contract_type or "nft" in contract_type:
        return ContractCategory.ERC721
    if "erc1155" in contract_type:
        return ContractCategory.ERC1155

    for category, kw in _DETECTION_KEYWORDS.items():
        primary_matches = sum(1 for w in kw["primary"] if w in text)
        secondary_matches = sum(1 for w in kw["secondary"] if w in text)
        if primary_matches >= 1 or secondary_matches >= 2:
            return category

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

def _select_erc20_profile(json_spec: Dict) -> ContractProfile:
    functions = json_spec.get("functions", [])
    func_names: Set[str] = {f.get("name", "").lower() for f in functions}
    description = json_spec.get("description", "").lower()
    extensions: List[str] = []
    security_features: List[SecurityFeature] = []

    if "mint" in func_names:
        extensions.append("Mintable")
    if "burn" in func_names:
        extensions.append("Burnable")
    if "pause" in func_names or "unpause" in func_names:
        extensions.append("Pausable")
        security_features.append(SecurityFeature.PAUSABLE)

    supply_semantics = None
    for var in json_spec.get("state_variables", []):
        name = var.get("name", "").lower()
        if "cap" in name or "max" in name:
            supply_semantics = {"type": "capped", "cap": var.get("initial_value")}
            extensions.append("Capped")
            break

    text = f"{description} {' '.join(func_names)}"
    if "snapshot" in text:
        extensions.append("Snapshot")
    if "vote" in text or "voting" in text:
        extensions.append("Votes")
    if "permit" in text:
        extensions.append("Permit")
    if "flashmint" in text or "flashloan" in text:
        extensions.append("FlashMint")

    roles = json_spec.get("roles", [])
    access = AccessControlType.ROLE_BASED if len(roles) > 1 else AccessControlType.SINGLE_OWNER

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

def _select_staking_profile(json_spec: Dict) -> ContractProfile:
    return ContractProfile(
        category=ContractCategory.STAKING,
        base_standard="Staking",
        extensions=[],
        access_control=AccessControlType.SINGLE_OWNER,
        security_features=[SecurityFeature.REENTRANCY_GUARD],
        supply_semantics=None,
    )

def _select_vault_profile(json_spec: Dict) -> ContractProfile:
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

def select_profile(json_spec: Dict) -> ContractProfile:
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
