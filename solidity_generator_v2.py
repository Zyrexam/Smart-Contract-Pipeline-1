from openai import OpenAI
import json
import os
from typing import Dict, List, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError(
        "OpenAI API key not found. Set `OPENAI_API_KEY` in a .env file or in your environment."
    )

client = OpenAI(api_key=API_KEY)

# ============================================================================
# CATEGORY DEFINITIONS AND PATTERNS
# ============================================================================

CATEGORY_PATTERNS = {
    "ERC20": {
        "imports": [
            'import "@openzeppelin/contracts/token/ERC20/ERC20.sol";',
            'import "@openzeppelin/contracts/access/Ownable.sol";'
        ],
        "inheritance": ["ERC20", "Ownable"],
        "constructor_base": 'ERC20("{name}", "{symbol}")',
        "standard": "ERC20",
        "description": "Standard ERC20 token with OpenZeppelin implementation"
    },
    "ERC721": {
        "imports": [
            'import "@openzeppelin/contracts/token/ERC721/ERC721.sol";',
            'import "@openzeppelin/contracts/access/Ownable.sol";'
        ],
        "inheritance": ["ERC721", "Ownable"],
        "constructor_base": 'ERC721("{name}", "{symbol}")',
        "standard": "ERC721",
        "description": "Standard ERC721 NFT with OpenZeppelin implementation"
    },
    "ERC1155": {
        "imports": [
            'import "@openzeppelin/contracts/token/ERC1155/ERC1155.sol";',
            'import "@openzeppelin/contracts/access/Ownable.sol";'
        ],
        "inheritance": ["ERC1155", "Ownable"],
        "constructor_base": 'ERC1155("{uri}")',
        "standard": "ERC1155",
        "description": "Standard ERC1155 multi-token with OpenZeppelin implementation"
    },
    "GOVERNANCE": {
        "imports": [
            'import "@openzeppelin/contracts/governance/Governor.sol";',
            'import "@openzeppelin/contracts/governance/extensions/GovernorSettings.sol";',
            'import "@openzeppelin/contracts/governance/extensions/GovernorCountingSimple.sol";',
            'import "@openzeppelin/contracts/governance/extensions/GovernorVotes.sol";'
        ],
        "inheritance": ["Governor", "GovernorSettings", "GovernorCountingSimple", "GovernorVotes"],
        "standard": "Governor",
        "description": "Governance contract using OpenZeppelin Governor pattern"
    },
    "CUSTOM": {
        "imports": [],
        "inheritance": [],
        "standard": "Custom",
        "description": "Custom contract implementation"
    }
}

# Access control patterns
ACCESS_CONTROL_PATTERNS = {
    "single_owner": {
        "import": 'import "@openzeppelin/contracts/access/Ownable.sol";',
        "inheritance": "Ownable",
        "modifier": "onlyOwner"
    },
    "role_based": {
        "import": 'import "@openzeppelin/contracts/access/AccessControl.sol";',
        "inheritance": "AccessControl",
        "requires_role_definition": True
    }
}

# ============================================================================
# STAGE 2.1: CATEGORY DETECTION AND PLANNING
# ============================================================================

def detect_contract_category(json_spec: dict) -> str:
    """
    Detect the contract category from JSON specification.
    
    Args:
        json_spec: Structured JSON from Stage 1
    
    Returns:
        str: Detected category (ERC20, ERC721, CUSTOM, etc.)
    """
    contract_type = json_spec.get("contract_type", "").upper()
    
    # Direct mapping from contract_type
    if "ERC20" in contract_type or "TOKEN" in contract_type:
        return "ERC20"
    elif "ERC721" in contract_type or "NFT" in contract_type:
        return "ERC721"
    elif "ERC1155" in contract_type:
        return "ERC1155"
    elif "GOVERN" in contract_type:
        return "GOVERNANCE"
    
    # Check for standard functions that indicate token types
    functions = json_spec.get("functions", [])
    function_names = [f.get("name", "").lower() for f in functions]
    
    if "transfer" in function_names and "balanceof" in function_names:
        return "ERC20"
    elif "safetransferfrom" in function_names and "ownerof" in function_names:
        return "ERC721"
    
    return "CUSTOM"


def plan_contract_structure(json_spec: dict, category: str) -> Dict:
    """
    Create a structured plan for contract generation.
    
    Args:
        json_spec: JSON specification from Stage 1
        category: Detected category
    
    Returns:
        dict: Contract structure plan
    """
    pattern = CATEGORY_PATTERNS.get(category, CATEGORY_PATTERNS["CUSTOM"])
    
    # Detect access control pattern
    roles = json_spec.get("roles", [])
    access_control = "single_owner" if len(roles) <= 1 else "role_based"
    
    plan = {
        "category": category,
        "contract_name": json_spec.get("contract_name", "GeneratedContract"),
        "imports": pattern["imports"].copy(),
        "inheritance": pattern["inheritance"].copy(),
        "access_control": access_control,
        "state_variables": json_spec.get("state_variables", []),
        "roles": roles,
        "functions": json_spec.get("functions", []),
        "events": json_spec.get("events", []),
        "modifiers": json_spec.get("modifiers", []),
        "constructor_base": pattern.get("constructor_base", ""),
        "standard": pattern["standard"]
    }
    
    # Add access control imports
    ac_pattern = ACCESS_CONTROL_PATTERNS[access_control]
    if ac_pattern["import"] not in plan["imports"]:
        plan["imports"].append(ac_pattern["import"])
    if ac_pattern["inheritance"] not in plan["inheritance"]:
        plan["inheritance"].append(ac_pattern["inheritance"])
    
    return plan


