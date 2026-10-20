"""The same HTTP conversation evals for scripted CI and opt-in hosted runs."""

import json
import time
from collections import Counter
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from .chain import Chain
from .main import create_app
from .providers import Provider
from .scenarios import Journey

CASES = Path(__file__).resolve().parents[1] / "evals/conversations.json"


def fact_present(text, key, display):
    if key == "instalmentSchedule":
        # The signed entries may be narrated separately with their due dates;
        # requiring a literal '+' would reject the same correct schedule.
        entries = Counter(display[key].split(" + "))
        return all(text.count(amount) >= count for amount, count in entries.items())
    return display[key] in text


def evaluate_conversations(provider_name="scripted", output=None, transport=None):
    results = []
    with TemporaryDirectory(prefix="bb-dialogue-") as folder:
        for case in json.loads(CASES.read_text(encoding="utf-8")):
            path = Path(folder) / case["id"]
            path.mkdir()
            provider = Provider(provider_name, transport=transport)
            app = create_app(
                "sqlite:///" + (path / "state.db").as_posix(), path, True, Chain("local"), provider
            )
            app.state.issuer.screening.mode = "synthetic"
            j = Journey(app)
            if case.get("paid"):
                old_name = provider.name
                provider.name = "scripted"
                j.pay()
                if case.get("refundReady"):
                    denial = j.upload("refusal")
                    j.chat("Visa refused", [denial["id"]])
                    j.approve(j.ok("GET", "/approvals")[0], "student_linh")
                provider.name = old_name
            if case.get("rent"):
                j.upload("rental_agreement", "parent_wang")
                response = j.client.post("/api/session", json={"persona": "student_hao"})
                j.headers["student_hao"] = {"Authorization": "Bearer " + response.json()["token"]}
                mandate = j.ok(
                    "POST",
                    "/mandates",
                    "parent_wang",
                    json={
                        "purpose": "rent",
                        "payeeRule": {"type": "name_checked", "payeeId": "payee_landlord"},
                        "cap": {"amount": "1000000.00", "currency": "KRW"},
                        "period": "monthly",
                        "expiresAt": "2027-06-01T00:00:00Z",
                    },
                )
                j.ok(
                    "POST",
                    f"/mandates/{mandate['id']}/sign",
                    "parent_wang",
                    json={"assertion": {"demo": True}},
                )
            if case.get("ready") or case.get("mandate"):
                j.mandate()
            if case.get("ready"):
                j.upload("admission")
                j.upload("invoice")
            if case.get("pendingTuition"):
                old_name = provider.name
                provider.name = "scripted"
                j.upload("admission")
                j.upload("invoice")
                j.chat("pay tuition")
                provider.name = old_name
            refs = [j.upload("fake_invoice")["id"]] if case.get("attackDocument") else []
            persona = case.get("persona", "student_linh")
            if persona not in j.headers:
                response = j.client.post("/api/session", json={"persona": persona})
                j.headers[persona] = {"Authorization": "Bearer " + response.json()["token"]}
            thread = j.ok("POST", "/agent/threads", persona)["threadId"]
            transcript, errors, originals = [], [], []
            incidents, incident_trace = {}, []
            started = time.perf_counter()
            with app.state.store.transaction() as s:
                before = {k: deepcopy(s[k]) for k in ("approvals", "refunds", "grants", "mandates", "users")}
            try:
                for index, turn in enumerate(case["turns"]):
                    if index and case.get("settleAfterFirst"):
                        j.ok("POST", "/clock/advance", "judge", json={"hours": 1})
                    current_refs = refs if index == 0 else []
                    if isinstance(turn, dict):
                        current_refs += [j.upload(kind)["id"] for kind in turn.get("documents", [])]
                        turn = turn["text"]
                    response = j.request(
                        "POST",
                        f"/agent/threads/{thread}/messages",
                        persona,
                        json={"text": turn, "documentIds": current_refs, "locale": case["locale"]},
                    )
                    assert response.status_code == 200, "HTTP conversation failed"
                    events = [
                        json.loads(line[6:])
                        for line in response.text.splitlines()
                        if line.startswith("data: ")
                    ]
                    assert not any(e["type"] == "error" for e in events), "SSE error"
                    tokens = [e for e in events if e["type"] == "token"]
                    text = " ".join(e["text"] for e in tokens)
                    transcript.append(
                        {
                            "user": turn,
                            "assistant": text,
                            "sources": [e.get("source") for e in tokens],
                            "providerStatus": provider.status(),
                        }
                    )
                    if case.get("referenceContinuity"):
                        with app.state.store.transaction() as s:
                            current = s["threads"][thread]["_lastFacts"]
                            reference = current["familyReference"]
                            assert reference["status"] == "signed_reference_only_not_execution_authority"
                            assert reference["latePaymentPolicy"]["id"] == "HBU-LATE-01-v1"
                            if index == 0:
                                stable_reference = reference
                            assert reference == stable_reference, "Stable reference changed with topic"
                        assert not any(
                            e.get("kind") in {"approval_required", "needs", "refund"} for e in events
                        ), "Reference question requested authority"
                        if index == 1:
                            assert not any(e["type"] == "card" for e in events), (
                                "Refund follow-up became invoice cards"
                            )
                            assert current["outcome"] == "policy", "Lost read-only conversation subject"
                    if provider_name != "scripted":
                        assert tokens and all(e.get("source") == provider_name for e in tokens), (
                            "Hosted reply fell back; not counted as a hosted pass"
                        )
                    if case.get("incidentCounts"):
                        rows = [
                            a
                            for a in j.ok("GET", "/approvals?status=all")
                            if a["rawAction"].get("verificationRequired")
                        ]
                        assert len(rows) == case["incidentCounts"][index], (
                            "Duplicate or missing scam incident"
                        )
                        for row in rows:
                            binding = {k: row[k] for k in ("consentHash", "cooling", "expiresAt")}
                            assert incidents.setdefault(row["id"], binding) == binding, (
                                "Existing case binding or cooling deadline changed"
                            )
                        if index and case["incidentCounts"][index] == case["incidentCounts"][index - 1]:
                            assert not any(e.get("kind") == "approval_required" for e in events), (
                                "Support asked for another approval"
                            )
                        if index == 0 and case.get("cosignAfterFirst"):
                            j.ok(
                                "POST",
                                f"/approvals/{rows[0]['id']}/cosign",
                                "mother_lan",
                                json={"assertion": {"demo": True}},
                            )
                        incident_trace.append({"count": len(rows), "ids": [r["id"] for r in rows]})
                    if index == 0 and case.get("signRefundAfterFirst"):
                        j.approve(j.ok("GET", "/approvals")[0], "student_linh")
                    approvals = j.ok("GET", "/approvals")
                    if approvals:
                        originals.append(approvals[-1])
                with app.state.store.transaction() as s:
                    facts = s["threads"][thread]["_lastFacts"]
                    assert facts["outcome"] == case["outcome"], f"Wrong outcome: {facts['outcome']}"
                    if case["outcome"] == "refused_unpaid":
                        stopped = s["admissionDispositions"][s["users"][persona]["familyId"]]
                        assert stopped["tuitionStopped"] and not stopped["refundRequired"]
                        assert stopped["parentNotice"]["status"] == "available_in_family_app_MOCK"
                        assert not s["payments"] and not s["refunds"] and not s["grants"]
                        assert not any(t.get("_pendingIntent") == "pay" for t in s["threads"].values())
                        assert any(
                            word in transcript[-1]["assistant"].lower()
                            for word in ({"vi": ["ba", "bố"], "en": ["father", "dad"]}[case["locale"]])
                        ), "Parent notice omitted"
                    if case.get("policyTopics"):
                        assert facts["policyAdvice"]["topics"] == case["policyTopics"], "Wrong policy topic"
                        assert (
                            facts["policyAdvice"]["hypothetical"] and not facts["policyAdvice"]["caseOpened"]
                        )
                        assert all(s[k] == before[k] for k in before), (
                            "Policy question mutated financial authority or balances"
                        )
                        assert not any(e["type"] == "card" for e in events), (
                            "Policy explanation emitted an action/status card"
                        )
                        assert not any(
                            e.get("kind") in {"approval_required", "refund", "needs", "blocked"}
                            for e in events
                        ), "Policy explanation requested action"
                    if case["outcome"] == "blocked":
                        assert facts["reason"] == case["intent"], "Denial did not match actual reason"
                    if case.get("incidentCounts"):
                        assert s["denials"]["fam_minh"] == case.get(
                            "expectedDenials", case["incidentCounts"][-1]
                        ), "Support incremented attack counter"
                        assert not s["frozen"].get("fam_minh"), "Support froze the family"
                        assert (
                            sum(e["type"] == "approval_created" for e in s["events"])
                            == case["incidentCounts"][-1]
                        ), "Duplicate approval notification"
                        if case.get("cosignAfterFirst"):
                            assert next(a for a in s["approvals"].values() if a.get("_riskOnly"))[
                                "_cosigned"
                            ], "Support discarded co-sign"
                text = transcript[-1]["assistant"]
                if case.get("maxReplyChars"):
                    assert all(len(t["assistant"]) <= case["maxReplyChars"] for t in transcript), (
                        "Reply too long for phone"
                    )
                if "maxGreetings" in case:
                    assert (
                        sum(t["assistant"].casefold().startswith("linh ơi") for t in transcript)
                        <= case["maxGreetings"]
                    ), "Repeated greeting across conversation"
                assert text.count("?") + text.count("？") == case["questions"], (
                    "Incorrect clarification count"
                )
                payments = j.ok("GET", "/payments", "parent_wang" if case.get("rent") else "parent_minh")
                if case.get("rent"):
                    assert len(payments) == 1 and payments[0]["status"] == case["paymentStatus"], (
                        "Rent state mismatch or duplicate debit"
                    )
                    assert facts["paymentStatus"] == payments[0]["status"], "Reply facts overstate payment"
                    assert facts["readerName"] == "Hao" and facts["readerRole"] == "student"
                else:
                    assert len(payments) == (1 if case.get("paid") else 0), (
                        "Conversation eval unexpectedly moved funds"
                    )
                    if case.get("paid"):
                        assert facts["refundPolicy"]["beforeStart"]
                        assert len(j.ok("GET", "/approvals")) == (
                            0 if case.get("parentGuidance") or case.get("filedRefund") else 1
                        )
                        if case.get("filedRefund"):
                            refunds = j.ok("GET", "/refunds")
                            assert len(refunds) == 1 and refunds[0]["status"] == "requested"
                            assert len(j.ok("GET", "/approvals?status=all")) == 2, (
                                "Refund support opened another consent"
                            )
                        else:
                            assert j.ok("GET", "/refunds") == [], "Unsigned claim filed itself"
                for phrase in case.get("contains", []):
                    assert phrase.casefold() in text.casefold(), "Missing reader-relative relationship"
                if case.get("containsAny"):
                    assert any(phrase.casefold() in text.casefold() for phrase in case["containsAny"]), (
                        "Missing expected reply wording"
                    )
                for phrase in case.get("notContains", []):
                    assert phrase.casefold() not in text.casefold(), "Unrelated denial explanation"
                if case.get("factual") or case.get("factualKeys"):
                    assert all(
                        fact_present(text, key, facts["display"])
                        for key in case.get("factualKeys", ("invoiceAmount", "dueDate", "sendAmount"))
                    ), "Missing grounded factual answer"
                    assert (
                        ("invoice" not in facts["missingDocuments"])
                        if case.get("uploadedFacts")
                        else ("invoice" in facts["missingDocuments"])
                    ), "Known issuer record incorrectly satisfied upload requirement"
                    assert any(e.get("kind") == "quote" and e["data"].get("source") for e in events), (
                        "Missing labelled quote card"
                    )
                if case.get("refundFactualKeys"):
                    assert all(facts["display"][key] in text for key in case["refundFactualKeys"]), (
                        "Refund answer omitted grounded facts"
                    )
                if case.get("referenceFactualKeys"):
                    assert all(facts["display"][key] in text for key in case["referenceFactualKeys"]), (
                        "Known signed schedule amount/date omitted"
                    )
                approvals = j.ok("GET", "/approvals")
                if case.get("receive"):
                    assert (
                        len(approvals) == 1
                        and approvals[0]["rawAction"]["receive"]["amount"] == case["receive"]
                    ), "Wrong issuer-defined amount"
                elif case.get("parentGuidance") or case.get("filedRefund"):
                    assert not approvals, "Parent guidance created student consent"
                elif case.get("paid"):
                    assert len(approvals) == 1 and approvals[0]["action"] == "refund_claim"
                    assert approvals[0]["rawAction"]["destinationAccountId"] == "acct_parent_minh"
                    assert approvals[0]["rawAction"]["paperwork"]["deadline"] == "2027-03-16T00:00:00Z"
                elif case["outcome"] != "approval":
                    assert not approvals, "Unintended pending financial action"
                if case.get("correction"):
                    assert len(originals) == 2 and originals[0]["id"] != originals[1]["id"], (
                        "Correction reused old approval"
                    )
                    old = j.ok("GET", "/approvals/" + originals[0]["id"])
                    assert (
                        old["status"] == "rejected" and old["consentHash"] == originals[0]["consentHash"]
                    ), "Old consent was mutated instead of superseded"
            except Exception as exc:
                # Only controlled assertions/types in reports; never HTTP request/response exception bodies.
                errors.append(str(exc) if isinstance(exc, AssertionError) else type(exc).__name__)
            results.append(
                {
                    "id": case["id"],
                    "locale": case["locale"],
                    "provider": provider_name,
                    "status": "fail" if errors else "pass",
                    "errors": errors,
                    "transcript": transcript,
                    "incidents": incident_trace,
                    "ms": round((time.perf_counter() - started) * 1000, 1),
                }
            )
            app.state.store.engine.dispose()
            if provider_name != "scripted":
                print(f"{case['id']} {results[-1]['status']} {results[-1]['ms']}ms", flush=True)
    report = {
        "provider": provider_name,
        "model": provider.model if provider_name != "scripted" else None,
        "hosted": provider_name != "scripted",
        "results": results,
        "summary": {
            "passed": sum(r["status"] == "pass" for r in results),
            "failed": sum(r["status"] == "fail" for r in results),
            "total": len(results),
        },
        "limits": "Deterministic HTTP assertions; hosted style still needs native-speaker review. No model-as-judge. Local chain and MOCK screening isolate dialogue.",
    }
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(
            json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n"
        )
    return report
