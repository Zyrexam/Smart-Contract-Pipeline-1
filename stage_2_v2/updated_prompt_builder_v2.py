
"""
Dynamic Prompt Builder based on LLM Classification

Instead of hardcoded category rules, prompts are built based on:
1. Whether it's a template (ERC20, Governor) or custom contract
2. The specific template type if applicable
3. The business logic from the specification
"""

import json
from typing import Dict, List, Tuple
from .llm_utils import estimate_tokens, truncate_spec_for_prompt

# Template-specific guidance
TEMPLATE_GUIDANCE = {
    "ERC20": """
ERC20 TOKEN IMPLEMENTATION:
- Inherit from OpenZeppelin ERC20 base
- Constructor: ERC20("name", "symbol") Ownable(msg.sender)
- For minting: Add mint() with access control
- For burning: Inherit ERC20Burnable or add burn()
- For custom transfer logic: Override _update(from, to, value)
- DO NOT reimplement transfer/approve/balanceOf
""",
    
    "ERC721": """
ERC721 NFT IMPLEMENTATION:
- Inherit from OpenZeppelin ERC721 base
- Constructor: ERC721("name", "symbol") Ownable(msg.sender)
- For minting: Add safeMint() with proper tokenId handling
- For metadata: Use ERC721URIStorage extension
- For enumeration: Use ERC721Enumerable extension
- Override _update for custom transfer logic
""",
    
    "Governor": """
GOVERNOR DAO IMPLEMENTATION:
- Inherit: Governor, GovernorSettings, GovernorVotes, GovernorVotesQuorumFraction
- Constructor must initialize all parent contracts
- Override required functions: votingDelay, votingPeriod, proposalThreshold, quorum
- Implement proposal lifecycle: propose, vote, execute
- Consider adding TimelockController for security
""",
    
    "Staking": """
STAKING CONTRACT IMPLEMENTATION:
- Use SafeERC20 for all token transfers
- Add ReentrancyGuard to stake/unstake functions
- Track: user stakes, total staked, rewards per token
- Implement: stake(), unstake(), claimRewards()
- Consider: reward rate updates, emergency withdraw
""",
    
    "Vault": """
VAULT IMPLEMENTATION:
- Prefer ERC4626 standard for asset vaults
- Implement: deposit, withdraw, redeem, totalAssets
- Use ReentrancyGuard for all fund operations
- Track shares and assets accurately
- Consider: fee mechanisms, withdrawal delays
""",
    
    "Marketplace": """
NFT MARKETPLACE IMPLEMENTATION:
- Use ReentrancyGuard for all payment functions
- Track: listings (seller, price, tokenId)
- Implement: list, buy, cancel, updatePrice
- Consider: royalties (ERC2981), fees, offers
- Use pull payment pattern for funds
""",
}

OPENZEPPELIN_V5_RULES = """
OPENZEPPELIN V5 REQUIREMENTS:
1. Ownable requires initialOwner in constructor: Ownable(msg.sender)
2. _beforeTokenTransfer REMOVED - use _update override instead
3. Use custom errors instead of require strings
4. SafeERC20 for all ERC20 interactions
5. Access control via Ownable or AccessControl
"""

