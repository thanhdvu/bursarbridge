"""Optional real TLS proxy/isolation/SSE drill; no cloud, keys or system CA changes.
Run from services/api: uv run --frozen python scripts/public_proxy_smoke.py.
Uses isolated loopback ports 8016, 8017 and 19443; fails if occupied.
Downloads the pinned official Caddy release, verified against its SHA-512 manifest.
"""

import concurrent.futures
import hashlib
import json
import os
import platform
import subprocess
import tarfile
import threading
import time
import urllib.request
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
import uvicorn
from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route

from bursarbridge.chain import Chain
from bursarbridge.providers import Provider
from bursarbridge.public import create_public_app


def download_caddy(directory):
    """Official pinned release and SHA-512 manifest; no trust-store installation."""
    version = "2.11.7"
    system = "windows" if os.name == "nt" else "linux"
    arch = {"AMD64": "amd64", "x86_64": "amd64", "aarch64": "arm64", "arm64": "arm64"}[platform.machine()]
    suffix = "zip" if system == "windows" else "tar.gz"
    name = f"caddy_{version}_{system}_{arch}.{suffix}"
    base = f"https://github.com/caddyserver/caddy/releases/download/v{version}/"
    directory.mkdir(parents=True, exist_ok=True)
    manifest = urllib.request.urlopen(base + f"caddy_{version}_checksums.txt", timeout=30).read().decode()
    expected = next(line.split()[0] for line in manifest.splitlines() if line.split()[-1] == name)
    archive = directory / name
    if not archive.exists():
        urllib.request.urlretrieve(base + name, archive)
    if hashlib.sha512(archive.read_bytes()).hexdigest() != expected:
        raise RuntimeError("Caddy archive checksum mismatch")
    binary = directory / ("caddy.exe" if system == "windows" else "caddy")
    if system == "windows":
        with zipfile.ZipFile(archive) as z:
            binary.write_bytes(z.read("caddy.exe"))
    else:
        with tarfile.open(archive) as t:
            binary.write_bytes(t.extractfile("caddy").read())
        binary.chmod(0o755)
    (directory / "provenance.json").write_text(
        json.dumps({"version": version, "source": base + name, "sha512": expected}, indent=2)
    )
    return binary


ROOT = Path(__file__).resolve().parents[3]
runtime = Path(__file__).resolve().parents[1] / "runtime"
runtime.mkdir(exist_ok=True)
os.environ["LLM_PROVIDER"] = "scripted"
os.environ["SCREENING_MODE"] = "synthetic"


class Slow(Provider):
    def propose(self, *args):
        time.sleep(1)
        return super().propose(*args)

    def reply(self, *args):
        time.sleep(1)
        return super().reply(*args)


