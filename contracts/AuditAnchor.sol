// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// Hashes and ranges only: no personal data or value on chain.
contract AuditAnchor {
    address public immutable owner;
    bytes32[] public roots;
    event Anchored(uint256 indexed index, bytes32 root, uint256 firstSeq, uint256 lastSeq);
    constructor() { owner = msg.sender; }
    function anchor(bytes32 root, uint256 first, uint256 last) external {
        require(msg.sender == owner, "owner only");
        require(root != bytes32(0) && first > 0 && last >= first, "invalid range");
        roots.push(root);
        emit Anchored(roots.length - 1, root, first, last);
    }
    function count() external view returns (uint256) { return roots.length; }
}
