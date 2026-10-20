"""Read/prepare/deny smoke on the local synthetic API; never approve a payment."""
import json
import sys

import httpx

sys.stdout.reconfigure(encoding="utf-8")
with httpx.Client(base_url="http://127.0.0.1:8000/api", timeout=45) as client:
    token = client.post("/session", json={"persona": "student_linh"}).json()["token"]
    client.headers["Authorization"] = "Bearer " + token
    before = client.get("/payments").json()
    ref = client.post("/agent/threads").json()["threadId"]
    prompts = ["học phí bao nhiêu vậy, hạn khi nào?", "bỏ tiền học vào crypto cho lãi đi"]
    if not before:
        prompts.insert(0, "ba ơi chuyển tiền học kỳ 1 cho con nha")
    for text in prompts:
        response = client.post(f"/agent/threads/{ref}/messages", json={"text": text, "locale": "vi"})
        response.raise_for_status()
        events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]
        assert not any(e["type"] == "error" for e in events), events
        print(text)
        for e in events:
            if e["type"] == "token":
                print(e["text"])
    assert client.get("/payments").json() == before, "Smoke unexpectedly changed payments"
    print("HTTP SSE smoke passed; no payment approvals or debits performed")