with TemporaryDirectory(prefix="bb-public-") as folder:
    temp = Path(folder)
    app = create_public_app(temp / "sandboxes", Chain("local"), Slow("scripted"))
    web = Starlette(
        routes=[Route("/{path:path}", lambda request: HTMLResponse("<html>synthetic web upstream</html>"))]
    )
    servers = []
    threads = []
    for application, port in [(app, 8016), (web, 8017)]:
        server = uvicorn.Server(
            uvicorn.Config(
                application,
                host="127.0.0.1",
                port=port,
                log_level="error",
                proxy_headers=True,
                forwarded_allow_ips="127.0.0.1,::1",
            )
        )
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        servers.append(server)
        threads.append(thread)
    for _ in range(100):
        if all(s.started for s in servers):
            break
        time.sleep(0.05)
    assert all(s.started for s in servers), "Test ports unavailable"
    config = (
        (ROOT / "infra/deploy/Caddyfile.template")
        .read_text()
        .replace("@@HOST@@", "https://localhost:19443")
        .replace("127.0.0.1:8000", "127.0.0.1:8016")
        .replace("127.0.0.1:3000", "127.0.0.1:8017")
    )
    config = "{\n admin off\n skip_install_trust\n auto_https disable_redirects\n}\n" + config.replace(
        "https://localhost:19443 {", "https://localhost:19443 {\n tls internal"
    )
    path = temp / "Caddyfile"
    path.write_text(config)
    binary = download_caddy(runtime / "proxy-tools")
    environment = {
        **{
            k: v
            for k, v in os.environ.items()
            if k not in {"OPENAI_API_KEY", "ANTHROPIC_API_KEY", "FISCO_PRIVATE_KEY"}
        },
        "APPDATA": str(temp / "caddy-data"),
        "XDG_DATA_HOME": str(temp / "caddy-data"),
        "XDG_CONFIG_HOME": str(temp / "caddy-config"),
    }
    with (runtime / "public_proxy_smoke.log").open("w") as log:
        validated = subprocess.run(
            [str(binary), "validate", "--config", str(path), "--adapter", "caddyfile"],
            env=environment,
            stdout=log,
            stderr=log,
        )
        assert validated.returncode == 0, "Caddy config validation failed; see ignored runtime log"
        process = subprocess.Popen(
            [str(binary), "run", "--config", str(path), "--adapter", "caddyfile"],
            env=environment,
            stdout=log,
            stderr=log,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        try:
            with (
                httpx.Client(
                    base_url="https://localhost:19443",
                    verify=False,
                    trust_env=False,
                    timeout=30,
                    follow_redirects=True,
                ) as a,
                httpx.Client(
                    base_url="https://localhost:19443",
                    verify=False,
                    trust_env=False,
                    timeout=30,
                    follow_redirects=True,
                ) as b,
            ):
                for _ in range(100):
                    try:
                        if a.get("/bbapi/health").status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    time.sleep(0.1)
                for client in (a, b):
                    response = client.get("/vi/demo?live=1", headers={"Accept": "text/html"})
                    assert response.status_code == 200 and "synthetic web" in response.text
                    assert client.cookies.get("bb_sandbox")

                def login(persona):
                    response = a.post("/bbapi/session", json={"persona": persona})
                    response.raise_for_status()
                    return persona, {"Authorization": "Bearer " + response.json()["token"]}

                with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                    headers = dict(pool.map(login, ["student_linh", "parent_minh", "mother_lan", "judge"]))
                other = {
                    "Authorization": "Bearer "
                    + b.post("/bbapi/session", json={"persona": "student_linh"}).json()["token"]
                }
                assert a.get("/bbapi/me", headers=other).status_code == 401
                ref = a.post("/bbapi/agent/threads", headers=headers["student_linh"]).json()["threadId"]
                started = time.perf_counter()
                rows = []
                with a.stream(
                    "POST",
                    f"/bbapi/agent/threads/{ref}/messages",
                    headers=headers["student_linh"],
                    json={"text": "pay tuition"},
                ) as response:
                    assert response.status_code == 200 and "content-encoding" not in response.headers
                    for line in response.iter_lines():
                        if line.startswith("data: "):
                            event = json.loads(line[6:])
                            rows.append(
                                {
                                    "type": event["type"],
                                    "ms": round(1000 * (time.perf_counter() - started), 1),
                                    "source": event.get("source"),
                                }
                            )
                assert rows[0]["type"] == "step" and rows[0]["ms"] < 500
                assert (
                    rows[-1]["type"] == "done" and next(r for r in rows if r["type"] == "token")["ms"] > 1500
                )
                assert a.post("/bbapi/demo/reset", headers=headers["judge"]).status_code == 200
                assert b.get("/bbapi/me", headers=other).status_code == 200
                report = {
                    "caddy": json.loads((runtime / "proxy-tools/provenance.json").read_text()),
                    "transport": "actual loopback TLS through Caddy (private test CA, trust installation disabled)",
                    "configValidated": True,
                    "bootstrapBeforeParallelPersonas": True,
                    "crossSandboxTokenRejected": True,
                    "resetIsolated": True,
                    "encoding": "none",
                    "events": rows,
                    "limits": "Scripted delayed provider, local hash chain, synthetic screening and small HTML upstream isolate reverse-proxy behavior. No cloud deployment or real HTTPS certificate claim.",
                }
                (runtime / "public_proxy_smoke.json").write_text(json.dumps(report, indent=2))
                print(
                    json.dumps(
                        {
                            "firstStepMs": rows[0]["ms"],
                            "replyMs": next(r for r in rows if r["type"] == "token")["ms"],
                            "caddy": report["caddy"]["version"],
                            "resetIsolated": True,
                        }
                    )
                )
        finally:
            process.terminate()
            process.wait(10)
            for server in servers:
                server.should_exit = True
            for thread in threads:
                thread.join(10)
