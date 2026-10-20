"""WebAuthn verification and short-lived, reference-bound assertion receipts."""

import base64
import json
import secrets
from urllib.parse import urlsplit

from webauthn import (
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.structs import AuthenticatorSelectionCriteria, UserVerificationRequirement

from .engine import dt, later, owned, require
from .security import digest
from .store import audit


def relying_parties(origins):
    """Only configured exact origins can select a WebAuthn RP."""
    parties = {}
    for origin in origins:
        parsed = urlsplit(origin)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path
            or parsed.query
            or parsed.fragment
            or (parsed.scheme == "http" and parsed.hostname != "localhost")
        ):
            raise ValueError("WEBAUTHN_ORIGIN must contain exact HTTPS origins or HTTP localhost origins")
        parties[origin] = parsed.hostname
    if not parties:
        raise ValueError("At least one WEBAUTHN_ORIGIN is required")
    return parties


def request_party(request, parties):
    # CLI/demo clients without Origin use the configured primary origin. Host,
    # Forwarded and clientDataJSON never select or extend the allowlist.
    headers = request.headers.getlist("origin")
    origin = headers[0] if len(headers) == 1 else next(iter(parties)) if not headers else None
    require(origin in parties, "WEBAUTHN_ORIGIN_NOT_ALLOWED", "Passkey origin is not allowed", 403)
    return parties[origin], origin


def credential_record(s, user, rp):
    record = s["authenticators"].get(user["id"] + ":" + rp)
    if record is None:
        legacy = s["authenticators"].get(user["id"])
        if legacy and legacy.get("rpId") == rp:
            record = legacy
    return record


def ceremony_key(user, origin, ref="register"):
    return user["id"] + ":" + ref + ":" + origin


def target_hash(s, user, ref, purpose):
    if purpose == "cosign":
        row = owned(s, "approvals", ref, user)
        require(user["role"] == "cosigner" and row.get("cooling", {}).get("cosignerId") == user["id"])
        return row["consentHash"]
    if purpose == "mandate":
        row = owned(s, "mandates", ref, user)
        require(row["_owner"] == user["id"])
        return row["hash"]
    if purpose == "approval":
        row = owned(s, "approvals", ref, user)
        require(
            user["role"]
            == ("student" if row["action"] in {"refund_claim", "escalation_letter"} else "parent")
        )
        return row["consentHash"]
    require(ref == user["familyId"] and user["role"] == "parent")
    return digest({"action": "unfreeze", "family": ref, "now": s["now"]})


def register_options(s, user, rp, origin):
    options = generate_registration_options(
        rp_id=rp,
        rp_name="BursarBridge MOCK",
        user_id=user["id"].encode(),
        user_name=user["name"],
        authenticator_selection=AuthenticatorSelectionCriteria(
            user_verification=UserVerificationRequirement.REQUIRED
        ),
    )
    s["challenges"][ceremony_key(user, origin)] = {
        "challenge": options.challenge.hex(),
        "expires": later(s, minutes=5),
        "rpId": rp,
        "origin": origin,
    }
    return json.loads(options_to_json(options))


def register_verify(s, user, credential, demo, rp, origin):
    key = ceremony_key(user, origin)
    challenge = s["challenges"].get(key)
    require(
        challenge
        and challenge.get("rpId") == rp
        and challenge.get("origin") == origin
        and dt(challenge["expires"]) > dt(s["now"]),
        "CHALLENGE_REQUIRED",
        "Request registration options first",
    )
    if credential.get("demo") is True:
        require(demo, "DEMO_DISABLED", "Demo authenticator disabled")
        record = {"demo": True}
    else:
        try:
            result = verify_registration_response(
                credential=credential,
                expected_challenge=bytes.fromhex(challenge["challenge"]),
                expected_rp_id=rp,
                expected_origin=origin,
                require_user_verification=True,
            )
        except Exception as exc:
            from .engine import DomainError

            raise DomainError("INVALID_ASSERTION", "WebAuthn registration failed", 403) from exc
        record = {
            "id": result.credential_id.hex(),
            "publicKey": result.credential_public_key.hex(),
            "signCount": result.sign_count,
            "demo": False,
        }
    s["authenticators"][user["id"] + ":" + rp] = {**record, "rpId": rp, "origin": origin}
    del s["challenges"][key]
    audit(
        s,
        user["id"],
        "authenticator_registered",
        "Authenticator registered",
        authenticator="demo" if credential.get("demo") else "webauthn",
    )
    return {"ok": True}


