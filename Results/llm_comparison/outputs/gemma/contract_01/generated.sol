pragma solidity ^0.8.20;

contract RentalNFT {

    // NFT contract address
    address public immutable_nft_contract;

    // NFT token name
    string public immutable_token_name;

    // NFT token symbol
    string public immutable_token_symbol;

    // NFT contract address
    address public immutable_rental_contract;

    // NFT token name
    string public immutable_rental_token_name;

    // NFT token symbol
    string public immutable_rental_token_symbol;

    // NFT token id
    uint256 public immutable_token_id;

    // User address
    address public user;

    // NFT token address
    address public token;

    // Rental duration in seconds
    uint256 public rental_duration;

    // Rental price
    uint256 public rental_price;

    // Mapping of NFT ids to rental data
    mapping(uint256 => RentalData) public rentals;

    // Event emitted when a NFT is rented
    event RentalCreated(uint256 indexed);

    // Event emitted when an NFT is returned
    event RentalReturned(uint256 indexed);

    constructor(
        address _nft_contract,
        string memory _token_name,
        string memory _token_symbol,
        address _rental_contract,
        string memory _rental_token_name,
        string memory _rental_token_symbol,
        uint256 _token_id,
        address _user,
        uint256 _rental_duration,
        uint256 _rental_price
    ) {
        immutable_nft_contract = _nft_contract;
        immutable_token_name = _token_name;
        immutable_token_symbol = _token_symbol;
        immutable_rental_contract = _rental_contract;
        immutable_rental_token_name = _rental_token_name;
        immutable_rental_token_symbol = _rental_token_symbol;
        immutable_token_id = _token_id;
        user = _user;
        token = _token;
        rental_duration = _rental_duration;
        rental_price = _rental_price;
    }

    // Function to create a rental
    function createRental() public {
        // Create a new rental entry
        rentals[immutable_token_id] = RentalData(
            token,
            user,
            ImmutableDateTime.now() + rental_duration,
            rental_price
        );

        // Emit event
        emit RentalCreated(rentals[immutable_token_id].index);
    }

    // Function to return an NFT
    function returnRental() public {
        // Check if the NFT is currently rented
        require(rentals[immutable_token_id].user == address(0), "NFT is not rented");

        // Remove the rental entry from the mapping
        delete rentals[immutable_token_id];

        // Emit event
        emit RentalReturned(immutable_token_id);
    }
}