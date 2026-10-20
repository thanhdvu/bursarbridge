import pytest

from bursarbridge.chain import Chain
from bursarbridge.main import create_app
from bursarbridge.scenarios import Journey


@pytest.fixture(autouse=True)
def offline_tests(monkeypatch):
    monkeypatch.setenv("CHAIN_MODE", "local")
    monkeypatch.setenv("LLM_PROVIDER", "scripted")
    monkeypatch.setenv("SCREENING_MODE", "synthetic")


@pytest.fixture
def journey(tmp_path):
    app = create_app("sqlite:///" + (tmp_path / "test.db").as_posix(), tmp_path, True, Chain("local"))
    yield Journey(app)
    app.state.store.engine.dispose()
