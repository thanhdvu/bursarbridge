"""Composition of language features and cancellable bank holds, not phrase memorization."""

import pytest

from bursarbridge.conversation import normalize, scripted_proposal
from bursarbridge.engine import advance


@pytest.mark.parametrize("verb", ["đóng", "nộp", "trả", "gửi", "chuyển"])
@pytest.mark.parametrize("noun", ["học phí", "tiền học", "tiền trường"])
def test_vietnamese_composition_with_and_without_accents(verb, noun):
    text = f"ba ơi {verb} giúp con {noun} kỳ này được không?"
    for variant in (text, normalize(text)):
        proposal = scripted_proposal(variant)
        assert proposal.intent == "pay" and not proposal.needsClarification


@pytest.mark.parametrize("verb", ["납부", "보내줘", "송금", "이체", "내주세요"])
def test_korean_composition(verb):
    assert scripted_proposal(f"아빠 등록금 이번 학기 {verb} 부탁해요").intent == "pay"


@pytest.mark.parametrize("verb", ["缴", "交", "付", "转账", "汇"])
def test_chinese_composition(verb):
    assert scripted_proposal(f"帮我把这学期的学费{verb}给学校吧").intent == "pay"


@pytest.mark.parametrize(
    "text,intent",
    [
        ("dung nop hoc phi", "clarify_request"),
        ("不要交学费", "clarify_request"),
        ("등록금 내지 마세요", "clarify_request"),
        ("nop hoc phi vao crypto", "crypto"),
        ("nop hoc phi tai khoan moi", "document_instruction"),
        ("hoc phi bao nhieu", "inform"),
        ("send money", "clarify_request"),
    ],
)
def test_recognition_preserves_guards_and_uncertainty(text, intent):
    assert scripted_proposal(text).intent == intent


def test_hold_cancel_boundary_and_settlement(journey):
    j = journey
    p = j.pay(settle=False)
    assert p["status"] == "sent" and p["cancelUntil"]
    assert [e["code"] for e in p["timeline"]] == ["payment_executed"]
    with j.app.state.store.transaction() as state:
        state["now"] = "2027-01-12T03:29:59Z"
        advance(state)
    assert j.ok("GET", "/payments")[0]["status"] == "sent"
    with j.app.state.store.transaction() as state:
        state["now"] = "2027-01-12T03:30:00Z"
        advance(state)
    settled = j.ok("GET", "/payments")[0]
    assert settled["status"] == "matched" and not settled["cancelUntil"]
    assert settled["timeline"][-1]["at"] == "2027-01-12T03:30:00Z"
    assert j.request("POST", f"/payments/{p['id']}/cancel").status_code == 409
    before = len(settled["timeline"])
    j.ok("POST", "/clock/advance", "judge", json={"hours": 1})
    assert len(j.ok("GET", "/payments")[0]["timeline"]) == before


def test_cancelled_hold_never_reaches_bursar(journey):
    j = journey
    before = j.ok("GET", "/me")["accounts"][0]["balance"]
    p = j.pay(settle=False)
    j.ok("POST", f"/payments/{p['id']}/cancel")
    j.ok("POST", "/clock/advance", "judge", json={"hours": 1})
    p = j.ok("GET", "/payments")[0]
    assert p["status"] == "cancelled" and not p["cancelUntil"]
    assert not any(e["code"] == "payment_matched" for e in p["timeline"])
    assert j.ok("GET", "/me")["accounts"][0]["balance"] == before


def test_default_passkey_origins_without_dotenv_or_env(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from bursarbridge.chain import Chain
    from bursarbridge.main import create_app

    monkeypatch.delenv("WEBAUTHN_ORIGIN", raising=False)
    monkeypatch.delenv("WEBAUTHN_RP_ID", raising=False)
    app = create_app("sqlite:///" + (tmp_path / "origins.db").as_posix(), tmp_path, True, Chain("local"))
    client = TestClient(app)
    for origin in ("http://localhost:3000", "http://localhost:3700"):
        result = client.options(
            "/api/webauthn/register/options",
            headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
        )
        assert result.headers["access-control-allow-origin"] == origin
    token = client.post("/api/session", json={"persona": "parent_minh"}).json()["token"]
    options = client.post(
        "/api/webauthn/register/options", headers={"Authorization": "Bearer " + token}
    ).json()
    assert options["rp"]["id"] == "localhost"
    app.state.store.engine.dispose()