CUSTOM_CONTRACT_GUIDANCE = """
CUSTOM CONTRACT IMPLEMENTATION:
1. Design from scratch based on business requirements
2. Use appropriate data structures for the domain
3. Implement proper access control (Ownable/AccessControl/none)
4. Use custom errors for gas efficiency
5. Emit events for all state changes
6. Follow checks-effects-interactions pattern
7. Add comprehensive NatSpec documentation
8. Use block.timestamp for time-based logic
9. Separate concerns with multiple mappings
10. NEVER reuse one mapping for multiple logical purposes

CRITICAL - DATA STRUCTURES (MUST FOLLOW):
Each distinct piece of data MUST have its own separate mapping/variable.
NEVER reuse the same mapping for different logical purposes.

EXAMPLE - Election System (CORRECT):
- mapping(address => bool) public hasVoted;           // Track if voter has voted
- mapping(address => uint256) public candidateVotes;  // Count votes per candidate
- mapping(address => bool) public voters;              // Track registered voters
- mapping(address => bool) public isCandidate;        // Track candidate status

EXAMPLE - Election System (WRONG - DO NOT DO THIS):
- mapping(address => uint256) public votes;  // Using ONE mapping for BOTH:
  * votes[msg.sender] = 1;                   // marking voter as voted
  * votes[candidate] += 1;                    // counting candidate votes
  This is WRONG because if a candidate is also a voter, their vote count gets corrupted!

RULE: If you need to track "has X happened?" AND "how many Y?", use TWO separate mappings.

AUTOMATIC ACTIONS - CRITICAL IMPLEMENTATION:
When spec says "automatically" do something (e.g., "automatically tabulate when period ends"):

CORRECT PATTERN:
1. Create an internal function for the automatic action: function _autoTabulate() internal { ... }
2. Check the condition at the START of relevant functions (before main logic)
3. Call the internal function automatically when condition is met
4. DO NOT create external/public functions that require manual calls for automatic actions

EXAMPLE - Automatic Tabulation (CORRECT):
function vote(uint256 candidateIndex) external {{
    // FIRST: Check if period ended and auto-tabulate if needed
    if (block.timestamp > votingPeriodEnd && !winnerDeclared) {{
        _autoTabulate();
    }}
    
    // THEN: Check if voting is still allowed
    if (block.timestamp > votingPeriodEnd) revert VotingPeriodEnded();
    if (hasVoted[msg.sender]) revert AlreadyVoted();
    
    // Main voting logic
    hasVoted[msg.sender] = true;
    candidateVotes[candidates[candidateIndex]] += 1;
    emit VoteCast(msg.sender, candidateIndex);
}}

// Internal function for automatic tabulation
function _autoTabulate() internal {{
    // Tabulation logic here
    winnerDeclared = true;
    // ... find winner ...
}}

EXAMPLE - Automatic Tabulation (WRONG - DO NOT DO THIS):
function vote(...) external onlyDuringVotingPeriod {{
    // ... voting logic ...
    
    // WRONG: Checking AFTER the vote is cast (will never be true due to modifier)
    if (block.timestamp > votingPeriodEnd) {{
        _declareWinner();
    }}
}}

// WRONG: External function requiring manual admin call
function declareWinner() external onlyAdmin {{
    _declareWinner();
}}

KEY POINTS:
- Check automatic conditions at the START of functions, not at the end
- Make automatic actions internal, not external
- Remove manual functions for actions that should be automatic
- If a modifier prevents a condition (e.g., onlyDuringVotingPeriod), don't check that condition again inside the function

SECURITY - ACCESS CONTROL (CRITICAL):
- Functions that add/remove roles, authorized addresses, or modify access control MUST have admin/owner-only modifiers
- Example: addEducationalInstitution(), addEmployer(), addRole() MUST have onlyAdmin or onlyOwner modifier
- NEVER make role management functions public without access control
- If contract has roles (institutions, employers, etc.), there MUST be an admin/owner who can manage them
- WRONG: function addEducationalInstitution(address) external {{ ... }}  // No access control!
- CORRECT: function addEducationalInstitution(address) external onlyAdmin {{ ... }}  // Admin only!

DAO/VOTING SYSTEMS - CRITICAL REQUIREMENTS:
- For token-based voting: Use token balance (getVotes() or balanceOf()) to determine vote weight, don't accept voteWeight as parameter
- For double-voting prevention: Use SEPARATE mapping per proposal: mapping(uint256 => mapping(address => bool)) hasVoted
- For vote weight tracking: Use SEPARATE mapping: mapping(uint256 => mapping(address => uint256)) voteWeights
- NEVER reuse one mapping for both "has voted?" and "vote weight"
- For automatic execution: Check if majority AND quorum reached at END of vote() function and call execute function automatically
- For token holder check: Use getVotes() to check if user has tokens, NOT a separate tokenBalance mapping that's never updated
- For quorum check: Must check BOTH majority (forVotes > againstVotes) AND quorum (totalVotes >= quorum(snapshot))
- For proposal snapshot: Use proposalSnapshot(proposalId) to get correct block number for getVotes()
- WRONG: mapping(address => uint256) tokenBalance;  // Never updated, will always fail
- WRONG: mapping(address => uint256) votes;  // Using for both hasVoted check and weight storage
- CORRECT: mapping(uint256 => mapping(address => bool)) hasVoted;  // Per-proposal vote status
- CORRECT: Use getVotes(msg.sender, proposalSnapshot(proposalId)) to check token balance

DAO VOTING EXAMPLE (CORRECT):
function vote(uint256 proposalId, bool support) external {{
    // Check if already voted for this proposal
    if (hasVoted[proposalId][msg.sender]) revert AlreadyVoted();
    
    // Get vote weight from token balance at proposal snapshot (not parameter)
    uint256 snapshot = proposalSnapshot(proposalId);
    uint256 voteWeight = getVotes(msg.sender, snapshot);
    if (voteWeight == 0) revert NoTokens();
    
    // Record vote
    hasVoted[proposalId][msg.sender] = true;
    if (support) {{
        proposals[proposalId].forVotes += voteWeight;
    }} else {{
        proposals[proposalId].againstVotes += voteWeight;
    }}
    
    emit VoteCast(msg.sender, proposalId, support);
    
    // AUTOMATIC EXECUTION: Check if majority AND quorum reached, then execute
    uint256 totalVotes = proposals[proposalId].forVotes + proposals[proposalId].againstVotes;
    uint256 requiredQuorum = quorum(snapshot);
    if (proposals[proposalId].forVotes > proposals[proposalId].againstVotes 
        && totalVotes >= requiredQuorum 
        && !proposals[proposalId].executed) {{
        _executeProposal(proposalId);
    }}
}}

DAO VOTING EXAMPLE (WRONG - DO NOT DO THIS):
function vote(uint256 proposalId, uint256 voteWeight) external {{
    // WRONG: Accepting voteWeight as parameter instead of using token balance
    if (votes[msg.sender] != 0) revert AlreadyVoted();  // WRONG: One mapping for both purposes
    votes[msg.sender] = voteWeight;  // WRONG: Same mapping stores weight
    // WRONG: No automatic execution
}}
"""


