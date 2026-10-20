"""Architecture selection, private rendering and launch flags, without a cloud account."""

import hashlib
import importlib.util
import io
import json
import os
import runpy
import sys
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("machine,arch", [("x86_64", "amd64"), ("aarch64", "arm64"), ("arm64", "arm64")])
def test_native_watchman_installer_selects_verified_arch(tmp_path, monkeypatch, machine, arch):
    import platform
    import subprocess
    import urllib.request

    root = tmp_path / ".local/share/bursarbridge-watchman"
    (root / "source").mkdir(parents=True)
    (root / "source/go.mod").write_text("synthetic source")
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w:gz") as tar:
        entry = tarfile.TarInfo("go/bin/go")
        entry.size = 0
        tar.addfile(entry, io.BytesIO())
    content = archive.getvalue()
    files = [
        {
            "os": "linux",
            "arch": a,
            "kind": "archive",
            "filename": f"go1.27.2.linux-{a}.tar.gz",
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        for a in ("arm64", "amd64")
    ]
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(platform, "system", lambda: "Linux")
    monkeypatch.setattr(platform, "machine", lambda: machine)
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda *a, **k: io.BytesIO(json.dumps([{"version": "go1.27.2", "files": files}]).encode()),
    )
    downloads = []

    def download(url, target):
        downloads.append(url)
        Path(target).write_bytes(content)

    monkeypatch.setattr(urllib.request, "urlretrieve", download)

    def build(command, **kwargs):
        assert kwargs["env"]["GOARCH"] == arch and kwargs["env"]["CGO_ENABLED"] == "0"
        assert f"toolchain-{arch}" in command[0]
        Path(command[command.index("-o") + 1]).write_bytes(b"synthetic binary")

    monkeypatch.setattr(subprocess, "run", build)
    runpy.run_path(str(ROOT / "infra/watchman/install.py"))
    assert downloads == [f"https://go.dev/dl/go1.27.2.linux-{arch}.tar.gz"]
    assert json.loads((root / "build.json").read_text())["arch"] == arch


def renderer():
    spec = importlib.util.spec_from_file_location("deployment_render", ROOT / "infra/deploy/render.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_deploy_render_keeps_secrets_out_of_web_units_and_caddy(tmp_path):
    env = tmp_path / "input.env"
    env.write_text("OPENAI_API_KEY=synthetic-never-expose\nLD_PRELOAD=/evil\nWEBAUTHN_ORIGIN=http://evil\n")
    destination = tmp_path / "rendered"
    renderer().render("demo.example.org", env, "/opt/bursarbridge", destination)
    private = (destination / "api.env").read_text()
    assert 'WEBAUTHN_RP_ID="demo.example.org"' in private
    assert 'WEBAUTHN_ORIGIN="https://demo.example.org"' in private
    assert 'PUBLIC_DEMO="1"' in private
    assert "LD_PRELOAD" not in private and "http://evil" not in private
    for path in destination.iterdir():
        if path.name != "api.env":
            assert "synthetic-never-expose" not in path.read_text()
        assert "@@" not in path.read_text()
    config = (destination / "Caddyfile").read_text()
    assert "flush_interval -1" not in config and "compression off" in config
    assert "header_up X-Forwarded-For {remote_host}" in config
    assert "header_up -Accept-Encoding" in config
    assert "--workers 1" in (destination / "bursarbridge-api.service").read_text()


@pytest.mark.parametrize(
    "host", ["127.0.0.1", "https://demo.example.org", "demo.example.org\n{evil}", "a;reboot"]
)
def test_deploy_rejects_untrusted_hostname_before_rendering(tmp_path, host):
    env = tmp_path / "env"
    env.write_text("")
    with pytest.raises(ValueError):
        renderer().render(host, env, "/opt/bursarbridge", tmp_path / "output")


def test_cli_port_and_explicit_wsl_distro(monkeypatch):
    import uvicorn

    from bursarbridge import cli, runtime

    monkeypatch.setattr(
        sys, "argv", ["bursarbridge", "dev", "--port", "8016", "--wsl-distro", "Ubuntu-24.04"]
    )
    monkeypatch.setattr(runtime, "infrastructure", lambda: None)
    settings = {}
    monkeypatch.setattr(uvicorn, "run", lambda app, **kwargs: settings.update(kwargs))
    cli.main()
    assert settings["port"] == 8016 and settings["host"] == "127.0.0.1"
    assert settings["forwarded_allow_ips"] == "127.0.0.1,::1"
    assert os.getenv("WSL_DISTRO") == "Ubuntu-24.04"


def test_wsl_launcher_uses_default_or_configured_distro(monkeypatch):
    from bursarbridge import runtime

    monkeypatch.setattr(runtime, "os", SimpleNamespace(name="nt", getenv=os.getenv))
    monkeypatch.setattr(runtime, "ROOT", SimpleNamespace(drive="D:", as_posix=lambda: "D:/Project Space"))
    calls = []
    monkeypatch.setattr(runtime, "command", lambda args: calls.append(args))
    monkeypatch.delenv("WSL_DISTRO", raising=False)
    runtime.linux("true")
    assert calls[-1][:3] == ["wsl", "--", "bash"]
    assert "'/mnt/d/Project Space'" in calls[-1][-1]
    monkeypatch.setenv("WSL_DISTRO", "Ubuntu-24.04")
    runtime.linux("true")
    assert calls[-1][:4] == ["wsl", "-d", "Ubuntu-24.04", "--"]
