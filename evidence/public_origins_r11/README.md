# Two public origins

Round 11, 20 October 2026. The backend accepts both configured public origins without moving a visitor between hosts. The new Pages proxy and live deployment remain operator-owned; these results are local backend checks.

| Check | Result | Evidence |
|---|---|---|
| Complete regression suite | 271 passed; one upstream websockets deprecation warning. | [pytest.txt](pytest.txt) |
| New origin/proxy checks | 21 passed. Actual ES256 registration/assertion payloads for both RP IDs; wrong origin/RP, cross-origin receipt, legacy key, spoofed IP, invalid/duplicate headers and two-host cookies/redirects. | [focused_tests.txt](focused_tests.txt), [test source](../../services/api/tests/test_round11.py) |
| Scripted conversation | 80/80 passed; no hosted calls. | [transcripts](scripted_conversations.json) |
| T01-T20 | 20/20 with FISCO and native government-list Watchman. Bank and bursar remain MOCK. | [judge.txt](judge.txt), [current scenario report](../scenario_report.md) |
| Audit receipts | Current audit/Merkle bundle and real FISCO receipts independently verified. | [verification](audit_verification.txt) |

New tests use a synthetic proxy secret. The real proxy.secret was not read, copied or logged. Physical passkeys on the public hosts and the Pages-to-tunnel route still need operator acceptance after deployment. The backend expects the proxy to forward browser Origin unchanged, overwrite its authenticated IP headers, and pass through relative redirects and host-only cookies. See [Changelog v1.23](../../docs/API.md#changelog) for public API behavior.
