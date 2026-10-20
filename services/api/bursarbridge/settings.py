"""Explicit API-local dotenv configuration; process environment takes precedence."""

import os
from pathlib import Path

from dotenv import load_dotenv


def load_settings():
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)


def provider_name():
    load_settings()
    configured = os.getenv("LLM_PROVIDER", "auto").strip().lower()
    if configured != "auto":
        return configured
    if os.getenv("ANTHROPIC_API_KEY", "").strip():
        return "anthropic"
    if os.getenv("OPENAI_API_KEY", "").strip():
        return "openai"
    return "scripted"
