// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Escrow Contract
/// @notice This contract holds funds in escrow until both buyer and seller approve the transaction.
contract Escrow {
    address public buyer;
    address public seller;
    uint256 public amount;
    
    bool private buyerApproved;
    bool private sellerApproved;

    /// @notice Emitted when funds are deposited into the escrow.
    /// @param amount The amount of funds deposited.
    event FundsDeposited(uint256 amount);

    /// @notice Emitted when a transaction is approved by a party.
    /// @param approver The address of the party that approved the transaction.
    event TransactionApproved(address approver);

    /// @notice Emitted when funds are released to the seller.
    /// @param amount The amount of funds released.
    event FundsReleased(uint256 amount);

    /// @dev Custom error for unauthorized access.
    error Unauthorized();

    /// @dev Custom error for invalid deposit amount.
    error InvalidAmount();

    /// @dev Custom error for already approved transaction.
    error AlreadyApproved();

    /// @dev Custom error for insufficient approvals.
    error InsufficientApprovals();

    /// @notice Constructor to set the buyer and seller addresses.
    /// @param _buyer The address of the buyer.
    /// @param _seller The address of the seller.
    constructor(address _buyer, address _seller) {
        buyer = _buyer;
        seller = _seller;
    }

    /// @notice Allows the buyer to deposit funds into the escrow.
    /// @param _amount The amount of funds to deposit.
    function depositFunds(uint256 _amount) external {
        if (msg.sender != buyer) revert Unauthorized();
        if (_amount <= 0) revert InvalidAmount();

        amount = _amount;
        emit FundsDeposited(_amount);
    }

    /// @notice Allows either party to approve the transaction.
    /// Funds are released when both parties approve.
    function approveTransaction() external {
        if (msg.sender != buyer && msg.sender != seller) revert Unauthorized();

        if (msg.sender == buyer) {
            if (buyerApproved) revert AlreadyApproved();
            buyerApproved = true;
        } else if (msg.sender == seller) {
            if (sellerApproved) revert AlreadyApproved();
            sellerApproved = true;
        }

        emit TransactionApproved(msg.sender);

        if (buyerApproved && sellerApproved) {
            _releaseFunds();
        }
    }

    /// @dev Automatically releases funds to the seller when both parties have approved the transaction.
    function _releaseFunds() private {
        if (!buyerApproved || !sellerApproved) revert InsufficientApprovals();

        uint256 releaseAmount = amount;
        amount = 0;
        payable(seller).transfer(releaseAmount);

        emit FundsReleased(releaseAmount);
    }
}
