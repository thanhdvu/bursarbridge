"""Real ASGI requests across independent cookie jars and durable public budgets."""

import json
import os

import httpx
import pytest
from fastapi.testclient import TestClient
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from bursarbridge.availability import Budget, HostedGate
from bursarbridge.chain import Chain
from bursarbridge.providers import Provider
from bursarbridge.public import COOKIE, create_public_app


def login(client, persona="student_linh"):
    response = client.post("/api/session", json={"persona": persona})
    assert response.status_code == 200, response.text
    return {"Authorization": "Bearer " + response.json()["token"]}


def chat(client, headers, text="pay tuition"):
    ref = client.post("/api/agent/threads", headers=headers).json()["threadId"]
    response = client.post(f"/api/agent/threads/{ref}/messages", headers=headers, json={"text": text})
    if response.status_code != 200:
        return response, []
    return response, [
        json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")
    ]


@pytest.fixture
def public(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    app = create_public_app(tmp_path, Chain("local"), Provider("scripted"))
    yield app
    for child in app.state.manager.apps.values():
        child.state.store.engine.dispose()


def test_private_sandboxes_reset_and_auth_do_not_cross_visitors(public):
    a, b = [TestClient(public, base_url="https://demo.example") for _ in range(2)]
    ha, hb = login(a), login(b)
    assert a.cookies[COOKIE] != b.cookies[COOKIE]
    assert a.get("/api/me", headers=hb).status_code == 401
    assert b.get("/api/me", headers=ha).status_code == 401
    _, events = chat(a, ha)
    assert any(e.get("kind") == "needs" for e in events)
    judge = login(a, "judge")
    assert a.post("/api/demo/reset", headers=judge).status_code == 200
    assert a.get("/api/me", headers=ha).status_code == 401
    assert b.get("/api/me", headers=hb).status_code == 200
    assert len(public.state.manager.apps) == 2
    issuers = [app.state.issuer.did for app in public.state.manager.apps.values()]
    assert len(set(issuers)) == 2  # No credential revocation/reset collisions on the shared registry.


def test_legacy_asgi_entry_point_honors_public_flag(tmp_path, monkeypatch):
    from bursarbridge.main import create_app

    monkeypatch.setenv("PUBLIC_DEMO", "1")
    app = create_app(data_dir=tmp_path, chain=Chain("local"), provider=Provider("scripted"))
    assert hasattr(app.state, "manager")
    client = TestClient(app, base_url="https://demo.example")
    headers = login(client)
    assert client.get("/api/me", headers=headers).status_code == 200
    for child in app.state.manager.apps.values():
        child.state.store.engine.dispose()


def test_cookie_lifetime_matches_and_renews_sandbox_idle_expiry(public):
    from http.cookies import SimpleCookie

    client = TestClient(public, base_url="https://demo.example")
    response = client.get("/api/public/bootstrap", follow_redirects=False)
    cookie = SimpleCookie(response.headers["set-cookie"])[COOKIE]
    assert int(cookie["max-age"]) == public.state.manager.ttl
    ref = public.state.manager.identify(cookie.value)
    assert not (public.state.manager.root / ref).exists()
    login(client)
    path = public.state.manager.root / ref
    # Restore a near-expiry active sandbox, then renew the same identity.
    import time

    previous = time.time() - public.state.manager.ttl + 120
    os.utime(path, (previous, previous))
    response = client.get("/api/public/bootstrap", follow_redirects=False)
    renewed = SimpleCookie(response.headers["set-cookie"])[COOKIE]
    assert renewed.value == cookie.value
    assert path.stat().st_mtime > previous
    headers = login(client)
    response = client.get("/api/me", headers=headers)
    renewed = SimpleCookie(response.headers["set-cookie"])[COOKIE]
    assert renewed.value == cookie.value
    assert int(renewed["max-age"]) == public.state.manager.ttl


def test_cookie_protection_and_bootstrap_precedes_parallel_persona_sessions(public):
    client = TestClient(public, base_url="https://demo.example")
    response = client.get(
        "/api/public/bootstrap", headers={"x-bursar-return": "/vi/demo?live=1"}, follow_redirects=False
    )
    assert response.status_code == 303 and response.headers["location"] == "/vi/demo?live=1"
    assert all(
        part in response.headers["set-cookie"].lower()
        for part in ("secure", "httponly", "samesite=lax", "path=/")
    )
    cookie = client.cookies[COOKIE]
    for persona in ("student_linh", "parent_minh", "mother_lan", "judge"):
        login(client, persona)
        assert client.cookies[COOKIE] == cookie
    assert len(public.state.manager.apps) == 1
    response = client.get(
        "/api/public/bootstrap", headers={"x-bursar-return": "//evil.example"}, follow_redirects=False
    )
    assert response.headers["location"] == "/"
    attacker = TestClient(public, base_url="https://demo.example")
    attacker.cookies.set(COOKIE, cookie[:-1] + ("a" if cookie[-1] != "a" else "b"))
    assert attacker.get("/api/clock", headers=login(client)).status_code == 401


def test_message_budget_is_per_visitor_not_one_shared_nat_bucket(public):
    a, b = [TestClient(public, base_url="https://demo.example") for _ in range(2)]
    ha, hb = login(a), login(b)
    for _ in range(3):
        assert chat(a, ha, "how much tuition?")[0].status_code == 200
    assert chat(a, ha)[0].status_code == 429
    assert chat(b, hb)[0].status_code == 200


def test_durable_global_llm_budget_does_not_reset_with_new_cookie(tmp_path):
    budget = Budget(tmp_path / "budget.db")
    gate = HostedGate(budget, daily=2, hourly=2)
    for _ in range(2):
        gate.enter()
        gate.leave()
    restarted = HostedGate(Budget(tmp_path / "budget.db"), daily=2, hourly=2)
    from bursarbridge.availability import AdmissionError

    with pytest.raises(AdmissionError, match="hosted_budget_exhausted"):
        restarted.enter()


def test_budget_connections_are_closed_without_waiting_for_garbage_collection(tmp_path, monkeypatch):
    import sqlite3

    from bursarbridge import availability

    original = sqlite3.connect
    connections = []

    def connect(*args, **kwargs):
        connection = original(*args, **kwargs)
        connections.append(connection)
        return connection

    monkeypatch.setattr(availability.sqlite3, "connect", connect)
    budget = Budget(tmp_path / "budget.db")
    for _ in range(3):
        assert budget.take([("test", 10, 60)])
    for connection in connections:
        with pytest.raises(sqlite3.ProgrammingError, match="closed"):
            connection.execute("SELECT 1")


def test_outage_is_visible_and_scripted_turn_still_prepares_needs(public, monkeypatch, caplog):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-secret-not-in-logs")

    def fail(request):
        return httpx.Response(429, json={"error": "synthetic-secret-not-in-logs"})

    provider = Provider("openai", httpx.MockTransport(fail))
    provider.gate = public.state.manager.provider.gate
    public.state.manager.provider = provider
    client = TestClient(public, base_url="https://demo.example")
    headers = login(client)
    _, events = chat(client, headers)
    assert any(e.get("kind") == "needs" for e in events)
    token = next(e for e in events if e["type"] == "token")
    assert token["source"] == "scripted_fallback" and token["fallback"]["code"] == "rate_limited"
    assert client.get("/api/me", headers=headers).json()["frozen"] is False
    health = client.get("/api/health").json()
    assert health["screeningMode"] == "synthetic"
    assert health["llm"]["effectiveProvider"] == "scripted"
    assert health["llm"]["lastError"]["httpStatus"] == 429
    assert "llm_fallback" in caplog.text
    assert "synthetic-secret-not-in-logs" not in json.dumps(health) + caplog.text + json.dumps(token)
    # The fallback supports the actual journey, not just a friendly sentence.
    from bursarbridge.fixtures import pdf

    for kind in ("admission", "invoice"):
        response = client.post(
            "/api/documents",
            headers=headers,
            files={"file": (kind + ".pdf", pdf(kind), "application/pdf")},
            data={"kind": kind},
        )
        assert response.status_code == 200
    parent = login(client, "parent_minh")
    issuer = client.get("/api/catalog", headers=parent).json()["issuer"]
    mandate = client.post(
        "/api/mandates",
        headers=parent,
        json={
            "purpose": "tuition",
            "payeeRule": {"type": "credentialed", "issuer": issuer},
            "cap": {"amount": "7174000.00", "currency": "KRW"},
            "expiresAt": "2027-06-01T00:00:00Z",
        },
    ).json()
    assert (
        client.post(
            f"/api/mandates/{mandate['id']}/sign", headers=parent, json={"assertion": {"demo": True}}
        ).status_code
        == 200
    )
    approval = client.get("/api/approvals", headers=parent).json()[0]
    assert approval["rawAction"]["receive"]["amount"] == "7174000.00"
    assert (
        client.post(
            f"/api/approvals/{approval['id']}/approve", headers=parent, json={"assertion": {"demo": True}}
        ).status_code
        == 200
    )
    assert client.get("/api/payments", headers=parent).json()[0]["status"] == "sent"
    # The deployment-wide cooldown must not freeze a second browser either.
    other = TestClient(public, base_url="https://demo.example")
    other_headers = login(other)
    _, events = chat(other, other_headers)
    assert next(e for e in events if e["type"] == "token")["fallback"]["code"] == "provider_cooldown"
    assert other.get("/api/me", headers=other_headers).json()["frozen"] is False


def test_money_freeze_survives_public_conversation_fallback(public):
    client = TestClient(public, base_url="https://demo.example")
    headers = login(client)
    client.post("/api/freeze", headers=headers)
    chat(client, headers)
    assert client.get("/api/me", headers=headers).json()["frozen"] is True
    assert client.get("/api/payments", headers=headers).json() == []


def test_chain_outage_defers_money_without_freezing_conversation(public):
    public.state.manager.chain.available = lambda: False
    client = TestClient(public, base_url="https://demo.example")
    headers = login(client)
    _, events = chat(client, headers)
    assert any(e.get("kind") == "needs" and e["data"]["code"] == "CHAIN_UNAVAILABLE" for e in events)
    assert client.get("/api/me", headers=headers).json()["frozen"] is False
    assert client.get("/api/payments", headers=headers).json() == []


def test_zero_hosted_budget_is_scripted_before_any_network_call(public, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-only")
    calls = []

    def network(request):
        calls.append(request)
        raise AssertionError("Zero budget must not make a provider request")

    provider = Provider("openai", httpx.MockTransport(network))
    provider.gate = HostedGate(public.state.manager.budget, daily=0)
    public.state.manager.provider = provider
    client = TestClient(public, base_url="https://demo.example")
    headers = login(client)
    _, events = chat(client, headers)
    assert next(e for e in events if e["type"] == "token")["fallback"]["code"] == "hosted_budget_exhausted"
    assert client.get("/api/me", headers=headers).json()["frozen"] is False
    assert not calls


def test_public_clock_jump_is_bounded_before_any_timers_run(public):
    client = TestClient(public, base_url="https://demo.example")
    headers = login(client, "judge")
    before = client.get("/api/clock", headers=headers).json()
    response = client.post("/api/clock/advance", headers=headers, json={"days": 365})
    assert response.status_code == 422 and response.json()["error"]["code"] == "PUBLIC_CLOCK_LIMIT"
    assert client.get("/api/clock", headers=headers).json() == before
    assert client.post("/api/clock/advance", headers=headers, json={"days": 31}).status_code == 200


def test_sandbox_limit_expiry_and_restart_persistence(tmp_path, monkeypatch):
    monkeypatch.setenv("PUBLIC_MAX_SANDBOXES", "2")
    app = create_public_app(tmp_path, Chain("local"), Provider("scripted"))
    a, b, c = [TestClient(app, base_url="https://demo.example") for _ in range(3)]
    _ha, hb = login(a), login(b)
    assert c.post("/api/session", json={"persona": "judge"}).status_code == 503
    ref = app.state.manager.identify(a.cookies[COOKIE])
    for child in app.state.manager.apps.values():
        child.state.store.engine.dispose()
    restarted = create_public_app(tmp_path, Chain("local"), Provider("scripted"))
    d = TestClient(restarted, base_url="https://demo.example")
    d.cookies.update(b.cookies)
    assert d.get("/api/me", headers=hb).status_code == 200
    os.utime(tmp_path / ref, (1, 1))
    restarted.state.manager.sweep()
    assert not (tmp_path / ref).exists()
    assert d.get("/api/me", headers=hb).status_code == 200
    assert c.post("/api/session", json={"persona": "judge"}).status_code == 200


def test_only_local_proxy_can_supply_client_ip():
    async def endpoint(scope, receive, send):
        from starlette.responses import JSONResponse

        await JSONResponse({"client": scope["client"][0]})(scope, receive, send)

    app = ProxyHeadersMiddleware(endpoint, trusted_hosts="127.0.0.1,::1")
    for peer, expected in [("127.0.0.1", "203.0.113.10"), ("198.51.100.10", "198.51.100.10")]:
        client = TestClient(app, client=(peer, 1234))
        assert client.get("/", headers={"X-Forwarded-For": "203.0.113.10"}).json()["client"] == expected


def test_disconnected_scenario_generator_releases_its_sqlite_resources():
    from bursarbridge.scenarios import run_scenarios

    stream = run_scenarios(["T01"], chain=Chain("local"))
    assert next(stream)["status"] == "running"
    assert next(stream)["status"] == "pass"
    stream.close()


def test_previews_bootstrap_without_consuming_state_or_creation_budget(public):
    manager = public.state.manager
    for _ in range(40):
        client = TestClient(public, base_url="https://demo.example")
        assert client.get("/api/public/bootstrap", follow_redirects=False).status_code == 303
        assert client.get("/api/clock").status_code == 401
    assert not manager.apps
    assert not [p for p in manager.root.iterdir() if p.is_dir()]
    a, b = [TestClient(public, base_url="https://demo.example") for _ in range(2)]
    login(a)
    login(b)
    assert a.cookies[COOKIE] != b.cookies[COOKIE]
    assert len(manager.apps) == 2


def test_capacity_retires_longest_idle_not_recent_or_inflight(public):
    import time
    manager = public.state.manager
    manager.max_sandboxes = 3
    a, b, c, d = [TestClient(public, base_url="https://demo.example") for _ in range(4)]
    ha, hb, hc = login(a), login(b), login(c)
    ra, rb = manager.identify(a.cookies[COOKIE]), manager.identify(b.cookies[COOKIE])
    now = time.time()
    os.utime(manager.root / ra, (now - 800, now - 800))
    os.utime(manager.root / rb, (now - 600, now - 600))
    manager.active[ra] = 1
    login(d)
    assert (manager.root / ra).is_dir() and not (manager.root / rb).exists()
    manager.active.pop(ra)
    assert a.get("/api/me", headers=ha).status_code == 200
    assert b.get("/api/me", headers=hb).status_code == 401
    assert c.get("/api/me", headers=hc).status_code == 200
    newcomer = TestClient(public, base_url="https://demo.example")
    response = newcomer.post("/api/session", json={"persona": "judge"}, headers={"accept": "text/html"})
    assert response.status_code == 503 and "text/html" in response.headers["content-type"]
    assert "Try again" in response.text and response.headers["retry-after"] == "60"


def test_creation_rates_configurable_bursts_preserved(public, monkeypatch):
    manager = public.state.manager
    monkeypatch.setenv("PUBLIC_NEW_PER_IP_MINUTE", "2")
    monkeypatch.setenv("PUBLIC_NEW_PER_IP_HOUR", "3")
    monkeypatch.setenv("PUBLIC_NEW_GLOBAL_HOUR", "4")
    assert manager.allocate("one")[1] is None
    assert manager.allocate("one")[1] is None
    assert manager.allocate("one")[1] == "SANDBOX_RATE_LIMITED"
    assert manager.allocate("two")[1] is None
    assert manager.allocate("two")[1] is None
    assert manager.allocate("three")[1] == "SANDBOX_RATE_LIMITED"

def test_default_creation_capacity_exceeds_old_32_per_hour(public):
    manager = public.state.manager
    for visitor in range(50):
        ref, error = manager.allocate(str(visitor))
        assert ref and error is None
    assert len([p for p in manager.root.iterdir() if p.is_dir()]) == 50
