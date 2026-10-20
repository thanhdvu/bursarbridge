from bursarbridge.conversation_evals import evaluate_conversations, fact_present


def test_schedule_check_accepts_each_signed_entry_but_rejects_missing_or_wrong_amounts():
    display = {"instalmentSchedule": "3,587,000 KRW + 3,587,000 KRW"}
    assert fact_present(
        "First: 3,587,000 KRW due January; second: 3,587,000 KRW due January", "instalmentSchedule", display
    )
    assert not fact_present("First: 3,587,000 KRW; second: 3,000,000 KRW", "instalmentSchedule", display)
    assert not fact_present("One payment of 3,587,000 KRW", "instalmentSchedule", display)


def test_scripted_conversation_eval_set():
    report = evaluate_conversations()
    failures = [r for r in report["results"] if r["status"] == "fail"]
    assert not failures, failures
