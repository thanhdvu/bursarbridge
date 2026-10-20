"""Render deployment files without evaluating shell or exposing private env values."""

import argparse
import json
import re
from pathlib import Path

from dotenv import dotenv_values


def render(host, env_file, root, output):
    if not re.fullmatch(r"(?=.{4,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}", host):
        raise ValueError("A fixed DNS hostname is required, not a URL or IP")
    if not re.fullmatch(r"/[a-zA-Z0-9_./-]+", str(root)) or Path(root).resolve() == Path("/"):
        raise ValueError("Unsafe deployment root")
    values = dotenv_values(env_file, interpolate=False)
    allowed = {"OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL", "OPENAI_TIMEOUT_SECONDS", "ANTHROPIC_API_KEY", "ANTHROPIC_MODEL", "LLM_PROVIDER", "PUBLIC_LLM_DAILY_CALLS", "PUBLIC_LLM_HOURLY_CALLS", "PUBLIC_AGENT_PER_MINUTE", "PUBLIC_AGENT_PER_HOUR", "PUBLIC_MAX_SANDBOXES", "PUBLIC_SANDBOX_IDLE_HOURS", 'PUBLIC_NEW_PER_IP_MINUTE', 'PUBLIC_NEW_PER_IP_HOUR', 'PUBLIC_NEW_GLOBAL_HOUR', 'PUBLIC_NEW_GLOBAL_DAY', 'PUBLIC_SANDBOX_PROTECT_MINUTES'}
    config = {k: v for k, v in values.items() if k in allowed and v}
    if any(not v.isascii() or any(ord(c) < 32 for c in v) for v in config.values()):
        raise ValueError("Env values must be single-line ASCII")
    if not config.get("OPENAI_BASE_URL", "https://api.openai.com/v1").startswith("https://"):
        raise ValueError("Public hosting requires a dedicated HTTPS API key, not a local proxy")
    config.update(DEMO="1", PUBLIC_DEMO="1", CHAIN_MODE="fisco", SCREENING_MODE="watchman", PUBLIC_DATA_DIR="/var/lib/bursarbridge/sandboxes", WEBAUTHN_RP_ID=host, WEBAUTHN_ORIGIN="https://" + host)
    config.setdefault("LLM_PROVIDER", "auto")
    config.setdefault("OPENAI_BASE_URL", "https://api.openai.com/v1")
    config.setdefault("OPENAI_MODEL", "gpt-4.1-mini")
    config.setdefault("OPENAI_TIMEOUT_SECONDS", "20")
    config.setdefault("PUBLIC_LLM_DAILY_CALLS", "500")
    config.setdefault("PUBLIC_LLM_HOURLY_CALLS", "100")
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    for name, data in [("api.env", config), ("web.env", {"NEXT_PUBLIC_API_MODE": "live", "NEXT_PUBLIC_API_URL": "/bbapi", "NEXT_TELEMETRY_DISABLED": "1"})]:
        path = destination / name
        path.write_text("".join(k + "=" + json.dumps(v) + "\n" for k, v in data.items()), encoding="utf-8")
        path.chmod(0o600)
    for path in Path(__file__).parent.glob("*.template"):
        content = path.read_text().replace("@@ROOT@@", str(root)).replace("@@HOST@@", host)
        (destination / path.name.removesuffix(".template")).write_text(content, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    for name in ("hostname", "env-file", "root", "output"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args()
    render(args.hostname, args.env_file, args.root, args.output)
    print("Deployment files rendered; private env values omitted")
