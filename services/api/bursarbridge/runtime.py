"""Reproducible local infrastructure launcher. No secret values in command lines."""

import json
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[3]


def command(arguments, cwd=None, timeout=300):
    subprocess.run(arguments, cwd=cwd or ROOT, check=True, timeout=timeout)


def linux(script):
    if os.name == "nt":
        path = "/mnt/" + ROOT.drive[0].lower() + ROOT.as_posix()[2:]
        distro = os.getenv("WSL_DISTRO")
        # No -d selects the user's default distro (including Ubuntu-24.04).
        command(["wsl", *(["-d", distro] if distro else []), "--", "bash", "-lc", f"cd {shlex.quote(path)} && {script}"])
    else:
        command(["bash", "-lc", script])


def infrastructure(fresh=False):
    if os.getenv("CHAIN_MODE") != "local":
        if fresh and (ROOT / "infra/fisco/nodes/127.0.0.1").exists():
            linux("bash infra/fisco/nodes/127.0.0.1/stop_all.sh && python3 infra/fisco/fresh_state.py")
        linux("bash infra/fisco/bootstrap.sh")
        deployment = ROOT / "services/api/runtime/chain-deployment.json"
        if fresh or not deployment.exists():
            npm = "npm.cmd" if os.name == "nt" else "npm"
            command([npm, "ci"], ROOT / "contracts")
            command([npm, "run", "compile"], ROOT / "contracts")
            command([sys.executable, str(ROOT / "services/api/scripts/deploy_chain.py")])
    if os.getenv("SCREENING_MODE") != "synthetic":
        linux("python3 infra/watchman/install.py && python3 infra/watchman/start.py")
        for _ in range(45):
            try:
                response = httpx.get("http://127.0.0.1:8084/v2/listinfo", timeout=2)
                info = response.json()
                if (
                    response.status_code == 200
                    and set(info.get("lists", {})) == {"us_ofac"}
                    and info["lists"]["us_ofac"] > 0
                ):
                    return
            except httpx.HTTPError:
                pass
            time.sleep(1)
        raise RuntimeError("Watchman did not index the configured government list; payments remain blocked")


def package_evidence(output):
    """Aggregate isolated traces without pretending their sequences form one log."""
    import csv
    import importlib.metadata
    import platform

    from .chain import Chain
    from .fixtures import FIXTURES, pdf
    from .store import verify

    output = Path(output)
    from .conversation_evals import evaluate_conversations

    conversation_report = evaluate_conversations("scripted", output / "conversation_eval_scripted.json")
    if conversation_report["summary"]["failed"]:
        raise RuntimeError("Conversation evals failed; see conversation_eval_scripted.json")
    if not (os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY")):
        (output / "conversation_eval_hosted.json").write_text(json.dumps({
            "status": "not_run", "hostedTested": False, "reason": "No hosted API key configured; mock HTTP tests are not live hosted validation"
        }, indent=2), encoding="utf-8", newline="\n")
    (output / ".gitattributes").write_text(
        "*.json text eol=lf\n*.jsonl text eol=lf\n*.csv text eol=lf\n*.md text eol=lf\n*.txt text eol=lf\n*.pdf -text\n",
        encoding="utf-8",
        newline="\n",
    )
    manifest = {
        "generatedAt": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "python": platform.python_version(),
        "chain": Chain().status(),
        "transport": "FastAPI HTTP TestClient",
        "provider": "scripted",
        "mockBank": True,
        "mockBursar": True,
        "liveDeployment": False,
        "files": {},
    }
    audit_lines, ops_lines, anchors, registries = [], [], [], []
    reports = json.loads((output / "scenario_results.json").read_text())
    for row in reports["results"]:
        folder = output / row["id"]
        entries = [
            json.loads(line)
            for line in (folder / "agent_audit.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        checked = verify(entries)
        if not checked["ok"]:
            raise RuntimeError("Generated audit failed: " + row["id"])
        # Bundle records retain source attribution. Independent verifier groups by run.
        audit_lines.extend({"runId": row["id"], "entry": e} for e in entries)
        ops_lines.extend(
            {"runId": row["id"], **json.loads(line)}
            for line in (folder / "sandbox_ops.jsonl").read_text().splitlines()
        )
        anchors.extend({"runId": row["id"], **a} for a in json.loads((folder / "anchors.json").read_text()))
        registry_file = folder / "registries.json"
        if registry_file.exists():
            registries.extend({"runId": row["id"], **r} for r in json.loads(registry_file.read_text()))
    for name, data in [("agent_audit.jsonl", audit_lines), ("sandbox_ops.jsonl", ops_lines)]:
        (output / name).write_text(
            "".join(json.dumps(v, ensure_ascii=False) + "\n" for v in data), encoding="utf-8"
        )
    for name, rows in [("anchors.csv", anchors), ("registries.csv", registries)]:
        fields = sorted({k for row in rows for k in row}) or ["mode"]
        with (output / name).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    attacks = {"T06", "T07", "T09", "T10", "T11", "T12", "T14", "T15", "T16", "T17", "T19", "T20"}
    report = "# Red-team report\n\n| Scenario | Control / observed outcome | Result | Audit references |\n|---|---|---|---|\n"
    report += "".join(
        f"| {r['id']} {r['expected']} | {r['actual']} | {r['status']} | {r['id']}/agent_audit.jsonl, seqs {r['auditSeqs']} |\n"
        for r in reports["results"]
        if r["id"] in attacks
    )
    (output / "redteam_report.md").write_text(report, encoding="utf-8")
    fixtures = output / "fixtures"
    fixtures.mkdir(exist_ok=True)
    for kind in FIXTURES:
        (fixtures / (kind + ".pdf")).write_bytes(pdf(kind))
    licenses = [
        {
            "name": d.metadata["Name"],
            "version": d.version,
            "license": d.metadata.get("License-Expression")
            or d.metadata.get("License", "See upstream license"),
        }
        for d in importlib.metadata.distributions()
    ]
    (output / "installed_packages.json").write_text(json.dumps(licenses, indent=2), encoding="utf-8")
    deployment = ROOT / "services/api/runtime/chain-deployment.json"
    if deployment.exists():
        (output / "chain_deployment.json").write_text(deployment.read_text(), encoding="utf-8")
    for path in output.rglob("*"):
        if path.is_file() and path.name != "manifest.json":
            import hashlib

            content = path.read_bytes()
            if path.suffix in {".json", ".jsonl", ".csv", ".md", ".txt"}:
                content = content.replace(b"\r\n", b"\n")
                path.write_bytes(content)
            manifest["files"][path.relative_to(output).as_posix()] = hashlib.sha256(content).hexdigest()
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8", newline="\n")
