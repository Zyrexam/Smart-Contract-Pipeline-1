# solidity_code_generator/category_patterns.py

"""
Pattern library for common contract categories with correct implementations
"""


ERC721_RENTAL_PATTERN = """
ERC721 RENTAL PATTERN (Correct Implementation):

ARCHITECTURE:

- Inherit ERC721 + Ownable only (NOT AccessControl unless multiple admin roles needed)
- NFTs must be minted before rental
- Use actual token transfers for rental (transferFrom or _transfer)
- Track rental metadata separately from token ownership

KEY FUNCTIONS:

1. mint/safeMint: Create NFTs (onlyOwner)
2. setRentalTerms: Configure rental price/duration per token (onlyOwner)
3. rentNFT: Transfer NFT to renter + record rental data (public/external, payable if ETH)
4. returnNFT: Transfer NFT back to original owner after rental period
5. claimRental: Owner can reclaim after rental period expires

STATE VARIABLES:

- Rental struct: { originalOwner, renter, startTime, duration, pricePerDay }
- mapping(uint256 => Rental) public rentals
- Do NOT create separate owner tracking - use ERC721.ownerOf()

ACCESS PATTERN:

- Admin functions (mint, setTerms): onlyOwner
- User functions (rentNFT): public/external, NO role requirements
- Anyone can rent if they meet conditions (payment, NFT available)

EXAMPLE STRUCTURE:

```solidity
contract NFTRental is ERC721, Ownable {
    struct Rental {
        address originalOwner;
        uint256 startTime;
        uint256 duration;
        uint256 price;
    }
    
    mapping(uint256 => Rental) public rentals;
    uint256 private _tokenIdCounter;
    
    constructor() ERC721("RentalNFT", "RNFT") Ownable(msg.sender) {}
    
    function safeMint(address to) public onlyOwner returns (uint256) {
        uint256 tokenId = _tokenIdCounter++;
        _safeMint(to, tokenId);
        return tokenId;
    }
    
    function rentNFT(uint256 tokenId, uint256 duration) external payable {
        require(msg.value >= calculateRentalCost(tokenId, duration), "Insufficient payment");
        address owner = ownerOf(tokenId);
        
        // Transfer NFT to renter
        _transfer(owner, msg.sender, tokenId);
        
        // Record rental
        rentals[tokenId] = Rental({
            originalOwner: owner,
            startTime: block.timestamp,
            duration: duration,
            price: msg.value
        });
    }
    
    function returnNFT(uint256 tokenId) external {
        Rental memory rental = rentals[tokenId];
        require(block.timestamp >= rental.startTime + rental.duration, "Rental period not over");
        
        // Transfer back to original owner
        _transfer(ownerOf(tokenId), rental.originalOwner, tokenId);
        delete rentals[tokenId];
    }
}
```
"""


ERC721_MARKETPLACE_PATTERN = """
ERC721 MARKETPLACE PATTERN:

ARCHITECTURE:

- Inherit ReentrancyGuard + Ownable
- Do NOT inherit ERC721 (marketplace is separate from NFT contract)
- Use IERC721 interface to interact with external NFT contracts
- Support multiple NFT collections

KEY FUNCTIONS:

1. listItem: Seller lists NFT with price
2. buyItem: Buyer purchases NFT (payable, nonReentrant)
3. cancelListing: Seller cancels listing
4. updateListing: Seller updates price

STATE VARIABLES:

- Listing struct: { seller, price, isActive }
- mapping(address => mapping(uint256 => Listing)) public listings

ACCESS:

- All main functions (list, buy, cancel) are public
- Only platform fee functions need onlyOwner
"""


ERC20_STAKING_PATTERN = """
ERC20 STAKING PATTERN:

ARCHITECTURE:

- Use SafeERC20 for all token operations
- ReentrancyGuard for stake/unstake
- Track user stakes and rewards separately

KEY FUNCTIONS:

1. stake: Lock tokens, start earning (nonReentrant)
2. unstake: Unlock tokens, claim rewards (nonReentrant)
3. claimRewards: Claim without unstaking (nonReentrant)
4. setRewardRate: Admin function (onlyOwner)

CRITICAL:

- Use SafeERC20: stakingToken.safeTransferFrom()
- Calculate rewards before any state changes
- Update state before external calls (checks-effects-interactions)
- Emit events for all state changes

EXAMPLE:

```solidity
contract Staking is ReentrancyGuard, Ownable {
    using SafeERC20 for IERC20;
    
    IERC20 public stakingToken;
    IERC20 public rewardToken;
    
    mapping(address => uint256) public stakedBalances;
    mapping(address => uint256) public rewardDebt;
    
    function stake(uint256 amount) external nonReentrant {
        require(amount > 0, "Cannot stake 0");
        
        // Calculate pending rewards
        _updateRewards(msg.sender);
        
        // Transfer tokens
        stakingToken.safeTransferFrom(msg.sender, address(this), amount);
        
        // Update state
        stakedBalances[msg.sender] += amount;
        
        emit Staked(msg.sender, amount);
    }
}
```
"""


