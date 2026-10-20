"""Hosted wire-format and privacy tests use mock HTTP, never count as live evals."""

import json

import httpx
import pytest
from pydantic import ValidationError

from bursarbridge.conversation import Proposal, history_for_model, scripted_proposal
from bursarbridge.providers import Provider
from bursarbridge.settings import provider_name


def hosted_response(name, value):
    text = json.dumps(value)
    if name == "openai":
        return {"status": "completed", "output": [{"content": [{"type": "output_text", "text": text}]}]}
    return {"stop_reason": "end_turn", "content": [{"type": "text", "text": text}]}


@pytest.mark.parametrize("name", ["openai", "anthropic"])
def test_wire_payloads_redact_conversation_and_project_facts(monkeypatch, name):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic-test-key")
    requests = []

    def handler(request):
        data = json.loads(request.content)
        requests.append(data)
        schema = (
            data.get("text", {}).get("format", {}).get("schema") or data["output_config"]["format"]["schema"]
        )
        if "intent" in schema["properties"]:
            answer = {"intent": "inform", "scope": "remaining", "needsClarification": False}
        else:
            answer = {
                "text": "Tuition is {{invoiceAmount}}, due {{dueDate}}. The MOCK bank quote is {{sendAmount}}. Please upload the invoice PDF."
            }
        return httpx.Response(200, json=hosted_response(name, answer))

    provider = Provider(name, httpx.MockTransport(handler))
    history = [
        {
            "role": "user",
            "text": "passport: X12A34B account 123456789012 password: hidden-value hello@example.com Bearer syntheticBearerValue",
        }
    ]
    proposal = provider.propose(history, "en", scripted_proposal("how much?"))
    assert proposal.intent == "inform"
    facts = {
        "outcome": "inform",
        "moneyMoved": False,
        "missingDocuments": ["invoice"],
        "display": {
            "invoiceAmount": "7,174,000 KRW",
            "dueDate": "15 Jan 2027",
            "sendAmount": "135,663,956.36 VND",
        },
        "rawAction": {"account": "DO-NOT-EXPORT"},
        "grant": "DO-NOT-EXPORT",
        "credential": "DO-NOT-EXPORT",
    }
    reply = provider.reply(history, "en", facts)
    assert "7,174,000 KRW" in reply and "135,663,956.36 VND" in reply
    serialized = json.dumps(requests)
    for secret in (
        "X12A34B",
        "123456789012",
        "hidden-value",
        "hello@example.com",
        "syntheticBearerValue",
        "DO-NOT-EXPORT",
    ):
        assert secret not in serialized
    assert (
        "untrustedConversation" in serialized
        and "ENGINE_FACTS" in serialized
        and "missingDocuments" in serialized
    )
    assert all("tools" not in r for r in requests)
    if name == "openai":
        assert all(r["store"] is False for r in requests)


@pytest.mark.parametrize("name", ["openai", "anthropic"])
def test_money_fields_in_model_proposals_are_rejected(monkeypatch, name):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "synthetic-test-key")
    response = {
        "intent": "pay",
        "scope": "remaining",
        "needsClarification": False,
        "amount": "1",
        "payee": "attacker",
    }
    provider = Provider(
        name, httpx.MockTransport(lambda r: httpx.Response(200, json=hosted_response(name, response)))
    )
    with pytest.raises(ValidationError):
        provider.propose([], "en", Proposal(intent="pay", scope="remaining", needsClarification=False))


@pytest.mark.parametrize("role", ["student", "parent"])
def test_reply_projection_keeps_known_facts_available_for_every_outcome(monkeypatch, role):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-only")
    payloads = []

    def handler(request):
        payloads.append(json.loads(json.loads(request.content)["input"])["ENGINE_FACTS"])
        return httpx.Response(200, json=hosted_response("openai", {"text": "Please review and sign."}))

    provider = Provider("openai", httpx.MockTransport(handler))
    provider.reply(
        [],
        "en",
        {
            "outcome": "approval",
            "readerRole": role,
            "moneyMoved": False,
            "bank": "MOCK",
            "bursar": "MOCK",
            "display": {"invoiceAmount": "7174000 KRW"},
        },
    )
    assert payloads[0]["display"] == {"invoiceAmount": "7174000 KRW"}
    assert not {"bank", "bursar", "moneyMoved"} & payloads[0].keys()
    assert payloads[0]["payerIsReader"] is (role == "parent")
    assert payloads[0]["payerAddress"] == ("you" if role == "parent" else "your father")