# ============================================================================
# STAGE 2.2: ENHANCED SYSTEM PROMPTS BY CATEGORY
# ============================================================================

def get_category_specific_prompt(category: str, plan: Dict) -> str:
    """Return category-specific generation instructions for the given plan.

    This function is the main way Stage 2 adapts to different categories
    (ERC20, ERC721, ERC1155, governance, custom, etc.).
    """

    base_instructions = """You are an expert Solidity smart contract developer.
Generate secure, production-ready Solidity code following these requirements:

GENERAL REQUIREMENTS:
1. Use Solidity ^0.8.20 with built-in overflow checks
2. Follow checks-effects-interactions pattern
3. Include comprehensive NatSpec documentation (@notice, @dev, @param, @return)
4. Emit events for all state-changing operations
5. Use custom errors (Solidity 0.8.4+) instead of require strings
6. Follow naming conventions: contracts (PascalCase), functions (camelCase), constants (UPPER_CASE)
7. Optimize for gas efficiency
8. Include SPDX license identifier (MIT)
"""

    # Category-specific hints for all supported patterns. If a category is not
    # present here, we fall back to the CUSTOM profile below.
    category_instructions = {
        "ERC20": """
CATEGORY-SPECIFIC REQUIREMENTS (ERC20):
- MUST inherit from OpenZeppelin's ERC20 and Ownable
- DO NOT reimplement transfer, balanceOf, approve, allowance - use inherited versions
- Add custom functionality (mint, burn, etc.) as extensions
- Use _mint() and _burn() internal functions from ERC20 base
- Constructor must call ERC20(name, symbol) and Ownable()
- If minting is needed, add mint() function with onlyOwner or role-based modifier
- Emit Transfer events through base ERC20 (automatic)
- Initial supply should use _mint(msg.sender, amount * 10**decimals())
""",
        "ERC721": """
CATEGORY-SPECIFIC REQUIREMENTS (ERC721):
- MUST inherit from OpenZeppelin's ERC721 and Ownable
- DO NOT reimplement transferFrom, ownerOf, balanceOf - use inherited versions
- Constructor must call ERC721(name, symbol) and Ownable()
- Use _safeMint() for minting new tokens
- Implement custom metadata/tokenURI logic if needed
- Use incremental tokenIds starting from 1
- Emit Transfer events through base ERC721 (automatic)
""",
        "ERC1155": """
CATEGORY-SPECIFIC REQUIREMENTS (ERC1155):
- MUST inherit from OpenZeppelin's ERC1155 and Ownable
- Constructor must call ERC1155(uri) and Ownable()
- Use _mint() / _mintBatch() and _burn() / _burnBatch() for token operations
- DO NOT reimplement safeTransferFrom / safeBatchTransferFrom - use inherited versions
- Use ids and amounts arrays consistently for batch operations
- Emit TransferSingle / TransferBatch events through base ERC1155 (automatic)
""",
        "GOVERNANCE": """
CATEGORY-SPECIFIC REQUIREMENTS (GOVERNANCE/GOVERNOR):
- Inherit from OpenZeppelin Governor + relevant extensions (as specified in the plan)
- Implement required virtual functions (e.g. votingDelay, votingPeriod, quorum, proposalThreshold)
- Ensure proposal creation, voting and execution flows follow OZ Governor patterns
- Use a Votes-compatible token (ERC20Votes) or similar for voting power
- Emit proposal and voting events provided by the Governor base contracts
""",
        "CUSTOM": """
CATEGORY-SPECIFIC REQUIREMENTS (CUSTOM):
- Implement all functionality from scratch
- Add appropriate access control (Ownable or AccessControl)
- Define all state variables, events, and modifiers explicitly
- Include reentrancy guards for functions handling ETH or external calls
- Validate all inputs and handle edge cases
"""
    }

    role_instructions = ""
    if plan["access_control"] == "role_based":
        role_instructions = """
ACCESS CONTROL (Role-Based):
- Inherit from OpenZeppelin AccessControl
- Define role constants: bytes32 public constant ROLE_NAME = keccak256("ROLE_NAME")
- Grant DEFAULT_ADMIN_ROLE to deployer in constructor
- Use hasRole() or onlyRole modifier for access checks
- Setup roles in constructor: _grantRole(ROLE_NAME, address)
"""
    else:
        role_instructions = """
ACCESS CONTROL (Single Owner):
- Inherit from OpenZeppelin Ownable
- Use onlyOwner modifier for restricted functions
- Constructor automatically sets deployer as owner
"""

    return base_instructions + category_instructions.get(category, category_instructions["CUSTOM"]) + role_instructions


