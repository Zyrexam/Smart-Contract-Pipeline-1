"""Coverage mapping from Stage 1 JSON to implementation details.

This module produces a SpecCoverage object that explains, for each
state variable / function / event / role, how it is implemented in the
final contract (inherited vs custom, etc.).
"""

from __future__ import annotations

from typing import Dict

from .categories import SpecCoverage, ContractProfile, ContractCategory, AccessControlType


class CoverageMapper:
    """Maps JSON specification to implementation notes.

    High level dispatcher that calls category-specific helpers.
    """

    @staticmethod
    def map_specification(json_spec: Dict, profile: ContractProfile) -> SpecCoverage:
        coverage = SpecCoverage()

        if profile.category == ContractCategory.ERC20:
            _map_erc20(json_spec, profile, coverage)
        elif profile.category == ContractCategory.ERC721:
            _map_erc721(json_spec, profile, coverage)
        elif profile.category == ContractCategory.STAKING:
            _map_staking(json_spec, profile, coverage)
        elif profile.category == ContractCategory.VAULT:
            _map_vault(json_spec, profile, coverage)
        elif profile.category == ContractCategory.GOVERNANCE:
            _map_governance(json_spec, profile, coverage)
        elif profile.category == ContractCategory.NFT_MARKETPLACE:
            _map_marketplace(json_spec, profile, coverage)
        else:
            _map_custom(json_spec, profile, coverage)

        return coverage


# ---------------------------------------------------------------------------
# ERC20 coverage
# ---------------------------------------------------------------------------


def _map_erc20(json_spec: Dict, profile: ContractProfile, coverage: SpecCoverage) -> None:
    for var in json_spec.get("state_variables", []):
        name = var.get("name")
        if name in {"name", "symbol"}:
            coverage.state_variables[name] = "Implemented via ERC20 constructor"
        elif name == "totalSupply":
            coverage.state_variables[name] = "Dynamic via ERC20.totalSupply()"
        elif name == "balances":
            coverage.state_variables[name] = "Internal ERC20 balance mapping"
        elif name == "owner" and profile.access_control == AccessControlType.SINGLE_OWNER:
            coverage.state_variables[name] = "Provided by Ownable.owner()"
        else:
            coverage.state_variables[name] = "Custom state variable"

    for func in json_spec.get("functions", []):
        fname = func.get("name")
        if fname in {"transfer", "transferFrom", "approve", "balanceOf", "allowance"}:
            coverage.functions[fname] = "Inherited from ERC20"
        elif fname == "mint":
            coverage.functions[fname] = "Custom mint() with access control"
        elif fname == "burn":
            if "Burnable" in profile.extensions:
                coverage.functions[fname] = "Provided by ERC20Burnable.burn()"
            else:
                coverage.functions[fname] = "Custom burn() implementation"
        else:
            coverage.functions[fname] = "Custom function"

    for event in json_spec.get("events", []):
        ename = event.get("name")
        if ename in {"Transfer", "Approval"}:
            coverage.events[ename] = "Standard ERC20 event from base contract"
        else:
            coverage.events[ename] = "Custom event"

    for role in json_spec.get("roles", []):
        rname = role.get("name")
        if rname == "owner" and profile.access_control == AccessControlType.SINGLE_OWNER:
            coverage.roles[rname] = "Ownable owner"
        else:
            coverage.roles[rname] = "AccessControl role or custom role"


# ---------------------------------------------------------------------------
# ERC721 coverage
# ---------------------------------------------------------------------------


def _map_erc721(json_spec: Dict, profile: ContractProfile, coverage: SpecCoverage) -> None:
    for var in json_spec.get("state_variables", []):
        name = var.get("name")
        coverage.state_variables[name] = "Custom or inherited via ERC721 (e.g., name/symbol)"

    for func in json_spec.get("functions", []):
        fname = func.get("name")
        if fname in {"ownerOf", "balanceOf", "safeTransferFrom", "transferFrom"}:
            coverage.functions[fname] = "Inherited from ERC721"
        elif fname == "tokenURI" and "URIStorage" in profile.extensions:
            coverage.functions[fname] = "Provided by ERC721URIStorage"
        else:
            coverage.functions[fname] = "Custom function"

    for event in json_spec.get("events", []):
        ename = event.get("name")
        if ename == "Transfer":
            coverage.events[ename] = "Standard ERC721 Transfer event"
        else:
            coverage.events[ename] = "Custom event"


