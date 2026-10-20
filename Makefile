.PHONY: install dev judge judge-offline evidence test fixtures openapi chain conversation-eval conversation-hosted ci
UV ?= uv
install:
	$(UV) sync --project services/api --frozen
dev:
	cd services/api && $(UV) run --frozen python -m bursarbridge.cli dev
judge:
	cd services/api && $(UV) run --frozen python -m bursarbridge.cli judge
judge-offline:
	cd services/api && $(UV) run --frozen python -m bursarbridge.cli judge --offline --output runtime/judge-offline
evidence:
	cd services/api && $(UV) run --frozen python -m bursarbridge.cli evidence
test:
	cd services/api && $(UV) run --frozen pytest -q
fixtures:
	cd services/api && $(UV) run --frozen python -m bursarbridge.cli fixtures
openapi:
	cd services/api && $(UV) run --frozen python -m bursarbridge.cli openapi
chain:
	bash infra/fisco/start.sh
conversation-eval:
	cd services/api && $(UV) run --frozen python -m bursarbridge.cli conversation-eval
conversation-hosted:
	cd services/api && $(UV) run --frozen python -m bursarbridge.cli conversation-eval --provider hosted
ci: install test conversation-eval conversation-hosted

.PHONY: deploy
deploy:
	bash infra/deploy/install.sh --hostname "$(DEMO_HOST)" --env-file "$(DEPLOY_ENV)"
