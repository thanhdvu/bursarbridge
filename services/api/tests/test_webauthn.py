"""Real signed WebAuthn payloads from a synthetic ES256 authenticator.

This validates challenge/origin/RP/UV/replay binding, not a browser UX ceremony.
"""

import base64
import hashlib
import json
import secrets

import cbor2
import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec


def b64(value):
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


@pytest.mark.parametrize("origin", ["http://localhost:3000", "http://localhost:3700"])
def test_signed_webauthn_mandate_and_receipt_replay(journey, origin):
    j = journey
    j.headers["parent_minh"]["Origin"] = origin
    options = j.ok("POST", "/webauthn/register/options")
    key = ec.generate_private_key(ec.SECP256R1())
    pub = key.public_key().public_numbers()
    cose = cbor2.dumps({1: 2, 3: -7, -1: 1, -2: pub.x.to_bytes(32), -3: pub.y.to_bytes(32)})
    credential_id = secrets.token_bytes(32)
    rp_hash = hashlib.sha256(b"localhost").digest()
    client = json.dumps(
        {"type": "webauthn.create", "challenge": options["challenge"], "origin": origin}
    ).encode()
    auth_data = (
        rp_hash
        + b"\x45"
        + (0).to_bytes(4)
        + b"\x00" * 16
        + len(credential_id).to_bytes(2)
        + credential_id
        + cose
    )
    attestation = cbor2.dumps({"fmt": "none", "attStmt": {}, "authData": auth_data})
    credential = {
        "id": b64(credential_id),
        "rawId": b64(credential_id),
        "type": "public-key",
        "response": {
            "clientDataJSON": b64(client),
            "attestationObject": b64(attestation),
            "transports": ["internal"],
        },
    }
    from copy import deepcopy

    invalid = deepcopy(credential)
    invalid["response"]["clientDataJSON"] = b64(
        json.dumps(
            {
                "type": "webauthn.create",
                "challenge": options["challenge"],
                "origin": "http://evil.localhost:3700",
            }
        ).encode()
    )
    assert j.request("POST", "/webauthn/register/verify", json={"credential": invalid}).status_code == 403
    j.ok("POST", "/webauthn/register/verify", json={"credential": credential})
    m = j.ok(
        "POST",
        "/mandates",
        json={
            "purpose": "tuition",
            "payeeRule": {"type": "credentialed", "issuer": j.app.state.issuer.did},
            "cap": {"amount": "16000000.00", "currency": "KRW"},
            "expiresAt": "2027-06-01T00:00:00Z",
        },
    )
    options = j.ok("POST", "/webauthn/assert/options", json={"purpose": "mandate", "refId": m["id"]})
    client = json.dumps(
        {"type": "webauthn.get", "challenge": options["challenge"], "origin": origin}
    ).encode()
    auth_data = rp_hash + b"\x05" + (1).to_bytes(4)
    signature = key.sign(auth_data + hashlib.sha256(client).digest(), ec.ECDSA(hashes.SHA256()))
    assertion = {
        "id": b64(credential_id),
        "rawId": b64(credential_id),
        "type": "public-key",
        "response": {
            "clientDataJSON": b64(client),
            "authenticatorData": b64(auth_data),
            "signature": b64(signature),
        },
    }
    proof = j.ok("POST", "/webauthn/assert/verify", json={"refId": m["id"], "credential": assertion})
    signed = j.ok("POST", "/mandates/" + m["id"] + "/sign", json={"assertion": proof["assertionHash"]})
    assert signed["status"] == "active"
    replay = j.request("POST", "/webauthn/assert/verify", json={"refId": m["id"], "credential": assertion})
    assert replay.status_code == 403
    with j.app.state.store.transaction() as s:
        records = [e for e in s["audit"] if e["kind"] == "assertion_verified"]
        assert records[-1]["authenticator"] == "webauthn"
