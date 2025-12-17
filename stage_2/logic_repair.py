# solidity_code_generator/logic_repair.py

"""
Repair semantic and logic issues in generated Solidity code
"""

from openai import OpenAI
from .repair import strip_markdown_fences, ensure_headers


def repair_semantic_issues(client: OpenAI, solidity_code: str, semantic_errors: list, json_spec: dict, debug: bool = False) -> str:
    """
    Repair semantic/logic issues using GPT-4o with targeted prompts
    """
    
    if not semantic_errors:
        return solidity_code
    
    if debug:
        print(f"[LogicRepair] Repairing {len(semantic_errors)} semantic issues...")
    
    # Build category-specific repair guidance
    repair_guidance = _build_repair_guidance(solidity_code, semantic_errors, json_spec)
    
    system_prompt = """You are an expert Solidity architect specializing in fixing logic and semantic issues.

CRITICAL RULES:

1. Fix ONLY the specific logic/semantic issues mentioned
2. Preserve all working code and business logic
3. Output compilable Solidity ^0.8.20 with OpenZeppelin v5
4. Use proper token lifecycle patterns (mint → transfer → burn)
5. Fix access control conflicts by choosing the right pattern
6. Ensure NFTs are minted before being used
7. Make user-facing functions accessible (don't over-restrict with roles)
8. Use actual token transfers for ERC721 rentals, not just state variables
9. Output ONLY Solidity code, no explanations

OpenZeppelin v5 Requirements:

- Ownable(msg.sender) in constructor
- Use _update override for transfer logic
- AccessControl OR Ownable, not both (unless truly needed)
- Custom errors instead of require strings
- Use _transfer() or transferFrom() for actual token ownership changes"""
    
    user_prompt = f"""Fix the following semantic/logic issues in this Solidity contract:

ISSUES TO FIX:

{chr(10).join(f'{i+1}. {err}' for i, err in enumerate(semantic_errors))}

REPAIR GUIDANCE:

{repair_guidance}

ORIGINAL SPECIFICATION:

{_format_spec_summary(json_spec)}

CURRENT SOLIDITY CODE:

{solidity_code}

Fix these issues while preserving the contract's intended functionality. Return the complete corrected contract."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.1,
    )
    
    fixed_code = response.choices[0].message.content or ""
    fixed_code = strip_markdown_fences(fixed_code)
    fixed_code = ensure_headers(fixed_code)
    
    if debug:
        print(f"[LogicRepair] Repair complete, code length: {len(fixed_code)}")
    
    return fixed_code


def _build_repair_guidance(code: str, errors: list, spec: dict) -> str:
    """Build specific repair guidance based on detected issues"""
    guidance = []
    
    # ERC721 issues
    if any('mint' in err.lower() and 'erc721' in err.lower() for err in errors):
        guidance.append("""
ERC721 MINT FIX:

- Add a mint/safeMint function with access control
- Example:

  function safeMint(address to, uint256 tokenId) public onlyOwner {
      _safeMint(to, tokenId);
  }

- For rental systems: mint NFTs first, then transfer/rent them
""")
    
    if any('rental' in err.lower() and 'transfer' in err.lower() for err in errors):
        guidance.append("""
NFT RENTAL PATTERN FIX:

- Use actual token transfers, not just state variables
- Pattern:

  1. Owner mints NFT: _safeMint(owner, tokenId)
  2. rentNFT: _transfer(owner, renter, tokenId) OR transferFrom(owner, renter, tokenId)
  3. returnNFT: _transfer(renter, originalOwner, tokenId)

- Track rental metadata in separate mapping (rental start time, duration, etc.)
- Don't create redundant owner tracking - use ERC721.ownerOf(tokenId)
- Remove redundant state variables like 'nftOwner' - ERC721 tracks this
""")
    
    # Access control conflicts
    if any('ownable' in err.lower() and 'accesscontrol' in err.lower() for err in errors):
        guidance.append("""
ACCESS CONTROL CONFLICT FIX:

- Remove one: keep Ownable OR AccessControl, not both
- Decision guide:
  * Single admin/owner → Use Ownable
  * Multiple roles (MINTER, BURNER, etc) → Use AccessControl
  * For rental/marketplace → Usually Ownable is enough
- Remove the unused inheritance and related code
- Update constructor to only initialize the chosen pattern
""")
    
    # Role restrictions on user functions
    if any('role' in err.lower() and 'user-facing' in err.lower() for err in errors):
        guidance.append("""
FUNCTION ACCESS FIX:

- Remove onlyRole from user-facing functions like rent(), buy(), claim()
- Users shouldn't need role grants to use the protocol
- Keep onlyOwner/onlyRole only for admin functions like:
  * mint, setPrice, pause, withdraw, etc
- Example fix:
  function rentNFT(uint256 tokenId) external payable {  // Remove onlyRole
      // rental logic
  }
""")
    
    # ERC20 mint access
    if any('mint' in err.lower() and 'access control' in err.lower() for err in errors):
        guidance.append("""
MINT ACCESS CONTROL FIX:

- Add onlyOwner or onlyRole to mint function
- Example:

  function mint(address to, uint256 amount) public onlyOwner {
      _mint(to, amount);
  }
""")
    
    # OpenZeppelin v5 _setupRole deprecation
    if any('_setupRole' in err.lower() or 'setupRole' in err.lower() for err in errors):
        guidance.append("""
OPENZEPPELIN V5 _setupRole FIX:

- _setupRole() was removed in OpenZeppelin v5
- Replace ALL instances of _setupRole() with _grantRole()
- Example fix in constructor:
  OLD: _setupRole(DEFAULT_ADMIN_ROLE, msg.sender);
  NEW: _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
- Search and replace: _setupRole → _grantRole
""")
    
    # Shadowing issues
    if any('shadow' in err.lower() for err in errors):
        guidance.append("""
SHADOWING FIX:

- Parameter names cannot shadow function names or OpenZeppelin functions
- Rename parameters that conflict with function names
- Common fixes:
  * tokenURI parameter → tokenURIValue, tokenURIParam, or metadataURI
  * ownerOf parameter → ownerOfValue, ownerAddress, or ownerParam
  * balanceOf parameter → balanceOfValue, balanceAmount, or balanceParam
  * transfer parameter → transferValue, transferData, or transferParam

EXAMPLE FIX:
  OLD: function mint(address to, string memory tokenURI) public { ... }
  NEW: function mint(address to, string memory metadataURI) public { ... }
       // Then use metadataURI instead of tokenURI inside the function
""")
    
    if not guidance:
        guidance.append("Fix the listed errors while maintaining contract logic.")
    
    return "\n".join(guidance)


def _format_spec_summary(spec: dict) -> str:
    """Format spec summary for context"""
    summary_parts = [
        f"Contract: {spec.get('contract_name', 'Unknown')}",
        f"Type: {spec.get('contract_type', 'Unknown')}",
        f"Description: {spec.get('description', 'N/A')}"
    ]
    
    functions = spec.get('functions', [])
    if functions:
        summary_parts.append(f"Functions: {', '.join(f.get('name', '?') for f in functions[:5])}")
    
    return "\n".join(summary_parts)

