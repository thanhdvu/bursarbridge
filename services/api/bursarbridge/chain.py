"""Honest anchor interface: local commitments have no transaction hashes."""

import json
import os
import threading
from functools import wraps
from pathlib import Path

from .engine import DomainError, require
from .store import merkle, verify

ABI = [
    {
        "type": "function",
        "name": "count",
        "stateMutability": "view",
        "inputs": [],
        "outputs": [{"name": "", "type": "uint256"}],
    },
    {
        "type": "function",
        "name": "anchor",
        "stateMutability": "nonpayable",
        "inputs": [
            {"name": "root", "type": "bytes32"},
            {"name": "first", "type": "uint256"},
            {"name": "last", "type": "uint256"},
        ],
        "outputs": [],
    },
    {
        "type": "function",
        "name": "roots",
        "stateMutability": "view",
        "inputs": [{"name": "index", "type": "uint256"}],
        "outputs": [{"name": "", "type": "bytes32"}],
    },
]


def serialized(method):
    @wraps(method)
    def call(self, *args, **kwargs):
        with self.lock:
            return method(self, *args, **kwargs)

    return call


class Chain:
    def __init__(self, mode=None):
        runtime = Path(__file__).resolve().parents[1] / "runtime"
        deployment = runtime / "chain-deployment.json"
        self.deployed = json.loads(deployment.read_text()) if deployment.exists() else {}
        self.mode = mode or os.getenv("CHAIN_MODE", "fisco" if self.deployed else "local")
        self.rpc = os.getenv("FISCO_RPC", "http://127.0.0.1:8545")
        self.address = os.getenv("AUDIT_CONTRACT") or self.deployed.get("AuditAnchor", {}).get("address", "")
        self.registry_address = os.getenv("CREDENTIAL_CONTRACT") or self.deployed.get(
            "CredentialRegistry", {}
        ).get("address", "")
        self.key_path = runtime / "fisco-account.key"
        self.lock = threading.RLock()

    def client(self):
        from web3 import Web3
        from web3.middleware import ExtraDataToPOAMiddleware

        client = Web3(Web3.HTTPProvider(self.rpc, request_kwargs={"timeout": 5}))
        client.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        return client

    def send(self, function):
        with self.lock:
            web3 = self.client()
            key = os.getenv("FISCO_PRIVATE_KEY") or self.key_path.read_text(encoding="utf-8")
            account = web3.eth.account.from_key(key)
            tx = function.build_transaction(
                {
                    "from": account.address,
                    "nonce": web3.eth.get_transaction_count(account.address),
                    "gas": 3000000,
                    "gasPrice": 0,
                    "chainId": web3.eth.chain_id,
                }
            )
            signed = account.sign_transaction(tx)
            receipt = web3.eth.wait_for_transaction_receipt(
                web3.eth.send_raw_transaction(signed.raw_transaction), timeout=30, poll_latency=0.2
            )
            require(receipt.status == 1, "CHAIN_FAILED", "Transaction reverted", 503)
            return {
                "txHash": "0x" + receipt.transactionHash.hex().removeprefix("0x"),
                "blockNumber": receipt.blockNumber,
            }

    def registry(self):
        abi = [
            {
                "type": "function",
                "name": "status",
                "stateMutability": "view",
                "inputs": [{"name": "hash", "type": "bytes32"}],
                "outputs": [{"name": "", "type": "uint8"}],
            },
            {
                "type": "function",
                "name": "setStatus",
                "stateMutability": "nonpayable",
                "inputs": [{"name": "hash", "type": "bytes32"}, {"name": "value", "type": "uint8"}],
                "outputs": [],
            },
        ]
        return self.client().eth.contract(address=self.registry_address, abi=abi)

    @serialized
    def register(self, s):
        if self.mode != "fisco":
            return
        require(self.available(), "CHAIN_UNAVAILABLE", "Registry unavailable", 503)
        for cred in s["credentials"].values():
            if self.credential_valid(cred["hash"]):
                continue  # A timed-out receipt may already have landed; do not re-register.
            function = self.registry().functions.setStatus(bytes.fromhex(cred["hash"]), 1)
            cred["chainTx"] = self.send(function)

    def credential_valid(self, hash_):
        if self.mode != "fisco":
            return True
        try:
            return self.registry().functions.status(bytes.fromhex(hash_)).call() == 1
        except Exception as exc:
            raise DomainError(
                "CHAIN_UNAVAILABLE", "Credential registry unavailable; writes paused", 503
            ) from exc

    def status(self):
        if self.mode == "local":
            return {
                "network": "Local hash chain (NO FISCO anchoring)",
                "connected": False,
                "blockNumber": 0,
                "contracts": [],
                "mode": "local",
            }
        try:
            web3 = self.client()
            connected = (
                web3.is_connected() and bool(self.address) and len(web3.eth.get_code(self.address)) > 0
            )
            return {
                "network": "FISCO BCOS (team-operated, 4 nodes)",
                "connected": connected,
                "blockNumber": web3.eth.block_number if connected else 0,
                "contracts": [{"name": name, "address": d["address"]} for name, d in self.deployed.items()],
                "mode": "fisco",
            }
        except Exception:
            return {
                "network": "FISCO BCOS (team-operated, 4 nodes)",
                "connected": False,
                "blockNumber": 0,
                "contracts": [],
                "mode": "fisco",
            }

    def available(self):
        return self.mode == "local" or self.status()["connected"]

    @serialized
    def anchor(self, s):
        require(verify(s["audit"])["ok"], "AUDIT_INVALID", "Cannot anchor corrupted audit", 409)
        first = s["anchors"][-1]["lastSeq"] + 1 if s["anchors"] else 1
        last = len(s["audit"])
        if first > last:
            return None
        root = merkle([e["hash"] for e in s["audit"][first - 1 : last]])
        result = {"root": root, "firstSeq": first, "lastSeq": last, "at": s["now"], "mode": self.mode}
        if self.mode == "fisco":
            try:
                web3 = self.client()
                contract = web3.eth.contract(address=self.address, abi=ABI)
                index = contract.functions.count().call()
                result.update(self.send(contract.functions.anchor(bytes.fromhex(root), first, last)))
                result.update({"contract": self.address, "index": index})
            except DomainError:
                raise
            except Exception as exc:
                raise DomainError(
                    "CHAIN_UNAVAILABLE", "Real FISCO anchoring failed; no hash fabricated", 503
                ) from exc
        s["anchors"].append(result)
        return result

    def verify(self, s):
        result = verify(s["audit"])
        result["anchors"] = len(s["anchors"])
        if not result["ok"]:
            return result
        for a in s["anchors"]:
            root = merkle([e["hash"] for e in s["audit"][a["firstSeq"] - 1 : a["lastSeq"]]])
            if root != a["root"]:
                return {
                    **result,
                    "ok": False,
                    "firstBadSeq": a["firstSeq"],
                    "detail": "Merkle commitment mismatch",
                }
            if a["mode"] == "fisco":
                try:
                    web3 = self.client()
                    receipt = web3.eth.get_transaction_receipt(a["txHash"])
                    contract = web3.eth.contract(address=a["contract"], abi=ABI)
                    stored = contract.functions.roots(a["index"]).call().hex()
                    transaction = web3.eth.get_transaction(a["txHash"])
                    function, args = contract.decode_function_input(transaction["input"])
                    if (
                        receipt.status != 1
                        or stored.removeprefix("0x") != root
                        or receipt["to"] != a["contract"]
                        or function.fn_name != "anchor"
                        or args["first"] != a["firstSeq"]
                        or args["last"] != a["lastSeq"]
                        or args["root"].hex() != root
                    ):
                        return {**result, "ok": False, "detail": "On-chain root or receipt mismatch"}
                except Exception:
                    return {**result, "ok": False, "detail": "Cannot verify real anchor: RPC unavailable"}
        return {**result, "mode": self.mode, "onChain": any(a["mode"] == "fisco" for a in s["anchors"])}