def assertion_options(s, user, ref, purpose, rp, origin):
    consent = target_hash(s, user, ref, purpose)
    challenge = bytes.fromhex(consent)
    s["challenges"][ceremony_key(user, origin, ref)] = {
        "hash": consent,
        "purpose": purpose,
        "expires": later(s, minutes=5),
        "rpId": rp,
        "origin": origin,
    }
    auth = credential_record(s, user, rp) or {}
    allowed = (
        []
        if auth.get("demo", True)
        else [
            {
                "type": "public-key",
                "id": base64.urlsafe_b64encode(bytes.fromhex(auth["id"])).decode().rstrip("="),
            }
        ]
    )
    return {
        "rpId": rp,
        "challenge": base64.urlsafe_b64encode(challenge).decode().rstrip("="),
        "timeout": 300000,
        "userVerification": "required",
        "allowCredentials": allowed,
    }


def assertion_verify(s, user, ref, credential, demo, rp, origin):
    key = ceremony_key(user, origin, ref)
    challenge = s["challenges"].get(key)
    require(
        challenge
        and challenge.get("rpId") == rp
        and challenge.get("origin") == origin
        and dt(challenge["expires"]) > dt(s["now"]),
        "CHALLENGE_REQUIRED",
        "Request assertion options first",
    )
    require(
        target_hash(s, user, ref, challenge["purpose"]) == challenge["hash"],
        "CONSENT_MISMATCH",
        "Consent changed",
    )
    authenticator = "webauthn"
    if credential.get("demo") is True:
        require(demo, "DEMO_DISABLED", "Demo authenticator disabled")
        authenticator = "demo"
    else:
        auth = credential_record(s, user, rp)
        require(auth and not auth.get("demo"), "AUTHENTICATOR_REQUIRED", "Register a passkey first")
        try:
            result = verify_authentication_response(
                credential=credential,
                expected_challenge=bytes.fromhex(challenge["hash"]),
                expected_rp_id=rp,
                expected_origin=origin,
                credential_public_key=bytes.fromhex(auth["publicKey"]),
                credential_current_sign_count=auth["signCount"],
                require_user_verification=True,
            )
            require(
                result.credential_id.hex() == auth["id"], "INVALID_ASSERTION", "Credential identity mismatch"
            )
            auth["signCount"] = result.new_sign_count
        except Exception as exc:
            from .engine import DomainError

            raise DomainError("INVALID_ASSERTION", "WebAuthn assertion failed", 403) from exc
    receipt = secrets.token_urlsafe(32)
    s["assertions"][digest(receipt)] = {
        "user": user["id"],
        "ref": ref,
        "hash": challenge["hash"],
        "expires": later(s, minutes=5),
        "used": False,
        "authenticator": authenticator,
        "rpId": rp,
        "origin": origin,
    }
    del s["challenges"][key]
    audit(
        s,
        user["id"],
        "assertion_verified",
        "Reference-bound assertion verified",
        consentHash=challenge["hash"],
        assertionHash=digest(receipt),
        authenticator=authenticator,
    )
    return {"ok": True, "assertionHash": receipt}


def consume(s, user, ref, assertion, expected, demo, rp, origin):
    # Direct demo fallback is explicitly authorized by the API, but never accepts a
    # caller-provided consent hash as proof in non-demo mode.
    if isinstance(assertion, dict) and assertion.get("demo") is True:
        require(demo, "DEMO_DISABLED", "Demo authenticator disabled")
        audit(
            s,
            user["id"],
            "demo_consent",
            "DEMO authenticator used",
            consentHash=expected,
            authenticator="demo",
        )
        return
    receipt = assertion if isinstance(assertion, str) else assertion.get("assertionHash", "")
    proof = s["assertions"].get(digest(receipt))
    require(
        proof
        and not proof["used"]
        and proof["ref"] == ref
        and proof["user"] == user["id"]
        and proof["hash"] == expected
        and proof.get("rpId") == rp
        and proof.get("origin") == origin
        and dt(proof["expires"]) > dt(s["now"]),
        "INVALID_ASSERTION",
        "Missing, expired, reused or incorrectly bound assertion",
    )
    proof["used"] = True
