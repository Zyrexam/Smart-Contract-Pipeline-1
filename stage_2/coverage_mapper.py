# solidity_code_generator/coverage_mapper.py
from typing import Dict
from .categories import SpecCoverage, ContractProfile, ContractCategory, AccessControlType

class CoverageMapper:
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

def _map_erc20(json_spec, profile: ContractProfile, coverage: SpecCoverage):
    for var in json_spec.get("state_variables", []):
        name = var.get("name")
        if name in {"name", "symbol"}:
            coverage.state_variables[name] = "Implemented via ERC20 constructor"
        elif name == "totalSupply":
            coverage.state_variables[name] = "Dynamic via ERC20.totalSupply()"
        elif name == "balances":
            coverage.state_variables[name] = "Internal ERC20 mapping"
        elif name == "owner" and profile.access_control == AccessControlType.SINGLE_OWNER:
            coverage.state_variables[name] = "Provided by Ownable.owner()"
        else:
            coverage.state_variables[name] = "Custom state variable"
    for func in json_spec.get("functions", []):
        fname = func.get("name")
        if fname in {"transfer","transferFrom","approve","balanceOf","allowance"}:
            coverage.functions[fname] = "Inherited from ERC20"
        elif fname == "mint":
            coverage.functions[fname] = "Custom mint() with access control"
        elif fname == "burn":
            coverage.functions[fname] = "Custom burn() or inherited from extension"
        else:
            coverage.functions[fname] = "Custom function"
    for event in json_spec.get("events", []):
        coverage.events[event.get("name")] = "Custom or inherited event"

def _map_erc721(json_spec, profile: ContractProfile, coverage: SpecCoverage):
    for var in json_spec.get("state_variables", []):
        coverage.state_variables[var.get("name")] = "Custom/inherited via ERC721"
    for func in json_spec.get("functions", []):
        fname = func.get("name")
        if fname in {"ownerOf","balanceOf","safeTransferFrom","transferFrom"}:
            coverage.functions[fname] = "Inherited from ERC721"
        else:
            coverage.functions[fname] = "Custom function"
    for event in json_spec.get("events", []):
        coverage.events[event.get("name")] = "Custom event"

def _map_staking(json_spec, profile: ContractProfile, coverage: SpecCoverage):
    for var in json_spec.get("state_variables", []):
        v = var.get("name","")
        if "token" in v.lower():
            coverage.state_variables[v] = "IERC20 token reference (staking/reward)"
        else:
            coverage.state_variables[v] = "Custom staking state variable"
    for func in json_spec.get("functions", []):
        fname = func.get("name","")
        if fname.lower() == "stake":
            coverage.functions[fname] = "Stake tokens with SafeERC20 + ReentrancyGuard"
        elif fname.lower() == "unstake":
            coverage.functions[fname] = "Unstake + claim rewards"
        elif "claim" in fname.lower():
            coverage.functions[fname] = "Claim rewards"
        else:
            coverage.functions[fname] = "Custom function"

def _map_vault(json_spec, profile: ContractProfile, coverage: SpecCoverage):
    for func in json_spec.get("functions", []):
        fname = func.get("name","")
        coverage.functions[fname] = "Vault function: mapping to ERC4626 or custom implementation"

def _map_governance(json_spec, profile: ContractProfile, coverage: SpecCoverage):
    for func in json_spec.get("functions", []):
        fname = func.get("name","")
        coverage.functions[fname] = "Governance function / override or custom"

def _map_marketplace(json_spec, profile: ContractProfile, coverage: SpecCoverage):
    for func in json_spec.get("functions", []):
        fname = func.get("name","")
        coverage.functions[fname] = "Marketplace function (list/buy/cancel)"

def _map_custom(json_spec, profile: ContractProfile, coverage: SpecCoverage):
    for var in json_spec.get("state_variables", []):
        coverage.state_variables[var.get("name")] = "Custom state variable"
    for func in json_spec.get("functions", []):
        coverage.functions[func.get("name")] = "Custom function"
    for event in json_spec.get("events", []):
        coverage.events[event.get("name")] = "Custom event"
    for role in json_spec.get("roles", []):
        coverage.roles[role.get("name")] = "Custom role"
