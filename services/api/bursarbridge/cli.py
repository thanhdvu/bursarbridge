import argparse
import json
import os
from pathlib import Path


def main():
    from .settings import load_settings

    load_settings()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", choices=["dev", "judge", "evidence", "fixtures", "openapi", "conversation-eval"]
    )
    parser.add_argument(
        "--provider", choices=["scripted", "auto", "hosted", "openai", "anthropic"], default="scripted"
    )
    parser.add_argument("--p0", action="store_true")
    parser.add_argument("--output", default="../../evidence")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    parser.add_argument("--wsl-distro", default=os.getenv("WSL_DISTRO"))
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Scripted LLM, local commitments and synthetic screening; no WSL or API key",
    )
    args = parser.parse_args()
    if args.offline:
        if args.command not in {"dev", "judge", "evidence"}:
            parser.error("--offline is supported for dev, judge and evidence only")
        os.environ.update(CHAIN_MODE="local", SCREENING_MODE="synthetic", LLM_PROVIDER="scripted")
    if args.wsl_distro:
        os.environ["WSL_DISTRO"] = args.wsl_distro
    if args.command == "dev":
        import uvicorn

        from .runtime import infrastructure

        if not 1 <= args.port <= 65535:
            parser.error("port must be between 1 and 65535")
        infrastructure()

        os.environ.setdefault("DEMO", "1")
        public = os.getenv("PUBLIC_DEMO", "0") == "1"
        uvicorn.run(
            "bursarbridge.public:create_public_app" if public else "bursarbridge.main:create_app",
            factory=True,
            host="127.0.0.1",
            port=args.port,
            proxy_headers=True,
            forwarded_allow_ips="127.0.0.1,::1",
            access_log=not public,
        )
    elif args.command == "fixtures":
        from .fixtures import FIXTURES, pdf

        path = Path("fixtures")
        path.mkdir(exist_ok=True)
        for kind in FIXTURES:
            (path / (kind + ".pdf")).write_bytes(pdf(kind))
    elif args.command == "openapi":
        from tempfile import TemporaryDirectory

        from .chain import Chain
        from .main import create_app
        from .public import BOOTSTRAP_PATH

        with TemporaryDirectory() as folder:
            app = create_app("sqlite:///" + folder + "/openapi.db", folder, True, Chain("local"))
            schema = app.openapi()
            schema["paths"].update(BOOTSTRAP_PATH)
            Path("openapi.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
            app.state.store.engine.dispose()
    elif args.command == "conversation-eval":
        from .conversation_evals import evaluate_conversations
        from .settings import provider_name

        chosen = provider_name() if args.provider in {"auto", "hosted"} else args.provider
        if args.provider == "hosted" and chosen == "scripted":
            chosen = (
                "anthropic"
                if os.getenv("ANTHROPIC_API_KEY")
                else "openai"
                if os.getenv("OPENAI_API_KEY")
                else "scripted"
            )
        if args.provider == "hosted" and chosen == "scripted":
            path = Path("runtime/conversation_hosted.json")
            path.parent.mkdir(exist_ok=True)
            path.write_text(
                json.dumps(
                    {"status": "not_run", "reason": "No hosted API key configured", "hostedTested": False},
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(
                "HOSTED NOT RUN: no Anthropic/OpenAI key configured; adapter mocks are not live validation."
            )
            return
        target = Path(args.output)
        if args.output == "../../evidence":
            target = Path("runtime") / ("conversation_" + chosen + ".json")
        report = evaluate_conversations(chosen, target)
        for row in report["results"]:
            print(row["id"], row["status"], ", ".join(row["errors"]))
        print(json.dumps(report["summary"]))
        if report["summary"]["failed"]:
            raise SystemExit(1)
    else:
        from .scenarios import CATALOG, run_scenarios

        os.environ["LLM_PROVIDER"] = "scripted"
        if args.command in {"evidence", "judge"}:
            from .runtime import infrastructure

            infrastructure(fresh=args.command == "evidence")
        ids = [c["id"] for c in CATALOG if c["priority"] == "P0"] if args.p0 else None
        for result in run_scenarios(ids, args.output):
            if "summary" in result:
                print(json.dumps(result["summary"]))
                if result["summary"]["failed"]:
                    raise SystemExit(1)
            elif result["status"] != "running":
                print(f"{result['id']} {result['status']:4} {result['ms']:8.1f}ms {result['actual']}")
        if args.command == "evidence":
            from .runtime import package_evidence

            package_evidence(args.output)


if __name__ == "__main__":
    main()
