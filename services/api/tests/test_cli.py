"""The documented keyless entry point cannot accidentally start infrastructure or a hosted model."""

import os
import sys

import pytest

from bursarbridge import cli, runtime


def test_offline_overrides_existing_hosted_and_chain_settings(monkeypatch):
    import uvicorn

    for key, value in [("CHAIN_MODE", "fisco"), ("SCREENING_MODE", "watchman"), ("LLM_PROVIDER", "openai")]:
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("PUBLIC_DEMO", "0")
    monkeypatch.setattr(sys, "argv", ["bursarbridge", "dev", "--offline", "--port", "18002"])
    seen = []

    def infrastructure():
        assert (os.environ["CHAIN_MODE"], os.environ["SCREENING_MODE"], os.environ["LLM_PROVIDER"]) == (
            "local",
            "synthetic",
            "scripted",
        )
        seen.append(True)

    monkeypatch.setattr(runtime, "infrastructure", infrastructure)
    monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: seen.append(kwargs["port"]))
    cli.main()
    assert seen == [True, 18002]


def test_offline_cannot_be_combined_with_a_hosted_evaluation(monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["bursarbridge", "conversation-eval", "--offline", "--provider", "hosted"]
    )
    with pytest.raises(SystemExit) as stopped:
        cli.main()
    assert stopped.value.code == 2
