from bursarbridge.scenarios import P0, run_scenarios


def test_p0_scenarios():
    results = list(run_scenarios([f"T{i:02}" for i in sorted(P0)]))
    failures = [r for r in results if r.get("status") == "fail"]
    assert not failures, failures
