"""Two public origins, exact ceremony binding and authenticated proxy IPs."""

import base64
import hashlib
import json
import secrets
from urllib.parse import urlsplit

import cbor2
import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from starlette.requests import Request

from bursarbridge.chain import Chain
from bursarbridge.main import create_app
from bursarbridge.providers import Provider
from bursarbridge.public import COOKIE, create_public_app, visitor_ip
from bursarbridge.scenarios import Journey

OLD = "https://bursarbridge.noamofficial.vn"
PAGES = "https://bursarbridge.pages.dev"
PROXY_SECRET = "synthetic-proxy-test-only"


def b64(value):
    return base64.urlsafe_b64encode(value).decode().rstrip("=")


class Passkey:
    def __init__(self):
        self.key = ec.generate_private_key(ec.SECP256R1())
        self.id = secrets.token_bytes(32)

    def payload(self, options, origin, register=False, rp=None, count=1):
        rp = rp or urlsplit(origin).hostname
        client = json.dumps(
            {
                "type": "webauthn.create" if register else "webauthn.get",
                "challenge": options["challenge"],
                "origin": origin,
            }
        ).encode()
        rp_hash = hashlib.sha256(rp.encode()).digest()
        if register:
            pub = self.key.public_key().public_numbers()
            cose = cbor2.dumps({1: 2, 3: -7, -1: 1, -2: pub.x.to_bytes(32), -3: pub.y.to_bytes(32)})
            data = rp_hash + b"\x45" + bytes(4) + bytes(16) + len(self.id).to_bytes(2) + self.id + cose
            response = {
                "clientDataJSON": b64(client),
                "attestationObject": b64(cbor2.dumps({"fmt": "none", "attStmt": {}, "authData": data})),
            }
        else:
            data = rp_hash + b"\x05" + count.to_bytes(4)
            response = {
                "clientDataJSON": b64(client),
                "authenticatorData": b64(data),
                "signature": b64(
                    self.key.sign(data + hashlib.sha256(client).digest(), ec.ECDSA(hashes.SHA256()))
                ),
            }
        return {"id": b64(self.id), "rawId": b64(self.id), "type": "public-key", "response": response}


