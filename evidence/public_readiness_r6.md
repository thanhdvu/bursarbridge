# Round 6 local readiness evidence

This is a bounded **synthetic public demo**, not production banking. No cloud account,
VM, DNS, public certificate, firewall rule or real-money operation was performed.
The VM acceptance gates remain in the [deployment guide](../docs/deploy/ubuntu-vm.md).

| Check | Observed evidence | Limits |
|---|---|---|
| Regression suite | 160 pytest tests passed; ruff passed | Windows Python 3.12; local/HTTP-mocked security failures, not penetration certification |
| Scripted dialogue | [41/41](conversation_eval_scripted.json) | Deterministic fixtures |
| Hosted dialogue | [41/41](conversation_eval_hosted_r6.json), gpt-6.1-sol | Owner's private local proxy on 8318; no claim about another public model |
| Scripted judge | [20/20 T01-T20](scenario_results.json) | Real local four-node FISCO and government-only native Watchman; MOCK bank/bursar and labelled DEMO authentication |
| Independent audit check | 20 runs, 147 entries, 36 receipt/root anchors | Existing local FISCO; no chain reset for this round |
| Concurrent families | [two complete journeys](public_family_r6.json), isolated reset, eight unique real anchor indices | Public ASGI HTTP TestClient; scripted provider, MOCK bank/bursar |
| Actual Caddy TLS/SSE | [report](public_caddy_r6.json), first step 54.4 ms vs reply 2080.9 ms, no encoding, cookie before parallel sessions | Private test CA without system trust installation, local hash chain and synthetic screening isolate proxy behavior |
| ARM Watchman | [actual arm64 binary under QEMU 8.2.2](watchman_arm64_r6.json); only us_ofac, 19,457 entries | Cross-built and emulated; not fresh native arm64 VM installation |
| Deployment structure | [systemd verification / architecture plans](deployment_validation_r6.json), verified official Node binary | Relocated executable paths, no installed services; unrelated WSL systemd warnings retained |
| Linux PDF limits | [normal/injection/over-page probes](public_pdf_worker_r6.json) | Native Linux Python 3.12 subprocess; resource isolation, same UID, not a malware sandbox |

The first ARM probe used Ubuntu 22's older QEMU 6.2 and faulted after indexing;
[raw failed report](watchman_arm64_qemu6_r6.json) is retained. Updating only the
emulator to Ubuntu 24's QEMU 8.2.2 passed; [official package provenance](qemu_provenance_r6.json).
This does not imply a change to Watchman's native ARM code.

Reproduce Caddy and concurrent journey drills using
[public_proxy_smoke.py](../services/api/scripts/public_proxy_smoke.py) and
[public_family_smoke.py](../services/api/scripts/public_family_smoke.py).
Stop the API before the real-chain drill or CLI judge: signer coordination is in-process.
The public API scenario runner instead shares that process's serialized chain adapter.

Public-mode outage, budget, reset, isolation, proxy trust, lifecycle and storage controls
are tested in [test_public.py](../services/api/tests/test_public.py).
[Deployment tests](../services/api/tests/test_deployment.py) exercise arch selection,
official checksum selection, config rendering, secret exclusion and CLI port/distro flags.
[PDF tests](../services/api/tests/test_pdf_worker.py) cover worker bounds and credential
environment exclusion. The deterministic [policy](../services/api/bursarbridge/policy.py)
was not loosened. Shared networks have separate cookie identities; resets cannot reset
admission counters. Rate limits are abuse resistance, not DDoS or dollar guarantees.

Remaining operator gates: dedicated capped HTTPS API key; fresh native-arm64 Ubuntu VM
installation/reboot; public DNS/TLS/firewall reachability; real hardware passkey on the
fixed hostname; public-model hosted eval; phone/mainland-network check. Separate
clearly MOCK web fallback is a separate build/link, not claimed automatic UI failover.
