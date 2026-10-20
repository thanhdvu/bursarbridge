"""The temporary Windows test proxy does not relax the VM/public provider guard."""

import pytest

from bursarbridge.chain import Chain
from bursarbridge.providers import Provider
from bursarbridge.public import create_public_app


def test_next_build_environment_does_not_inherit_llm_or_other_credentials(monkeypatch):
    import importlib.util
    from pathlib import Path

    source = Path(__file__).resolve().parents[3] / "infra/windows/live.py"
    spec = importlib.util.spec_from_file_location("windows_live", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "FISCO_PRIVATE_KEY", "GITHUB_TOKEN", "NEXT_PUBLIC_OPENAI_API_KEY"):
        monkeypatch.setenv(name, "synthetic-do-not-build")
    env = module.web_env()
    assert "synthetic-do-not-build" not in env.values()
    assert env["NEXT_PUBLIC_API_MODE"] == "live" and env["NEXT_PUBLIC_API_URL"] == "/bbapi"


@pytest.mark.parametrize("url", ["http://127.0.0.1:8317/v1", "http://localhost:8318/v1", "http://example.com/v1"])
def test_local_test_opt_in_cannot_enable_other_http_proxies(tmp_path, monkeypatch, url):
    monkeypatch.setenv("PUBLIC_LOCAL_PROXY", "1")
    monkeypatch.setenv("OPENAI_BASE_URL", url)
    with pytest.raises(ValueError, match="dedicated HTTPS"):
        create_public_app(tmp_path, Chain("local"), Provider("openai"))


@pytest.mark.parametrize("enabled", ["0", "1"])
def test_local_test_proxy_requires_explicit_opt_in(tmp_path, monkeypatch, enabled):
    monkeypatch.setenv("PUBLIC_LOCAL_PROXY", enabled)
    monkeypatch.setenv("OPENAI_BASE_URL", "http://127.0.0.1:8318/v1")
    if enabled == "0":
        with pytest.raises(ValueError, match="dedicated HTTPS"):
            create_public_app(tmp_path, Chain("local"), Provider("openai"))
    else:
        app = create_public_app(tmp_path, Chain("local"), Provider("openai"))
        assert app is not None
