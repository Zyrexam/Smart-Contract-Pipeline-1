"""
Simplified Coverage Mapper for Dynamic Classification

Maps specification elements to implementation strategies based on
contract profile (template vs custom).

Handles all generalized input types:
- Election systems
- Certificate verification
- Supply chain tracking (IoT, temperature sensors, conditional payments)
- Royalty distribution (automatic payments, oracle integration)
- Authentication/provenance (ownership history, immutable records)
- Registry systems
- DAO/Governance (token-based voting, automatic execution)
"""

from typing import Dict
from .categories_v2 import SpecCoverage, ContractProfile


class CoverageMapper:
    """Maps JSON spec to implementation coverage"""
    
    @staticmethod
    def map_specification(json_spec: Dict, profile: ContractProfile) -> SpecCoverage:
        """
        Map specification to coverage based on profile.
        
        For templates: Map to OpenZeppelin patterns
        For custom: Map to custom implementation strategies
        """
        coverage = SpecCoverage()
        
        if profile.is_template:
            CoverageMapper._map_template(json_spec, profile, coverage)
        else:
            CoverageMapper._map_custom(json_spec, profile, coverage)
        
        return coverage
    
    @staticmethod
    def _map_template(json_spec: Dict, profile: ContractProfile, coverage: SpecCoverage):
        """Map template contracts (ERC20, Governor, etc.)"""
        
        category = profile.category
        
        if category == "ERC20":
            CoverageMapper._map_erc20(json_spec, profile, coverage)
        elif category == "ERC721":
            CoverageMapper._map_erc721(json_spec, profile, coverage)
        elif category == "Governor":
            CoverageMapper._map_governor(json_spec, profile, coverage)
        elif category == "Staking":
            CoverageMapper._map_staking(json_spec, profile, coverage)
        elif category == "Vault":
            CoverageMapper._map_vault(json_spec, profile, coverage)
        elif category == "Marketplace":
            CoverageMapper._map_marketplace(json_spec, profile, coverage)
        else:
            # Fallback to generic template mapping
            CoverageMapper._map_generic_template(json_spec, profile, coverage)
    
    @staticmethod
    def _map_custom(json_spec: Dict, profile: ContractProfile, coverage: SpecCoverage):
        """Map custom contracts with semantic understanding"""
        
        subtype = profile.subtype or "general"
        
        # Map based on subtype
        if subtype == "election":
            CoverageMapper._map_election(json_spec, coverage)
        elif subtype == "certificate":
            CoverageMapper._map_certificate(json_spec, coverage)
        elif subtype == "supply_chain":
            CoverageMapper._map_supply_chain(json_spec, coverage)
        elif subtype == "royalty":
            CoverageMapper._map_royalty(json_spec, coverage)
        elif subtype == "authentication":
            CoverageMapper._map_authentication(json_spec, coverage)
        elif subtype == "registry":
            CoverageMapper._map_registry(json_spec, coverage)
        else:
            # Generic custom mapping
            CoverageMapper._map_generic_custom(json_spec, coverage)
    
    # Template mappers
    
    @staticmethod
    def _map_erc20(json_spec: Dict, profile: ContractProfile, coverage: SpecCoverage):
        """Map ERC20 token specification"""
        for var in json_spec.get("state_variables", []):
            name = var.get("name", "")
            if name in {"name", "symbol"}:
                coverage.state_variables[name] = "Implemented via ERC20 constructor"
            elif name == "totalSupply":
                coverage.state_variables[name] = "Dynamic via ERC20.totalSupply()"
            else:
                coverage.state_variables[name] = "Custom state variable"
        
        for func in json_spec.get("functions", []):
            fname = func.get("name", "")
            if fname in {"transfer", "transferFrom", "approve", "balanceOf", "allowance"}:
                coverage.functions[fname] = "Inherited from ERC20"
            elif fname == "mint":
                coverage.functions[fname] = "Custom mint() with access control"
            elif fname == "burn":
                coverage.functions[fname] = "Inherited from ERC20Burnable"
            else:
                coverage.functions[fname] = "Custom function"
        
        for event in json_spec.get("events", []):
            coverage.events[event.get("name", "")] = "Custom or inherited event"
    
    @staticmethod
    def _map_erc721(json_spec: Dict, profile: ContractProfile, coverage: SpecCoverage):
        """Map ERC721 NFT specification"""
        for func in json_spec.get("functions", []):
            fname = func.get("name", "")
            if fname in {"ownerOf", "balanceOf", "safeTransferFrom", "transferFrom"}:
                coverage.functions[fname] = "Inherited from ERC721"
            elif fname == "mint":
                coverage.functions[fname] = "Custom safeMint() implementation"
            else:
                coverage.functions[fname] = "Custom function"
    
    @staticmethod
    def _map_governor(json_spec: Dict, profile: ContractProfile, coverage: SpecCoverage):
        """Map Governor DAO specification with explicit requirements"""
        for var in json_spec.get("state_variables", []):
            name = var.get("name", "").lower()
            if "vote" in name and ("weight" in name or "count" in name):
                coverage.state_variables[var.get("name")] = "Vote weight tracking - Use mapping(uint256 => mapping(address => uint256)) voteWeights - SEPARATE from hasVoted"
            elif "voted" in name or "hasvoted" in name:
                coverage.state_variables[var.get("name")] = "Vote status tracking - Use mapping(uint256 => mapping(address => bool)) hasVoted - SEPARATE from vote weights"
        
        for func in json_spec.get("functions", []):
            fname = func.get("name", "").lower()
            if fname in {"propose", "castvote", "execute", "queue"}:
                coverage.functions[func.get("name")] = "Inherited from Governor - Use inherited functions"
            elif "vote" in fname:
                coverage.functions[func.get("name")] = "Vote casting - MUST: 1) Use getVotes(msg.sender, proposalSnapshot(proposalId)) for token balance (not parameter), 2) Use per-proposal hasVoted mapping, 3) Check BOTH majority AND quorum, 4) Auto-execute if conditions met"
            elif "execute" in fname or "action" in fname:
                coverage.functions[func.get("name")] = "Proposal execution - MUST be called automatically in vote() when majority AND quorum reached, NOT as separate manual function"
            elif "calculate" in fname or "result" in fname:
                coverage.functions[func.get("name")] = "Result calculation - MUST check BOTH: 1) Majority (forVotes > againstVotes), 2) Quorum (totalVotes >= quorum(snapshot))"
            else:
                coverage.functions[func.get("name")] = "Override or custom function"
        
        # Add explicit requirements for DAO systems
        coverage.state_variables["_REQUIREMENT_hasVoted"] = "MUST create: mapping(uint256 => mapping(address => bool)) hasVoted - Per-proposal vote status tracking"
        coverage.state_variables["_REQUIREMENT_noTokenBalance"] = "DO NOT create tokenBalance mapping - Use getVotes() directly to check token balance"
        coverage.functions["_REQUIREMENT_autoExecute"] = "MUST check if BOTH majority (forVotes > againstVotes) AND quorum (totalVotes >= quorum(snapshot)) reached at END of vote() function and call execute automatically"
        coverage.functions["_REQUIREMENT_getVotes"] = "MUST use getVotes(msg.sender, proposalSnapshot(proposalId)) to get vote weight, NOT block.number or separate mapping"
    
    @staticmethod
    def _map_staking(json_spec: Dict, profile: ContractProfile, coverage: SpecCoverage):
        """Map staking contract specification"""
        for func in json_spec.get("functions", []):
            fname = func.get("name", "").lower()
            if "stake" in fname:
                coverage.functions[fname] = "Stake with SafeERC20 + ReentrancyGuard"
            elif "unstake" in fname or "withdraw" in fname:
                coverage.functions[fname] = "Unstake + reward claim"
            elif "claim" in fname:
                coverage.functions[fname] = "Claim accumulated rewards"
            else:
                coverage.functions[fname] = "Custom staking function"
    
    @staticmethod
    def _map_vault(json_spec: Dict, profile: ContractProfile, coverage: SpecCoverage):
        """Map vault specification"""
        for func in json_spec.get("functions", []):
            fname = func.get("name", "")
            coverage.functions[fname] = "Vault function (ERC4626 or custom)"
    
    @staticmethod
    def _map_marketplace(json_spec: Dict, profile: ContractProfile, coverage: SpecCoverage):
        """Map marketplace specification"""
        for func in json_spec.get("functions", []):
            fname = func.get("name", "").lower()
            if "list" in fname:
                coverage.functions[fname] = "Create listing with price and token"
            elif "buy" in fname:
                coverage.functions[fname] = "Purchase with payment handling"
            elif "cancel" in fname:
                coverage.functions[fname] = "Cancel listing"
            else:
                coverage.functions[fname] = "Marketplace function"
    
    @staticmethod
    def _map_generic_template(json_spec: Dict, profile: ContractProfile, coverage: SpecCoverage):
        """Generic template mapping"""
        for var in json_spec.get("state_variables", []):
            coverage.state_variables[var.get("name", "")] = "Template state variable"
        for func in json_spec.get("functions", []):
            coverage.functions[func.get("name", "")] = "Template function"
        for event in json_spec.get("events", []):
            coverage.events[event.get("name", "")] = "Template event"
    
    # Custom mappers
    
    @staticmethod
    def _map_election(json_spec: Dict, coverage: SpecCoverage):
        """Map election system specification with explicit data structure requirements"""
        for var in json_spec.get("state_variables", []):
            name = var.get("name", "").lower()
            if "voter" in name and ("register" in name or "list" in name):
                coverage.state_variables[var.get("name")] = "Voter tracking (registration/status) - Use mapping(address => bool)"
            elif "voted" in name or "hasvoted" in name:
                coverage.state_variables[var.get("name")] = "Vote status tracking - Use mapping(address => bool) hasVoted - SEPARATE from vote counts"
            elif "candidate" in name and ("vote" in name or "count" in name or "votes" in name):
                coverage.state_variables[var.get("name")] = "Candidate vote counts - Use mapping(address => uint256) candidateVotes - SEPARATE from hasVoted"
            elif "candidate" in name:
                coverage.state_variables[var.get("name")] = "Candidate tracking (info/status) - Use mapping(address => bool) isCandidate"
            elif "period" in name or "deadline" in name or "time" in name or "end" in name:
                coverage.state_variables[var.get("name")] = "Time-based voting period - Use uint256 for timestamp"
            else:
                coverage.state_variables[var.get("name")] = "Election state - Design appropriate type"
        
        for func in json_spec.get("functions", []):
            fname = func.get("name", "").lower()
            if "register" in fname:
                coverage.functions[func.get("name")] = "Voter registration with verification - Set voters[address] = true"
            elif "vote" in fname or "cast" in fname:
                coverage.functions[func.get("name")] = "Vote casting - MUST: 1) Check auto-tabulate at START, 2) Check hasVoted[msg.sender], 3) Set hasVoted[msg.sender]=true, 4) Increment candidateVotes[candidate] - Use SEPARATE mappings"
            elif "result" in fname or "winner" in fname or "tabulate" in fname:
                coverage.functions[func.get("name")] = "Result calculation - MUST be internal _autoTabulate() called automatically, NOT external manual function"
            else:
                coverage.functions[func.get("name")] = "Election function - Implement with proper data structures"
        
        for event in json_spec.get("events", []):
            coverage.events[event.get("name")] = "Election event for transparency"
        
        # Add explicit data structure requirements
        coverage.state_variables["_REQUIREMENT_hasVoted"] = "MUST create: mapping(address => bool) public hasVoted - SEPARATE mapping for tracking if voter voted"
        coverage.state_variables["_REQUIREMENT_candidateVotes"] = "MUST create: mapping(address => uint256) public candidateVotes - SEPARATE mapping for vote counts per candidate"
        coverage.functions["_REQUIREMENT_autoTabulate"] = "MUST create internal _autoTabulate() function, check at START of vote() function, NOT as external manual function"
    
    @staticmethod
    def _map_certificate(json_spec: Dict, coverage: SpecCoverage):
        """Map certificate verification specification"""
        for func in json_spec.get("functions", []):
            fname = func.get("name", "").lower()
            if "issue" in fname:
                coverage.functions[func.get("name")] = "Certificate issuance with authorization - Use onlyEducationalInstitution modifier"
            elif "verify" in fname:
                coverage.functions[func.get("name")] = "Certificate verification/validation - Use onlyEmployer modifier"
            elif "revoke" in fname:
                coverage.functions[func.get("name")] = "Certificate revocation - Use onlyEducationalInstitution modifier"
            elif "add" in fname and ("institution" in fname or "employer" in fname or "role" in fname or "authorized" in fname):
                coverage.functions[func.get("name")] = "CRITICAL: Add role/authorized address - MUST have onlyAdmin/onlyOwner modifier - NO public access!"
            else:
                coverage.functions[func.get("name")] = "Certificate function - Check if access control needed"
    
    @staticmethod
    def _map_supply_chain(json_spec: Dict, coverage: SpecCoverage):
        """Map supply chain tracking specification (IoT sensors, temperature monitoring, conditional payments)"""
        for var in json_spec.get("state_variables", []):
            name = var.get("name", "").lower()
            if "location" in name or "status" in name:
                coverage.state_variables[var.get("name")] = "Location/status tracking - Use struct or mapping"
            elif "temperature" in name or "sensor" in name:
                coverage.state_variables[var.get("name")] = "Sensor data tracking - Use uint256 for temperature, mapping for sensor data"
            elif "payment" in name or "balance" in name:
                coverage.state_variables[var.get("name")] = "Payment tracking - Use mapping(address => uint256) for balances"
        
        for func in json_spec.get("functions", []):
            fname = func.get("name", "").lower()
            if "update" in fname or "log" in fname or "record" in fname:
                coverage.functions[func.get("name")] = "Location/status update - MUST accept IoT sensor data, use oracle or authorized updater, emit events"
            elif "alert" in fname or "trigger" in fname:
                coverage.functions[func.get("name")] = "Conditional alert/trigger - MUST check conditions automatically (e.g., temperature range), emit Alert event"
            elif "release" in fname or "payment" in fname or "deliver" in fname:
                coverage.functions[func.get("name")] = "Conditional payment release - MUST check delivery confirmation, release payment automatically when conditions met, use ReentrancyGuard"
            else:
                coverage.functions[func.get("name")] = "Supply chain function - Consider IoT/oracle integration"
        
        # Add explicit requirements
        coverage.functions["_REQUIREMENT_autoAlert"] = "MUST implement automatic alert when conditions violated (e.g., temperature out of range) - check in update function"
        coverage.functions["_REQUIREMENT_conditionalPayment"] = "MUST release payment automatically when delivery confirmed, NOT as separate manual function"
    
    @staticmethod
    def _map_royalty(json_spec: Dict, coverage: SpecCoverage):
        """Map royalty distribution specification (automatic payments, oracle integration, micro-payments)"""
        for var in json_spec.get("state_variables", []):
            name = var.get("name", "").lower()
            if "share" in name or "percentage" in name or "ownership" in name:
                coverage.state_variables[var.get("name")] = "Ownership share tracking - Use mapping(address => uint256) for percentages, ensure sum = 100%"
            elif "balance" in name or "payment" in name:
                coverage.state_variables[var.get("name")] = "Payment balance tracking - Use mapping(address => uint256) for accumulated payments"
        
        for func in json_spec.get("functions", []):
            fname = func.get("name", "").lower()
            if "distribute" in fname:
                coverage.functions[func.get("name")] = "Automatic royalty distribution - MUST be called automatically when oracle reports usage, distribute according to shares, use ReentrancyGuard"
            elif "report" in fname or "usage" in fname or "oracle" in fname:
                coverage.functions[func.get("name")] = "Oracle/usage reporting - MUST trigger automatic distribution, use onlyOracle modifier or authorized reporter"
            elif "withdraw" in fname or "claim" in fname:
                coverage.functions[func.get("name")] = "Pull payment for royalties - Use pull payment pattern, allow recipients to claim accumulated payments"
            else:
                coverage.functions[func.get("name")] = "Royalty function - Consider automatic distribution logic"
        
        # Add explicit requirements
        coverage.functions["_REQUIREMENT_autoDistribute"] = "MUST automatically distribute payments when oracle reports usage data, NOT as separate manual function"
        coverage.functions["_REQUIREMENT_microPayments"] = "MUST handle micro-payments correctly, use SafeERC20 for token transfers"
    
    @staticmethod
    def _map_authentication(json_spec: Dict, coverage: SpecCoverage):
        """Map authenticity/provenance tracking specification (immutable records, ownership history, maintenance records)"""
        for var in json_spec.get("state_variables", []):
            name = var.get("name", "").lower()
            if "history" in name or "provenance" in name or "record" in name:
                coverage.state_variables[var.get("name")] = "Ownership/transaction history - Use struct array or mapping(uint256 => HistoryEntry) for immutable records"
            elif "id" in name or "unique" in name:
                coverage.state_variables[var.get("name")] = "Unique identifier - Use bytes32 or uint256 for item ID"
            elif "maintenance" in name:
                coverage.state_variables[var.get("name")] = "Maintenance records - Use struct array for immutable maintenance history"
        
        for func in json_spec.get("functions", []):
            fname = func.get("name", "").lower()
            if "verify" in fname or "authenticate" in fname:
                coverage.functions[func.get("name")] = "Authenticity verification - MUST check immutable records, return verification result, emit event"
            elif "transfer" in fname or "change" in fname:
                coverage.functions[func.get("name")] = "Ownership transfer - MUST update ownership history immutably, emit Transfer event with full history"
            elif "register" in fname or "create" in fname:
                coverage.functions[func.get("name")] = "Item registration - MUST store unique ID, initial ownership, emit Registration event"
            elif "maintenance" in fname or "record" in fname:
                coverage.functions[func.get("name")] = "Maintenance record - MUST add immutable maintenance entry to history, emit MaintenanceRecorded event"
            else:
                coverage.functions[func.get("name")] = "Authentication function - Ensure immutable record keeping"
        
        # Add explicit requirements
        coverage.state_variables["_REQUIREMENT_immutableHistory"] = "MUST use immutable data structures for ownership/maintenance history - cannot be modified after creation"
        coverage.functions["_REQUIREMENT_transparentTransfer"] = "MUST manage transparent transfer of digital title, update history immutably"
    
    @staticmethod
    def _map_registry(json_spec: Dict, coverage: SpecCoverage):
        """Map registry system specification"""
        for func in json_spec.get("functions", []):
            fname = func.get("name", "").lower()
            if "register" in fname or "add" in fname:
                coverage.functions[func.get("name")] = "Record registration"
            elif "lookup" in fname or "get" in fname:
                coverage.functions[func.get("name")] = "Record lookup/retrieval"
            else:
                coverage.functions[func.get("name")] = "Registry function"
    
    @staticmethod
    def _map_generic_custom(json_spec: Dict, coverage: SpecCoverage):
        """Generic custom contract mapping"""
        for var in json_spec.get("state_variables", []):
            coverage.state_variables[var.get("name", "")] = "Custom state variable"
        for func in json_spec.get("functions", []):
            coverage.functions[func.get("name", "")] = "Custom function"
        for event in json_spec.get("events", []):
            coverage.events[event.get("name", "")] = "Custom event"
        for role in json_spec.get("roles", []):
            coverage.roles[role.get("name", "")] = "Custom role"