class DynamicPromptBuilder:
    """Builds prompts based on contract profile and classification"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
    
    def build_prompts(
        self, 
        json_spec: Dict, 
        profile: 'ContractProfile',
        classification: Dict,
        coverage: 'SpecCoverage'
    ) -> Tuple[str, str, List[str], List[str]]:
        """
        Build system and user prompts based on profile.
        
        Returns:
            (system_prompt, user_prompt, imports, inheritance)
        """
        
        if profile.is_template:
            return self._build_template_prompts(json_spec, profile, coverage)
        else:
            return self._build_custom_prompts(json_spec, profile, classification, coverage)
    
    def _build_template_prompts(
        self, 
        json_spec: Dict, 
        profile: 'ContractProfile',
        coverage: 'SpecCoverage'
    ) -> Tuple[str, str, List[str], List[str]]:
        """Build prompts for template contracts (ERC20, Governor, etc.)"""
        
        # Get template-specific guidance
        template_guidance = TEMPLATE_GUIDANCE.get(profile.category, "")
        
        # Build system prompt
        system_prompt = f"""You are an expert Solidity developer specializing in {profile.category} contracts.

TARGET: Solidity ^0.8.20 with OpenZeppelin v5

{OPENZEPPELIN_V5_RULES}

{template_guidance}

PROFILE:
{profile.describe()}

REQUIREMENTS:
- Use NatSpec documentation for all public functions
- Use custom errors (not require strings)
- Follow checks-effects-interactions pattern
- Emit events for all state changes
- Optimize for gas efficiency
- Single-file output only
- NO explanations, ONLY Solidity code
"""

        # Build user prompt
        contract_name = json_spec.get('contract_name', 'Contract')
        
        user_prompt = f"""Generate a complete, compilable Solidity {profile.category} contract.

SPECIFICATION:
{json.dumps(json_spec, indent=2)}

IMPLEMENTATION MAPPING:
{json.dumps(coverage.to_dict(), indent=2)}

CONTRACT NAME: {contract_name}

CRITICAL REQUIREMENTS:
1. Inherit from appropriate OpenZeppelin contracts
2. Initialize all parent constructors correctly
3. Implement all specified functions
4. Add proper access control
5. Use custom errors exclusively
6. Emit events for state changes

