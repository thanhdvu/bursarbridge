"""Deploy to the real local FISCO Web3 RPC. Persist secrets only in runtime/."""

import json
import os
from pathlib import Path

from web3 import Web3

root = Path(__file__).resolve().parents[3]
runtime = root / "services/api/runtime"
runtime.mkdir(exist_ok=True)
key_path = runtime / "fisco-account.key"
if not key_path.exists():
    key_path.write_text(Web3().eth.account.create().key.hex(), encoding="utf-8")
web3 = Web3(
    Web3.HTTPProvider(os.getenv("FISCO_RPC", "http://127.0.0.1:8545"), request_kwargs={"timeout": 10})
)
account = web3.eth.account.from_key(key_path.read_text(encoding="utf-8"))
assert web3.is_connected(), "Real FISCO RPC required"
deployed = {}
for name in ("AuditAnchor", "CredentialRegistry", "MandateGuard"):
    artifact = json.loads((root / "contracts/artifacts" / (name + ".json")).read_text())
    factory = web3.eth.contract(abi=artifact["abi"], bytecode=artifact["evm"]["bytecode"]["object"])
    tx = factory.constructor().build_transaction(
        {
            "from": account.address,
            "nonce": web3.eth.get_transaction_count(account.address),
            "gas": 10000000,
            "gasPrice": 0,
            "chainId": web3.eth.chain_id,
        }
    )
    signed = account.sign_transaction(tx)
    receipt = web3.eth.wait_for_transaction_receipt(
        web3.eth.send_raw_transaction(signed.raw_transaction), timeout=60
    )
    assert receipt.status == 1 and web3.eth.get_code(receipt.contractAddress), f"Deployment failed: {name}"
    deployed[name] = {
        "address": receipt.contractAddress,
        "txHash": "0x" + receipt.transactionHash.hex().removeprefix("0x"),
        "blockNumber": receipt.blockNumber,
    }
    print(name, receipt.contractAddress, deployed[name]["txHash"])
(runtime / "chain-deployment.json").write_text(json.dumps(deployed, indent=2), encoding="utf-8")
print("Real deployments persisted in ignored runtime/chain-deployment.json. No key printed.")
