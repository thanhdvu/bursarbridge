"""Public PDF work cannot hold the ledger lock or inherit hosted credentials."""

import json
import subprocess
import threading
from types import SimpleNamespace

import pytest

from bursarbridge import pdf_worker
from bursarbridge.engine import DomainError


def test_public_worker_receives_original_bytes_but_no_credentials(monkeypatch):
    monkeypatch.setattr(pdf_worker.sys, "platform", "linux")
    monkeypatch.setenv("OPENAI_API_KEY", "synthetic-worker-must-not-see")

    def run(command, **kwargs):
        assert command[-1].endswith("pdf_worker.py")
        assert kwargs["input"] == b"%PDF-synthetic"
        assert kwargs["timeout"] == 5 and kwargs["stderr"] == subprocess.DEVNULL
        assert "OPENAI_API_KEY" not in kwargs["env"]
        return SimpleNamespace(returncode=0, stdout=json.dumps({"text": "untrusted document text"}).encode())

    monkeypatch.setattr(pdf_worker.subprocess, "run", run)
    assert pdf_worker.extract_public_text(b"%PDF-synthetic") == "untrusted document text"


def test_public_worker_timeout_releases_the_actual_parser_slot(monkeypatch):
    monkeypatch.setattr(pdf_worker.sys, "platform", "linux")
    monkeypatch.setattr(pdf_worker, "SLOTS", threading.BoundedSemaphore(1))

    def timeout(*a, **k):
        raise subprocess.TimeoutExpired("synthetic worker", 5)

    monkeypatch.setattr(pdf_worker.subprocess, "run", timeout)
    with pytest.raises(DomainError) as exc:
        pdf_worker.extract_public_text(b"%PDF-synthetic")
    assert exc.value.code == "DOCUMENT_PARSE_LIMIT"
    monkeypatch.setattr(
        pdf_worker.subprocess, "run", lambda *a, **k: SimpleNamespace(returncode=0, stdout=b'{"text":"ok"}')
    )
    assert pdf_worker.extract_public_text(b"%PDF-synthetic") == "ok"


def test_public_text_documents_are_bounded_before_parsing():
    with pytest.raises(DomainError) as exc:
        pdf_worker.extract_public_text(b"x" * 12001)
    assert exc.value.code == "DOCUMENT_SIZE"