@pytest.fixture
def dual(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAUTHN_ORIGIN", OLD + "," + PAGES)
    monkeypatch.setenv("WEBAUTHN_RP_ID", urlsplit(OLD).hostname)
    app = create_app("sqlite:///" + (tmp_path / "state.db").as_posix(), tmp_path, True, Chain("local"))
    j = Journey(app)
    yield j
    j.app.state.store.engine.dispose()


def audience(j, origin):
    j.headers["parent_minh"]["Origin"] = origin


def register(j, origin, key):
    audience(j, origin)
    options = j.ok("POST", "/webauthn/register/options")
    assert options["rp"]["id"] == urlsplit(origin).hostname
    j.ok("POST", "/webauthn/register/verify", json={"credential": key.payload(options, origin, True)})


def unsigned_mandate(j):
    return j.ok(
        "POST",
        "/mandates",
        json={
            "purpose": "tuition",
            "payeeRule": {"type": "credentialed", "issuer": j.app.state.issuer.did},
            "cap": {"amount": "7174000.00", "currency": "KRW"},
            "expiresAt": "2027-06-01T00:00:00Z",
        },
    )


def options_for(j, row):
    return j.ok("POST", "/webauthn/assert/options", json={"purpose": "mandate", "refId": row["id"]})


def test_real_passkeys_register_and_sign_independently_on_both_domains(dual):
    j = dual
    keys = {origin: Passkey() for origin in (OLD, PAGES)}
    for origin, key in keys.items():
        register(j, origin, key)
    for origin, key in keys.items():
        audience(j, origin)
        row = unsigned_mandate(j)
        options = options_for(j, row)
        assert options["rpId"] == urlsplit(origin).hostname
        assert options["allowCredentials"] == [{"type": "public-key", "id": b64(key.id)}]
        proof = j.ok(
            "POST",
            "/webauthn/assert/verify",
            json={"refId": row["id"], "credential": key.payload(options, origin)},
        )
        assert (
            j.ok("POST", f"/mandates/{row['id']}/sign", json={"assertion": proof["assertionHash"]})["status"]
            == "active"
        )
        assert (
            j.request(
                "POST",
                "/webauthn/assert/verify",
                json={"refId": row["id"], "credential": key.payload(options, origin)},
            ).status_code
            == 403
        )
    with j.app.state.store.transaction() as s:
        assert len(s["authenticators"]) == 2
        assert {a["rpId"] for a in s["authenticators"].values()} == {urlsplit(o).hostname for o in keys}


def test_registration_challenge_rejects_other_allowed_origin_and_rp(dual):
    j = dual
    key = Passkey()
    audience(j, OLD)
    options = j.ok("POST", "/webauthn/register/options")
    audience(j, PAGES)
    assert (
        j.request(
            "POST", "/webauthn/register/verify", json={"credential": key.payload(options, PAGES, True)}
        ).status_code
        == 403
    )
    audience(j, OLD)
    for payload in (
        key.payload(options, PAGES, True),
        key.payload(options, OLD, True, rp=urlsplit(PAGES).hostname),
    ):
        assert j.request("POST", "/webauthn/register/verify", json={"credential": payload}).status_code == 403
    j.ok("POST", "/webauthn/register/verify", json={"credential": key.payload(options, OLD, True)})


def test_assertion_and_receipt_cannot_cross_origin_even_with_same_consent_hash(dual):
    j = dual
    a, b = Passkey(), Passkey()
    register(j, OLD, a)
    register(j, PAGES, b)
    row = unsigned_mandate(j)
    audience(j, OLD)
    old_options = options_for(j, row)
    audience(j, PAGES)
    new_options = options_for(j, row)
    assert old_options["challenge"] == new_options["challenge"]
    assert (
        j.request(
            "POST",
            "/webauthn/assert/verify",
            json={"refId": row["id"], "credential": a.payload(old_options, OLD)},
        ).status_code
        == 403
    )
    audience(j, OLD)
    for payload in (a.payload(old_options, PAGES), a.payload(old_options, OLD, rp=urlsplit(PAGES).hostname)):
        assert (
            j.request(
                "POST", "/webauthn/assert/verify", json={"refId": row["id"], "credential": payload}
            ).status_code
            == 403
        )
    proof = j.ok(
        "POST",
        "/webauthn/assert/verify",
        json={"refId": row["id"], "credential": a.payload(old_options, OLD)},
    )
    audience(j, PAGES)
    assert (
        j.request(
            "POST", f"/mandates/{row['id']}/sign", json={"assertion": proof["assertionHash"]}
        ).status_code
        == 403
    )
    audience(j, OLD)
    assert (
        j.ok("POST", f"/mandates/{row['id']}/sign", json={"assertion": proof["assertionHash"]})["status"]
        == "active"
    )


def test_legacy_passkey_stays_on_old_rp_after_upgrade(dual, tmp_path):
    j = dual
    key = Passkey()
    register(j, OLD, key)
    with j.app.state.store.transaction() as s:
        uid = s["users"]["parent_minh"]["id"]
        legacy = s["authenticators"].pop(uid + ":" + urlsplit(OLD).hostname)
        legacy.pop("rpId")
        legacy.pop("origin")
        s["authenticators"][uid] = legacy
    j.app.state.store.engine.dispose()
    j.app = create_app("sqlite:///" + (tmp_path / "state.db").as_posix(), tmp_path, True, Chain("local"))
    j.client = TestClient(j.app)
    row = unsigned_mandate(j)
    audience(j, PAGES)
    assert options_for(j, row)["allowCredentials"] == []
    audience(j, OLD)
    options = options_for(j, row)
    assert options["allowCredentials"][0]["id"] == b64(key.id)
    j.ok(
        "POST", "/webauthn/assert/verify", json={"refId": row["id"], "credential": key.payload(options, OLD)}
    )


@pytest.mark.parametrize("origin", ["https://evil.example", "null", "", PAGES + ".evil.example"])
def test_unlisted_origin_cannot_select_rp_using_host_or_forwarded_headers(dual, origin):
    j = dual
    j.headers["parent_minh"].update(
        {"Origin": origin, "Host": urlsplit(PAGES).hostname, "X-Forwarded-Host": urlsplit(PAGES).hostname}
    )
    assert j.request("POST", "/webauthn/register/options").status_code == 403


def test_allowed_origin_not_tunnel_host_selects_rp_and_missing_origin_uses_primary(dual):
    j = dual
    j.headers["parent_minh"]["Host"] = urlsplit(OLD).hostname
    audience(j, PAGES)
    assert j.ok("POST", "/webauthn/register/options")["rp"]["id"] == urlsplit(PAGES).hostname
    j.headers["parent_minh"].pop("Origin")
    j.headers["parent_minh"].update(
        {"Host": urlsplit(PAGES).hostname, "X-Forwarded-Host": urlsplit(PAGES).hostname}
    )
    assert j.ok("POST", "/webauthn/register/options")["rp"]["id"] == urlsplit(OLD).hostname


def ip_request(headers):
    return Request(
        {"type": "http", "method": "GET", "path": "/", "headers": headers, "client": ("203.0.113.200", 443)}
    )


@pytest.mark.parametrize(
    "value", ["", "bogus", "198.51.100.1, 198.51.100.2", "198.51.100.1:80", "198.51.100.0/24", "fe80::1%eth0"]
)
def test_authenticated_but_invalid_proxy_ip_uses_existing_client(value):
    request = ip_request([(b"x-bb-proxy-secret", PROXY_SECRET.encode()), (b"x-bb-client-ip", value.encode())])
    assert visitor_ip(request, PROXY_SECRET) == "203.0.113.200"


@pytest.mark.parametrize(
    "configured,supplied", [("", PROXY_SECRET), (PROXY_SECRET, "wrong"), (PROXY_SECRET, "")]
)
def test_proxy_headers_are_ignored_without_matching_nonempty_secret(configured, supplied):
    request = ip_request([(b"x-bb-proxy-secret", supplied.encode()), (b"x-bb-client-ip", b"198.51.100.1")])
    assert visitor_ip(request, configured) == "203.0.113.200"


def test_proxy_secret_constant_time_compare_and_duplicate_headers(monkeypatch):
    import hmac
    from unittest.mock import Mock

    compare = Mock(wraps=hmac.compare_digest)
    monkeypatch.setattr("bursarbridge.public.hmac.compare_digest", compare)
    headers = [(b"x-bb-proxy-secret", PROXY_SECRET.encode()), (b"x-bb-client-ip", b"2001:0db8::1")]
    assert visitor_ip(ip_request(headers), PROXY_SECRET) == "2001:db8::1"
    compare.assert_called_once_with(PROXY_SECRET.encode(), PROXY_SECRET.encode())
    for duplicate in headers:
        assert visitor_ip(ip_request(headers + [duplicate]), PROXY_SECRET) == "203.0.113.200"


def test_proxy_ip_separates_creation_limits_but_bad_secret_cannot_evade_them(tmp_path, monkeypatch):
    monkeypatch.setenv("PUBLIC_PROXY_SECRET", PROXY_SECRET)
    monkeypatch.setenv("PUBLIC_NEW_PER_IP_MINUTE", "1")
    app = create_public_app(tmp_path, Chain("local"), Provider("scripted"))
    try:

        def login(ip, secret=PROXY_SECRET):
            client = TestClient(app, base_url=OLD, client=("203.0.113.200", 443))
            return client.post(
                "/api/session",
                json={"persona": "student_linh"},
                headers={"X-BB-Proxy-Secret": secret, "X-BB-Client-IP": ip},
            )

        assert login("198.51.100.1").status_code == 200
        assert login("198.51.100.2").status_code == 200
        assert login("198.51.100.1").status_code == 429
        assert login("198.51.100.3", "wrong").status_code == 200
        assert login("198.51.100.4", "wrong").status_code == 429
    finally:
        for child in app.state.manager.apps.values():
            child.state.store.engine.dispose()


def test_both_public_hosts_keep_relative_redirects_host_only_cookies_and_downloads(tmp_path, monkeypatch):
    monkeypatch.setenv("WEBAUTHN_ORIGIN", OLD + "," + PAGES)
    app = create_public_app(tmp_path, Chain("local"), Provider("scripted"))
    clients = [TestClient(app, base_url=origin) for origin in (OLD, PAGES)]
    tokens = []
    try:
        for origin, client in zip((OLD, PAGES), clients):
            result = client.get(
                "/api/public/bootstrap",
                headers={"x-bursar-return": "/vi/demo?live=1"},
                follow_redirects=False,
            )
            assert result.status_code == 303 and result.headers["location"] == "/vi/demo?live=1"
            cookie = result.headers["set-cookie"].lower()
            assert "domain=" not in cookie and "secure" in cookie and "httponly" in cookie
            assert list(client.cookies.jar)[0].domain == urlsplit(origin).hostname
            token = client.post("/api/session", json={"persona": "parent_minh"}).json()["token"]
            tokens.append(token)
            headers = {"Authorization": "Bearer " + token, "Origin": origin}
            options = client.post("/api/webauthn/register/options", headers=headers)
            assert options.json()["rp"]["id"] == urlsplit(origin).hostname
            assert options.headers["access-control-allow-origin"] == origin
            plan = client.get("/api/study-plan", headers=headers).json()
            assert plan["standardAdmissionCertificate"]["downloadUrl"].startswith("/api/")
            for target in (OLD + "/vi/demo", "//evil.example", "/\\evil.example"):
                redirect = client.get(
                    "/api/public/bootstrap", headers={"x-bursar-return": target}, follow_redirects=False
                )
                assert redirect.headers["location"] == "/"
        assert clients[0].cookies[COOKIE] != clients[1].cookies[COOKIE]
        assert clients[1].get("/api/me", headers={"Authorization": "Bearer " + tokens[0]}).status_code == 401
    finally:
        for child in app.state.manager.apps.values():
            child.state.store.engine.dispose()