OUTPUT: Complete Solidity source code only, no markdown.
"""

        # Build imports and inheritance
        imports = self._build_template_imports(profile)
        inheritance = self._build_template_inheritance(profile)
        
        return system_prompt, user_prompt, imports, inheritance
    
    def _build_custom_prompts(
        self, 
        json_spec: Dict, 
        profile: 'ContractProfile',
        classification: Dict,
        coverage: 'SpecCoverage'
    ) -> Tuple[str, str, List[str], List[str]]:
        """Build prompts for custom contracts"""
        
        subtype = profile.subtype or "custom business logic"
        
        # Build system prompt
        system_prompt = f"""You are an expert Solidity developer specializing in custom smart contracts.

TARGET: Solidity ^0.8.20

{CUSTOM_CONTRACT_GUIDANCE}

CONTRACT TYPE: {subtype.upper()}
Classification Confidence: {classification.get('confidence', 0.5):.0%}
Reasoning: {classification.get('reasoning', 'Custom contract')}

PROFILE:
{profile.describe()}

REQUIREMENTS:
- Design contract from scratch based on business requirements
- Use appropriate data structures for the domain
- Implement proper access control as needed
- Use custom errors for gas efficiency
- Add comprehensive NatSpec documentation
- Follow Solidity best practices
- Single-file output only
- NO explanations, ONLY Solidity code
"""

        # Extract detailed requirements
        contract_name = json_spec.get('contract_name', 'CustomContract')
        description = json_spec.get('description', '')
        
        # Check if spec is too large and truncate if needed
        spec_str = json.dumps(json_spec, indent=2)
        if estimate_tokens(spec_str) > 10000:  # ~40k chars
            if self.debug:
                print(f"Warning: Large spec detected, truncating for prompt...")
            json_spec = truncate_spec_for_prompt(json_spec, max_chars=2000)
        
        state_vars = json_spec.get('state_variables', [])
        functions = json_spec.get('functions', [])
        events = json_spec.get('events', [])
        roles = json_spec.get('roles', [])
        
        # Build detailed user prompt
        user_prompt = f"""Generate a complete Solidity smart contract: {contract_name}

DESCRIPTION:
{description}

FULL SPECIFICATION:
{json.dumps(json_spec, indent=2)}

IMPLEMENTATION REQUIREMENTS:

STATE VARIABLES ({len(state_vars)} specified):
{self._format_state_vars(state_vars)}

FUNCTIONS ({len(functions)} specified):
{self._format_functions(functions)}

EVENTS ({len(events)} specified):
{self._format_events(events)}

ACCESS CONTROL:
Type: {profile.access_control}
Roles: {', '.join(r.get('name', '') for r in roles) if roles else 'Owner only'}

IMPLEMENTATION COVERAGE:
{json.dumps(coverage.to_dict(), indent=2)}

CRITICAL REQUIREMENTS:
1. Implement ALL specified state variables, functions, and events
2. Use SEPARATE mappings for DIFFERENT logical purposes - THIS IS CRITICAL
3. For voting/tracking: separate "has participated" from "count/amount"
4. Implement proper access control with modifiers - CRITICAL SECURITY
5. Add time-based logic with block.timestamp where needed
6. Emit events for all state changes
7. Use custom errors (not require strings)
8. Add comprehensive NatSpec documentation
9. Make automatic actions truly automatic (no manual function calls needed)
10. SECURITY: Functions that add/remove roles, authorized addresses, or modify access control MUST have admin/owner-only access control

DATA STRUCTURE RULES - CRITICAL (MUST FOLLOW):
Each distinct piece of data MUST have its own separate mapping/variable.
NEVER reuse the same mapping for different logical purposes.

For Election Systems (EXAMPLE):
CORRECT:
- mapping(address => bool) public hasVoted;           // Track if voter voted
- mapping(address => uint256) public candidateVotes;  // Count votes per candidate
- mapping(address => bool) public voters;              // Registered voters
- mapping(address => bool) public isCandidate;        // Candidate status

WRONG (DO NOT DO THIS):
- mapping(address => uint256) public votes;  // Using ONE mapping for BOTH:
  * votes[msg.sender] = 1;                   // marking voter as voted
  * votes[candidate] += 1;                   // counting candidate votes
  This causes bugs if a candidate is also a voter!

RULE: If tracking "has X happened?" AND "how many Y?", use TWO separate mappings.

AUTOMATIC ACTIONS - CRITICAL IMPLEMENTATION:
When spec says "automatically" (e.g., "automatically tabulate when period ends"):

