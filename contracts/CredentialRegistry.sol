// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract CredentialRegistry {
    address public immutable owner;
    mapping(bytes32 => uint8) public status; // 0 absent, 1 valid, 2 revoked
    event CredentialStatus(bytes32 indexed credentialHash, uint8 status);
    constructor() { owner = msg.sender; }
    function setStatus(bytes32 credentialHash, uint8 value) external {
        require(msg.sender == owner, "owner only");
        require(value == 1 || value == 2, "invalid status");
        status[credentialHash] = value;
        emit CredentialStatus(credentialHash, value);
    }
}
