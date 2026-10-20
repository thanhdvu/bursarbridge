// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// Optional secondary cap/replay guard; the API still validates full consent.
contract MandateGuard {
    address public immutable owner;
    struct Mandate { bytes32 payee; uint256 cap; uint256 spent; uint256 expiry; bool active; }
    mapping(bytes32 => Mandate) public mandates;
    mapping(bytes32 => bool) public usedConsents;
    event Registered(bytes32 indexed mandateHash);
    event Recorded(bytes32 indexed mandateHash, bytes32 consentHash, uint256 amount);
    constructor() { owner = msg.sender; }
    modifier onlyOwner() { require(msg.sender == owner, "owner only"); _; }
    function register(bytes32 id, bytes32 payee, uint256 cap, uint256 expiry) external onlyOwner {
        require(!mandates[id].active && cap > 0, "invalid mandate");
        mandates[id] = Mandate(payee, cap, 0, expiry, true);
        emit Registered(id);
    }
    function revoke(bytes32 id) external onlyOwner { mandates[id].active = false; }
    function checkAndRecord(bytes32 id, bytes32 payee, uint256 amount, bytes32 consent) external onlyOwner {
        Mandate storage m = mandates[id];
        require(m.active && block.timestamp < m.expiry, "inactive");
        require(m.payee == payee && m.spent + amount <= m.cap, "cap/payee mismatch");
        require(!usedConsents[consent] && amount > 0, "replayed/zero");
        usedConsents[consent] = true;
        m.spent += amount;
        emit Recorded(id, consent, amount);
    }
}