CORRECT PATTERN:
1. Create internal function: function _autoTabulate() internal { ... }
2. Check condition at the START of relevant functions (before main logic)
3. Call internal function automatically when condition is met
4. DO NOT create external functions requiring manual calls

CORRECT EXAMPLE:
function vote(uint256 candidateIndex) external {{
    // FIRST: Check if period ended and auto-tabulate
    if (block.timestamp > votingPeriodEnd && !winnerDeclared) {{
        _autoTabulate();
    }}
    
    // THEN: Check if voting still allowed
    if (block.timestamp > votingPeriodEnd) revert VotingPeriodEnded();
    if (hasVoted[msg.sender]) revert AlreadyVoted();
    
    // Main voting logic
    hasVoted[msg.sender] = true;
    candidateVotes[candidates[candidateIndex]] += 1;
}}

WRONG EXAMPLE (DO NOT DO THIS):
function vote(...) external onlyDuringVotingPeriod {{
    // ... voting logic ...
    
    // WRONG: Checking AFTER vote (will never be true due to modifier)
    if (block.timestamp > votingPeriodEnd) {{
        _declareWinner();
    }}
}}

// WRONG: External function requiring manual call
function declareWinner() external onlyAdmin {{
    _declareWinner();
}}

KEY POINTS:
- Check automatic conditions at the START of functions, not at the end
- Make automatic actions internal, not external
- Remove manual functions for actions that should be automatic
- If a modifier prevents a condition, don't check that same condition again inside the function

SECURITY - ACCESS CONTROL (CRITICAL):
- Functions that add/remove roles, authorized addresses, or modify access control MUST have admin/owner-only modifiers
- Example: addEducationalInstitution(), addEmployer(), addRole() MUST have onlyAdmin or onlyOwner modifier
- NEVER make role management functions public without access control
- If contract has roles (institutions, employers, etc.), there MUST be an admin/owner who can manage them
- WRONG: function addEducationalInstitution(address) external { ... }  // No access control!
- CORRECT: function addEducationalInstitution(address) external onlyAdmin { ... }  // Admin only!