# ============================================================================
# STAGE 2.3: GENERATE SOLIDITY CODE WITH CATEGORY AWARENESS
# ============================================================================

def generate_solidity_code(json_spec: dict) -> Tuple[str, Dict]:
    """Generate category-aware Solidity smart contract code from a Stage 1 spec.

    Stage 2 takes ONLY the structured JSON from Stage 1 as input. It does not
    consume the original natural-language user prompt; all information must be
    encoded in ``json_spec``.

    Args:
        json_spec: Structured JSON specification from Stage 1.

    Returns:
        tuple: (solidity_code, generation_metadata)
    """
    
    # Step 1: Detect category and create plan
    print("  🔍 Detecting contract category...")
    category = detect_contract_category(json_spec)
    print(f"  ✓ Category detected: {category}")
    
    print("  📋 Planning contract structure...")
    plan = plan_contract_structure(json_spec, category)
    print(f"  ✓ Plan created: {plan['standard']} with {plan['access_control']} access control")
    
    # Step 2: Prepare enhanced prompts
    system_prompt = get_category_specific_prompt(category, plan)
    
    # Step 3: Create structured user prompt
    spec_string = json.dumps(json_spec, indent=2)
    plan_string = json.dumps({
        "category": plan["category"],
        "standard": plan["standard"],
        "imports": plan["imports"],
        "inheritance": plan["inheritance"],
        "access_control": plan["access_control"]
    }, indent=2)
    
    user_prompt = f"""Generate a complete Solidity smart contract with the following:


STRUCTURED SPECIFICATION (from Stage 1):
{spec_string}

CONTRACT GENERATION PLAN:
{plan_string}

CRITICAL INSTRUCTIONS:
1. Follow the category-specific requirements for {category}
2. Use OpenZeppelin imports and inheritance as specified in the plan
3. DO NOT reimplement standard functions - extend the base contracts
4. Ensure ALL functions from the specification are implemented
5. Add proper NatSpec documentation
6. Use custom errors with descriptive names
7. Include security best practices (reentrancy guards, input validation)

Output ONLY the complete Solidity contract code, no explanations."""

    # Step 4: Generate code
    print("  🤖 Generating Solidity code...")
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.2  # Lower temperature for more consistent standard compliance
    )
    
    solidity_code = response.choices[0].message.content
    
    if solidity_code is None:
        raise RuntimeError("No content returned by the model in Stage 2")
    
    # Step 5: Clean up output
    if solidity_code.startswith("```solidity"):
        solidity_code = solidity_code.replace("```solidity", "").replace("```", "").strip()
    elif solidity_code.startswith("```"):
        solidity_code = solidity_code.replace("```", "").strip()
    
    # Step 6: Ensure proper headers
    if "SPDX-License-Identifier" not in solidity_code:
        solidity_code = "// SPDX-License-Identifier: MIT\n" + solidity_code
    
    if "pragma solidity" not in solidity_code:
        lines = solidity_code.split('\n')
        for i, line in enumerate(lines):
            if line.startswith("// SPDX"):
                lines.insert(i + 1, "pragma solidity ^0.8.20;\n")
                break
        solidity_code = '\n'.join(lines)
    
    # Metadata about generation
    metadata = {
        "category": category,
        "standard": plan["standard"],
        "access_control": plan["access_control"],
        "imports_used": plan["imports"],
        "inheritance": plan["inheritance"]
    }
    
    return solidity_code, metadata


# ============================================================================
# TESTING
# ============================================================================

if __name__ == "__main__":
    # Test with ERC20 example
    test_spec = {
        "contract_name": "MyToken",
        "contract_type": "ERC20",
        "description": "A mintable ERC20 token",
        "state_variables": [
            {"name": "name", "type": "string", "visibility": "public", "initial_value": "MyToken"},
            {"name": "symbol", "type": "string", "visibility": "public", "initial_value": "MTK"}
        ],
        "roles": [
            {"name": "owner", "permissions": ["mint"]}
        ],
        "functions": [
            {
                "name": "mint",
                "visibility": "public",
                "inputs": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}],
                "outputs": [],
                "restricted_to": "owner",
                "description": "Mint new tokens"
            }
        ],
        "events": [
            {"name": "TokensMinted", "parameters": [{"name": "to", "type": "address"}, {"name": "amount", "type": "uint256"}]}
        ]
    }
    
    # test_input = """
    # Create an ERC20 token called MyToken (MTK) with:
    # - 1 million initial supply
    # - Owner can mint new tokens
    # - Standard transfer functionality
    # """
    
    print("Testing Enhanced Stage 2: Code Generation")
    print("=" * 80)
    
    try:
        code, metadata = generate_solidity_code(test_spec)
        
        print("\n✅ Generation Complete!")
        print(f"Category: {metadata['category']}")
        print(f"Standard: {metadata['standard']}")
        print(f"Access Control: {metadata['access_control']}")
        print("\nGenerated Code:")
        print("=" * 80)
        print(code)
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error: {e}")