# ---------------------------------------------------------------------------
# Staking coverage
# ---------------------------------------------------------------------------


def _map_staking(json_spec: Dict, profile: ContractProfile, coverage: SpecCoverage) -> None:
    for var in json_spec.get("state_variables", []):
        vname = var.get("name", "")
        lower = vname.lower()
        if "token" in lower:
            coverage.state_variables[vname] = "IERC20 token reference (staking/reward)"
        elif "rate" in lower or "reward" in lower:
            coverage.state_variables[vname] = "Reward distribution parameter"
        else:
            coverage.state_variables[vname] = "Custom staking state variable"

    for func in json_spec.get("functions", []):
        fname = func.get("name", "")
        lower = fname.lower()
        if lower == "stake":
            coverage.functions[fname] = "Stake tokens with SafeERC20 + ReentrancyGuard"
        elif lower == "unstake":
            coverage.functions[fname] = "Unstake tokens and optionally claim rewards"
        elif "claim" in lower or "reward" in lower:
            coverage.functions[fname] = "Claim accumulated staking rewards"
        elif lower.startswith("set") or lower.startswith("update"):
            coverage.functions[fname] = "Admin-only configuration (onlyOwner)"
        else:
            coverage.functions[fname] = "Custom staking function"


# ---------------------------------------------------------------------------
# Vault coverage
# ---------------------------------------------------------------------------


def _map_vault(json_spec: Dict, profile: ContractProfile, coverage: SpecCoverage) -> None:
    for func in json_spec.get("functions", []):
        fname = func.get("name", "")
        lower = fname.lower()
        if lower == "deposit":
            coverage.functions[fname] = "Deposit assets and mint shares (ERC4626-style)"
        elif lower == "withdraw":
            coverage.functions[fname] = "Burn shares and withdraw assets"
        elif "totalassets" in lower:
            coverage.functions[fname] = "Vault totalAssets reporting"
        elif "shares" in lower or "convert" in lower:
            coverage.functions[fname] = "Conversion between assets and shares"
        else:
            coverage.functions[fname] = "Custom vault function"


# ---------------------------------------------------------------------------
# Governance coverage
# ---------------------------------------------------------------------------


def _map_governance(json_spec: Dict, profile: ContractProfile, coverage: SpecCoverage) -> None:
    for func in json_spec.get("functions", []):
        fname = func.get("name", "")
        lower = fname.lower()
        if lower in {"propose", "castvote", "execute"}:
            coverage.functions[fname] = "Inherited from OpenZeppelin Governor"
        elif lower in {"votingdelay", "votingperiod", "proposalthreshold", "quorum"}:
            coverage.functions[fname] = "Governor configuration override"
        else:
            coverage.functions[fname] = "Custom governance helper"


# ---------------------------------------------------------------------------
# Marketplace coverage
# ---------------------------------------------------------------------------


def _map_marketplace(json_spec: Dict, profile: ContractProfile, coverage: SpecCoverage) -> None:
    for func in json_spec.get("functions", []):
        fname = func.get("name", "")
        lower = fname.lower()
        if "list" in lower:
            coverage.functions[fname] = "Create or update NFT listing"
        elif "buy" in lower or "purchase" in lower:
            coverage.functions[fname] = "Buy listed NFT with fee + royalty handling"
        elif "cancel" in lower:
            coverage.functions[fname] = "Cancel active listing"
        elif "offer" in lower:
            coverage.functions[fname] = "Offer/bid related function"
        else:
            coverage.functions[fname] = "Custom marketplace function"


# ---------------------------------------------------------------------------
# Fallback custom coverage
# ---------------------------------------------------------------------------


def _map_custom(json_spec: Dict, profile: ContractProfile, coverage: SpecCoverage) -> None:
    for var in json_spec.get("state_variables", []):
        vname = var.get("name")
        coverage.state_variables[vname] = "Custom state variable"

    for func in json_spec.get("functions", []):
        fname = func.get("name")
        coverage.functions[fname] = "Custom function"

    for event in json_spec.get("events", []):
        ename = event.get("name")
        coverage.events[ename] = "Custom event"

    for role in json_spec.get("roles", []):
        rname = role.get("name")
        coverage.roles[rname] = "Custom role"
