"""Canonical consent, issuer credentials and privacy helpers."""

import hashlib
import json
import re
import unicodedata

import base58
import jwt
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value):
    return hashlib.sha256((value if isinstance(value, str) else canonical(value)).encode()).hexdigest()


def redact(text):
    text = "".join(c for c in unicodedata.normalize("NFKC", text) if unicodedata.category(c) != "Cf")
    text = re.sub(
        r"(?:password|mật khẩu|비밀번호|密码|access[_ -]?token|api[_ -]?key|otp|cvv|pin)\s*(?:is|là|[:=])\s*[^\s,;]+",
        "[redacted secret]",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"(?:passport|hộ chiếu|여권|护照)\s*(?:number|số|번호|号码)?\s*[:=]\s*[^\s,;]+",
        "[redacted ID]",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"-----BEGIN [^-]*PRIVATE KEY-----.*?-----END [^-]*PRIVATE KEY-----",
        "[redacted secret]",
        text,
        flags=re.S,
    )
    text = re.sub(
        r"\b(?:sk-(?:ant-|proj-)?[A-Za-z0-9_-]{12,}|Bearer\s+[A-Za-z0-9._~-]+)",
        "[redacted secret]",
        text,
        flags=re.I,
    )
    text = re.sub(r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b", "[redacted token]", text)
    text = re.sub(r"\b[A-Z]{2}\d{2}[A-Z0-9 ]{10,30}\b", "[redacted account]", text)
    text = re.sub(r"\bMOCK-[A-Z0-9-]+\b", "[redacted account]", text)
    text = re.sub(r"[\w.+-]+@[\w.-]+\.[a-zA-Z]+", "[redacted email]", text)
    text = re.sub(r"\b(?:\d[ -]?){5,}\d\b", "[redacted number]", text)
    text = re.sub(r"\b[A-Z]{1,3}\d{6,12}\b", "[redacted ID]", text)
    text = re.sub(r"https?://\S+", "[redacted link]", text)
    return text


class Issuer:
    def __init__(self, key_path):
        # Local synthetic issuer key; generated per installation, kept off Git.
        if key_path.exists():
            self.key = Ed25519PrivateKey.from_private_bytes(key_path.read_bytes())
        else:
            self.key = Ed25519PrivateKey.generate()
            key_path.write_bytes(self.key.private_bytes_raw())
        raw = self.key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        self.did = "did:key:z" + base58.b58encode(b"\xed\x01" + raw).decode()

    def issue(self, subject, now, expires):
        return jwt.encode(
            {"iss": self.did, "sub": subject["id"], "iat": now, "nbf": now, "exp": expires, "vc": subject},
            self.key,
            algorithm="EdDSA",
            headers={"kid": self.did + "#" + self.did.split(":")[-1]},
        )

    def verify(self, token, now):
        body = jwt.decode(
            token,
            self.key.public_key(),
            algorithms=["EdDSA"],
            issuer=self.did,
            options={
                "verify_exp": False,
                "verify_nbf": False,
                "verify_iat": False,
                "require": ["exp", "nbf", "iat", "iss", "sub"],
            },
        )
        if not body["nbf"] <= now < body["exp"]:
            raise ValueError("Credential expired or not yet valid")
        return body["vc"]