OUTPUT: Complete, compilable Solidity contract with all specified functionality.
"""

        # Build imports and inheritance
        imports = self._build_custom_imports(profile)
        inheritance = self._build_custom_inheritance(profile)
        
        return system_prompt, user_prompt, imports, inheritance
    
    def _format_state_vars(self, state_vars: List[Dict]) -> str:
        """Format state variables for prompt"""
        if not state_vars:
            return "  (None specified - design appropriate data structures)"
        
        lines = []
        for var in state_vars:
            name = var.get('name', 'unknown')
            type_ = var.get('type', 'uint256')
            vis = var.get('visibility', 'private')
            desc = var.get('description', '')
            lines.append(f"  - {name}: {type_} ({vis}) - {desc}")
        return "\n".join(lines)
    
    def _format_functions(self, functions: List[Dict]) -> str:
        """Format functions for prompt"""
        if not functions:
            return "  (None specified - design appropriate interface)"
        
        lines = []
        for func in functions:
            name = func.get('name', 'unknown')
            vis = func.get('visibility', 'public')
            desc = func.get('description', '')
            restricted = func.get('restricted_to', '')
            
            func_str = f"  - {name}() [{vis}]"
            if restricted:
                func_str += f" [access: {restricted}]"
            if desc:
                func_str += f": {desc}"
            lines.append(func_str)
        return "\n".join(lines)
    
    def _format_events(self, events: List[Dict]) -> str:
        """Format events for prompt"""
        if not events:
            return "  (Design appropriate events for state changes)"
        
        lines = []
        for event in events:
            name = event.get('name', 'unknown')
            params = event.get('parameters', [])
            param_str = ', '.join(f"{p.get('type', 'uint256')} {p.get('name', '')}" for p in params)
            lines.append(f"  - {name}({param_str})")
        return "\n".join(lines)
    
    def _build_template_imports(self, profile: 'ContractProfile') -> List[str]:
        """Build imports for template contracts"""
        imports = []
        
        if profile.category == "ERC20":
            imports.append("@openzeppelin/contracts/token/ERC20/ERC20.sol")
            if "Burnable" in profile.extensions:
                imports.append("@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol")
            if "Capped" in profile.extensions:
                imports.append("@openzeppelin/contracts/token/ERC20/extensions/ERC20Capped.sol")
        
        elif profile.category == "ERC721":
            imports.append("@openzeppelin/contracts/token/ERC721/ERC721.sol")
            if "Enumerable" in profile.extensions:
                imports.append("@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol")
            if "URIStorage" in profile.extensions:
                imports.append("@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol")
        
        elif profile.category == "Governor":
            imports.extend([
                "@openzeppelin/contracts/governance/Governor.sol",
                "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol",
                "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol",
                "@openzeppelin/contracts/governance/extensions/GovernorVotesQuorumFraction.sol",
            ])
        
        elif profile.category == "Staking":
            imports.extend([
                "@openzeppelin/contracts/token/ERC20/IERC20.sol",
                "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol",
            ])
        
        # Add access control
        if profile.access_control == "single_owner":
            imports.append("@openzeppelin/contracts/access/Ownable.sol")
        elif profile.access_control == "role_based":
            imports.append("@openzeppelin/contracts/access/AccessControl.sol")
        
        # Add security features
        if "ReentrancyGuard" in profile.security_features:
            imports.append("@openzeppelin/contracts/utils/ReentrancyGuard.sol")
        if "Pausable" in profile.security_features:
            imports.append("@openzeppelin/contracts/utils/Pausable.sol")
        
        return list(dict.fromkeys(imports))  # Dedupe
    
    def _build_template_inheritance(self, profile: 'ContractProfile') -> List[str]:
        """Build inheritance chain for template contracts"""
        parts = []
        
        if profile.category == "ERC20":
            parts.append("ERC20")
            if "Burnable" in profile.extensions:
                parts.append("ERC20Burnable")
        elif profile.category == "ERC721":
            parts.append("ERC721")
            if "Enumerable" in profile.extensions:
                parts.append("ERC721Enumerable")
            if "URIStorage" in profile.extensions:
                parts.append("ERC721URIStorage")
        elif profile.category == "Governor":
            parts.extend(["Governor", "GovernorSettings", "GovernorVotes", "GovernorVotesQuorumFraction"])
        
        # Add security features
        if "ReentrancyGuard" in profile.security_features:
            parts.append("ReentrancyGuard")
        if "Pausable" in profile.security_features:
            parts.append("Pausable")
        
        # Add access control (last for proper linearization)
        if profile.access_control == "single_owner":
            parts.append("Ownable")
        elif profile.access_control == "role_based":
            parts.append("AccessControl")
        
        return parts
    
    def _build_custom_imports(self, profile: 'ContractProfile') -> List[str]:
        """Build imports for custom contracts"""
        imports = []
        
        # Access control
        if profile.access_control == "single_owner":
            imports.append("@openzeppelin/contracts/access/Ownable.sol")
        elif profile.access_control == "role_based":
            imports.append("@openzeppelin/contracts/access/AccessControl.sol")
        
        # Security features
        if "ReentrancyGuard" in profile.security_features:
            imports.append("@openzeppelin/contracts/utils/ReentrancyGuard.sol")
        if "Pausable" in profile.security_features:
            imports.append("@openzeppelin/contracts/utils/Pausable.sol")
        
        return imports
    
    def _build_custom_inheritance(self, profile: 'ContractProfile') -> List[str]:
        """Build inheritance for custom contracts"""
        parts = []
        
        # Access control
        if profile.access_control == "single_owner":
            parts.append("Ownable")
        elif profile.access_control == "role_based":
            parts.append("AccessControl")
        
        # Security features
        if "ReentrancyGuard" in profile.security_features:
            parts.append("ReentrancyGuard")
        if "Pausable" in profile.security_features:
            parts.append("Pausable")
        
        return parts


def build_prompts_dynamic(
    json_spec: Dict,
    profile: 'ContractProfile',
    classification: Dict,
    coverage: 'SpecCoverage',
    debug: bool = False
) -> Tuple[str, str, List[str], List[str]]:
    """
    Build prompts dynamically based on classification.
    
    Returns:
        (system_prompt, user_prompt, imports, inheritance)
    """
    builder = DynamicPromptBuilder(debug=debug)
    return builder.build_prompts(json_spec, profile, classification, coverage)