ERC20_TAX_PATTERN = """
ERC20 TAX PATTERN:

ARCHITECTURE:

- Inherit ERC20 + Ownable
- Override _update() for transfer tax logic
- Track treasury address

KEY FUNCTIONS:

1. setTaxRate: Admin sets tax percentage (onlyOwner)
2. setTreasury: Admin sets treasury address (onlyOwner)
3. _update override: Apply tax on transfers

CRITICAL:

- Use _update override (OpenZeppelin v5 pattern)
- Calculate tax before state changes
- Transfer tax to treasury
- Transfer remaining to recipient
- Emit Transfer events correctly

EXAMPLE:

```solidity
contract TaxToken is ERC20, Ownable {
    uint256 public taxRate; // in basis points (100 = 1%)
    address public treasury;
    
    constructor() ERC20("TaxToken", "TAX") Ownable(msg.sender) {
        taxRate = 300; // 3%
        treasury = msg.sender;
    }
    
    function _update(address from, address to, uint256 value) internal override {
        if (from == address(0) || to == address(0) || taxRate == 0) {
            super._update(from, to, value);
            return;
        }
        
        uint256 tax = (value * taxRate) / 10000;
        uint256 afterTax = value - tax;
        
        if (tax > 0) {
            super._update(from, treasury, tax);
        }
        
        super._update(from, to, afterTax);
    }
}
```
"""


ERC1155_PATTERN = """
ERC1155 PATTERN:

ARCHITECTURE:

- Inherit ERC1155 + Ownable or AccessControl
- Support multiple token types (fungible and non-fungible)
- Use _mint and _mintBatch for creation

KEY FUNCTIONS:

1. mint: Mint single token type (onlyOwner/onlyRole)
2. mintBatch: Mint multiple token types (onlyOwner/onlyRole)
3. setURI: Update token metadata URI (onlyOwner)

CRITICAL:

- Use _mint() for single token
- Use _mintBatch() for multiple tokens
- Track balances per token ID
- Support both fungible and non-fungible semantics
"""


DAO_GOVERNANCE_PATTERN = """
DAO GOVERNANCE PATTERN:

ARCHITECTURE:

- Inherit OpenZeppelin Governor + extensions
- Requires a voting token (ERC20Votes)
- Use GovernorSettings, GovernorVotes, GovernorVotesQuorumFraction

KEY COMPONENTS:

1. Voting token must implement ERC20Votes (with checkpoints)
2. Governor contract manages proposals and voting
3. Timelock optional for delayed execution

REQUIRED OVERRIDES:

- votingDelay(): Delay before voting starts
- votingPeriod(): Duration of voting
- quorum(): Minimum votes required
- proposalThreshold(): Tokens needed to propose

DO NOT create custom voting logic - use OpenZeppelin Governor
"""


def get_pattern_for_category(category: str, keywords: list = None) -> str:
    """
    Get implementation pattern based on category and keywords
    """
    category_lower = category.lower()
    keywords_lower = [k.lower() for k in (keywords or [])]
    
    # NFT-related patterns
    if 'erc721' in category_lower or 'nft' in category_lower:
        if any(k in keywords_lower for k in ['rent', 'rental', 'lease']):
            return ERC721_RENTAL_PATTERN
        elif any(k in keywords_lower for k in ['marketplace', 'market', 'buy', 'sell']):
            return ERC721_MARKETPLACE_PATTERN
    
    # Token patterns
    if 'erc20' in category_lower or 'token' in category_lower:
        if any(k in keywords_lower for k in ['stake', 'staking', 'farm']):
            return ERC20_STAKING_PATTERN
        elif any(k in keywords_lower for k in ['tax', 'fee', 'treasury']):
            return ERC20_TAX_PATTERN
    
    # Multi-token
    if 'erc1155' in category_lower or 'multi' in category_lower:
        return ERC1155_PATTERN
    
    # Governance
    if any(k in keywords_lower for k in ['governance', 'dao', 'voting', 'governor']):
        return DAO_GOVERNANCE_PATTERN
    
    return ""