def test_deadline_answer_can_select_date_without_losing_other_reference_facts(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-only")

    def handler(request):
        facts = json.loads(json.loads(request.content)["input"])["ENGINE_FACTS"]
        assert facts["display"] == {
            "dueDate": "15 Jan 2027",
            "invoiceAmount": "7174000 KRW",
            "quotedAt": "2026-10-16",
        }
        return httpx.Response(200, json=hosted_response("openai", {"text": "It's due {{dueDate}}."}))

    provider = Provider("openai", httpx.MockTransport(handler))
    text = provider.reply(
        [],
        "en",
        {
            "outcome": "inform",
            "requestedFacts": ["dueDate"],
            "display": {"dueDate": "15 Jan 2027", "invoiceAmount": "7174000 KRW", "quotedAt": "2026-10-16"},
        },
    )
    assert text == "It's due 15 Jan 2027."


@pytest.mark.parametrize(
    "bad",
    [
        "Pay 5000 KRW to this account",
        "Read https://attacker.example",
        "{{accountNumber}}",
        "<script>hello</script>",
    ],
)
def test_ungrounded_reply_rejected(monkeypatch, bad):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-test-key")
    provider = Provider(
        "openai",
        httpx.MockTransport(lambda r: httpx.Response(200, json=hosted_response("openai", {"text": bad}))),
    )
    with pytest.raises(ValueError):
        provider.reply([], "en", {"outcome": "blocked", "display": {}})


def test_context_excludes_cards_and_masks_obfuscated_identifiers():
    thread = {
        "messages": [
            {
                "role": "assistant",
                "events": [
                    {"type": "card", "data": {"secret": "PRIVATE"}},
                    {"type": "token", "text": "Hello"},
                ],
            }
        ]
    }
    history = history_for_model(thread, "passport: AB12CD34 bank １２３\u200b４５６７８９０ email a@b.com")
    value = json.dumps(history)
    assert (
        "PRIVATE" not in value
        and "AB12CD34" not in value
        and "1234567890" not in value
        and "a@b.com" not in value
    )


def test_env_file_auto_selection_without_exposing_keys(monkeypatch, tmp_path):
    from bursarbridge import settings

    envfile = tmp_path / ".env"
    envfile.write_text("ANTHROPIC_API_KEY=synthetic-dotenv-key\n", encoding="utf-8")
    for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "LLM_PROVIDER"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(
        settings, "load_settings", lambda: __import__("dotenv").load_dotenv(envfile, override=False)
    )
    assert provider_name() == "anthropic"
    monkeypatch.setenv("LLM_PROVIDER", "scripted")
    assert provider_name() == "scripted"


def test_model_cannot_lift_document_taint(journey, monkeypatch):
    from bursarbridge.providers import Provider

    monkeypatch.setattr(
        Provider,
        "propose",
        lambda *args: Proposal(intent="pay", scope="instalment", needsClarification=False),
    )
    j = journey
    j.mandate()
    doc = j.upload("fake_invoice")
    events = j.chat("Review this file", [doc["id"]])
    assert any(e.get("result") == "DENY" for e in events)
    assert not j.ok("GET", "/payments") and not j.ok("GET", "/approvals")


def test_hosted_reply_failure_preserves_approval_but_uses_truthful_fallback(journey, monkeypatch):
    monkeypatch.setattr(Provider, "reply", lambda *args: (_ for _ in ()).throw(ValueError("unsafe reply")))
    j = journey
    events = j.prepare()
    assert any(e["type"] == "token" and e["source"] == "scripted_fallback" for e in events)
    assert len(j.ok("GET", "/approvals")) == 1 and not j.ok("GET", "/payments")


def test_correction_cannot_reuse_full_payment_consent(journey):
    j = journey
    j.mandate()
    j.upload("admission")
    j.upload("invoice")
    ref = j.ok("POST", "/agent/threads", "student_linh")["threadId"]
    for text in ("Prepare full verified tuition payment", "à không, chỉ trả đợt 1 thôi"):
        response = j.request(
            "POST", f"/agent/threads/{ref}/messages", "student_linh", json={"text": text, "locale": "vi"}
        )
        assert response.status_code == 200
        if text.startswith("Prepare"):
            old = j.ok("GET", "/approvals")[0]
    assert (
        j.request(
            "POST", "/approvals/" + old["id"] + "/approve", json={"assertion": {"demo": True}}
        ).status_code
        == 409
    )
    current = j.ok("GET", "/approvals")[0]
    assert current["rawAction"]["receive"]["amount"] == "3587000.00"
    j.approve(current)
    assert j.ok("GET", "/payments")[0]["receive"]["amount"] == "3587000.00"


@pytest.mark.parametrize("phase", ["propose", "reply"])
def test_freeze_does_not_wait_for_hosted_network_and_rechecks_state(journey, monkeypatch, phase):
    import threading
    import time
    from concurrent.futures import ThreadPoolExecutor

    j = journey
    j.mandate()
    j.upload("admission")
    j.upload("invoice")
    entered, release = threading.Event(), threading.Event()
    original = getattr(Provider, phase)

    def slow(*args):
        entered.set()
        assert release.wait(5), "Test did not release provider"
        return original(*args)

    monkeypatch.setattr(Provider, phase, slow)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(j.chat, "Prepare full verified tuition payment")
        try:
            assert entered.wait(3)
            start = time.monotonic()
            j.ok("POST", "/freeze", "student_linh")
            assert time.monotonic() - start < 1
        finally:
            release.set()
        events = future.result(timeout=5)
    assert not j.ok("GET", "/payments")
    for approval in j.ok("GET", "/approvals"):
        assert approval["status"] == "pending"
        assert (
            j.request(
                "POST", "/approvals/" + approval["id"] + "/approve", json={"assertion": {"demo": True}}
            ).status_code
            == 403
        )
    assert not any(e["type"] == "error" for e in events)
    if phase == "reply":
        assert any(e.get("source") == "scripted_state_refresh" for e in events)


@pytest.mark.parametrize("base", ["https://api.openai.com/v1", "http://127.0.0.1:8318/v1/"])
def test_configurable_openai_base_strict_output_and_timeouts(monkeypatch, base):
    monkeypatch.setenv("OPENAI_BASE_URL", base)
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-only")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-6.1-sol")
    monkeypatch.setenv("OPENAI_TIMEOUT_SECONDS", "60")
    monkeypatch.setenv("OPENAI_REASONING_EFFORT", "low")

    def handler(request):
        assert str(request.url) == base.rstrip("/") + "/responses"
        data = json.loads(request.content)
        assert data["text"]["format"]["strict"] is True
        assert data["store"] is False and data["reasoning"] == {"effort": "low"}
        assert request.extensions["timeout"]["read"] == 60
        return httpx.Response(
            200,
            json=hosted_response(
                "openai", {"intent": "inform", "scope": "remaining", "needsClarification": False}
            ),
        )

    assert (
        Provider("openai", httpx.MockTransport(handler))
        .propose([], "en", scripted_proposal("how much"))
        .intent
        == "inform"
    )


