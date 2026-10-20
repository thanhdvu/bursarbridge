"""Two concurrent private judge journeys on real local FISCO/Watchman.

Stop the interactive API first: a different process cannot share the signer nonce lock.
From services/api: uv run --frozen python scripts/public_family_smoke.py.
No hosted calls, resets of the chain or changes to interactive state. DEMO assertions
are deliberately labelled; this does not claim hardware passkey or public VM testing.
"""

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from bursarbridge.chain import Chain
from bursarbridge.fixtures import pdf
from bursarbridge.providers import Provider
from bursarbridge.public import create_public_app


def journey(app):
    client = TestClient(app, base_url="https://demo.example")
    headers = {}
    for persona in ("student_linh", "parent_minh", "judge"):
        response = client.post("/api/session", json={"persona": persona})
        assert response.status_code == 200
        headers[persona] = {"Authorization": "Bearer " + response.json()["token"]}

    def call(method, path, persona="student_linh", **kwargs):
        response = client.request(method, "/api" + path, headers=headers[persona], **kwargs)
        assert response.status_code == 200, f"{method} {path} HTTP {response.status_code}"
        return response

    thread = call("POST", "/agent/threads").json()["threadId"]

    def chat(text, docs=()):
        response = call(
            "POST", f"/agent/threads/{thread}/messages", json={"text": text, "documentIds": list(docs)}
        )
        events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
        assert not any(e["type"] == "error" for e in events)
        return events

    def upload(kind):
        return call(
            "POST",
            "/documents",
            files={"file": (kind + ".pdf", pdf(kind), "application/pdf")},
            data={"kind": kind if kind in {"admission", "invoice", "refusal"} else "email"},
        ).json()["id"]

    assert any(e.get("kind") == "needs" for e in chat("pay tuition"))
    upload("admission")
    upload("invoice")
    issuer = call("GET", "/catalog", "parent_minh").json()["issuer"]
    mandate = call(
        "POST",
        "/mandates",
        "parent_minh",
        json={
            "purpose": "tuition",
            "payeeRule": {"type": "credentialed", "issuer": issuer},
            "cap": {"amount": "8954000.00", "currency": "KRW"},
            "expiresAt": "2027-06-01T00:00:00Z",
        },
    ).json()
    call("POST", f"/mandates/{mandate['id']}/sign", "parent_minh", json={"assertion": {"demo": True}})
    approval = call("GET", "/approvals").json()[0]
    assert approval["rawAction"]["receive"]["amount"] == "8954000.00"
    call("POST", f"/approvals/{approval['id']}/approve", "parent_minh", json={"assertion": {"demo": True}})
    call("POST", "/clock/advance", "judge", json={"hours": 1})
    payment = call("GET", "/payments").json()[0]
    assert payment["status"] == "matched"
    assert any(e.get("kind") == "blocked" for e in chat("forwarded", [upload("fake_invoice")]))
    chat("visa refused", [upload("refusal")])
    claim = call("GET", "/approvals").json()[0]
    call("POST", f"/approvals/{claim['id']}/approve", json={"assertion": {"demo": True}})
    call("POST", "/clock/advance", "judge", json={"days": 10})
    refund = call("GET", "/refunds").json()[0]
    assert refund["status"] == "reconciled" and refund["destination"]["id"] == "acct_parent_minh"
    call("POST", "/chain/anchor", "judge")
    verified = call("POST", "/audit/verify", "judge").json()
    assert verified["ok"]
    anchors = call("GET", "/chain/anchors", "judge").json()
    assert anchors and all(a["mode"] == "fisco" and a["txHash"].startswith("0x") for a in anchors)
    return (
        client,
        headers,
        {
            "paymentStatus": payment["status"],
            "refundStatus": refund["status"],
            "originalPayer": True,
            "verify": verified,
            "anchors": anchors,
        },
    )


if __name__ == "__main__":
    started = time.monotonic()
    chain = Chain()
    assert chain.mode == "fisco" and chain.available(), "Real FISCO required"
    assert os.getenv("SCREENING_MODE", "watchman") == "watchman", "Native Watchman required"
    with TemporaryDirectory(prefix="bb-public-real-") as folder:
        app = create_public_app(folder, chain, Provider("scripted"))
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: journey(app), range(2)))
            a, b = results
            assert a[0].post("/api/demo/reset", headers=a[1]["judge"]).status_code == 200
            assert b[0].get("/api/me", headers=b[1]["student_linh"]).status_code == 200
            assert a[0].get("/api/me", headers=a[1]["student_linh"]).status_code == 401
            indices = [anchor["index"] for result in results for anchor in result[2]["anchors"]]
            assert len(indices) == len(set(indices)), "Anchor index race"
            report = {
                "transport": "two concurrent HTTP TestClient public sandboxes",
                "provider": "scripted",
                "chain": "real FISCO BCOS",
                "screening": "native Watchman",
                "resetIsolated": True,
                "anchorIndicesUnique": True,
                "ms": round(1000 * (time.monotonic() - started), 1),
                "journeys": [result[2] for result in results],
                "limits": "Local services, labelled DEMO assertions and MOCK bank/bursar. No cloud, public certificate, real money or hardware passkey claim.",
            }
            Path("runtime/public_family_smoke.json").write_text(
                json.dumps(report, indent=2), encoding="utf-8"
            )
            print(
                json.dumps(
                    {
                        "journeys": len(results),
                        "matchedAndRefunded": True,
                        "resetIsolated": True,
                        "uniqueAnchorIndices": len(indices),
                    }
                )
            )
        finally:
            for child in app.state.manager.apps.values():
                child.state.store.engine.dispose()