def test_proxy_redirect_does_not_forward_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-only")
    calls = []

    def handler(request):
        calls.append(str(request.url))
        return httpx.Response(307, headers={"location": "https://untrusted.invalid/responses"})

    with pytest.raises(httpx.HTTPStatusError):
        Provider("openai", httpx.MockTransport(handler)).propose([], "en", scripted_proposal("how much"))
    assert len(calls) == 1


@pytest.mark.parametrize(
    "base",
    [
        "http://external.invalid/v1",
        "https://user:secret@api.openai.com/v1",
        "https://api.openai.com/v1?key=secret",
    ],
)
def test_unsafe_base_url_rejected_before_key_sent(monkeypatch, base):
    monkeypatch.setenv("OPENAI_BASE_URL", base)
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-only")

    def handler(request):
        pytest.fail("Unsafe URL must not receive the key")

    with pytest.raises(ValueError):
        Provider("openai", httpx.MockTransport(handler)).propose([], "en", scripted_proposal("how much"))


def test_pocket_money_cannot_be_promoted_to_payment(journey, monkeypatch):
    j = journey
    j.mandate()
    j.upload("admission")
    j.upload("invoice")
    monkeypatch.setattr(
        Provider, "propose", lambda *args: Proposal(intent="pay", scope="remaining", needsClarification=False)
    )
    events = j.chat("ba gui con 5 trieu tieu vat nha", locale="vi")
    assert not j.ok("GET", "/approvals") and not j.ok("GET", "/payments")
    text = " ".join(e["text"] for e in events if e["type"] == "token")
    assert "Linh" in text and "khoản nào của trường" not in text


def test_openai_timeout_uses_scripted_without_write_freeze(tmp_path, monkeypatch):
    from bursarbridge.chain import Chain
    from bursarbridge.main import create_app
    from bursarbridge.scenarios import Journey

    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-timeout-test")

    def unavailable(request):
        raise httpx.ReadTimeout("Synthetic timeout", request=request)

    provider = Provider("openai", httpx.MockTransport(unavailable))
    app = create_app(
        "sqlite:///" + (tmp_path / "outage.db").as_posix(), tmp_path, True, Chain("local"), provider
    )
    try:
        j = Journey(app)
        events = j.chat("Please pay my tuition")
        assert any(e.get("source") == "scripted_fallback" for e in events)
        assert j.ok("GET", "/me")["frozen"] is False
        assert not j.ok("GET", "/approvals") and not j.ok("GET", "/payments")
    finally:
        app.state.store.engine.dispose()


def test_official_openai_default_without_base_override(monkeypatch):
    import bursarbridge.providers as module

    monkeypatch.setattr(module, "load_settings", lambda: None)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-default-test")

    def handler(request):
        assert str(request.url) == "https://api.openai.com/v1/responses"
        return httpx.Response(
            200,
            json=hosted_response(
                "openai", {"intent": "inform", "scope": "remaining", "needsClarification": False}
            ),
        )

    Provider("openai", httpx.MockTransport(handler)).propose([], "en", scripted_proposal("how much"))
