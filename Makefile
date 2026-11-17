# Common commands. Run `make setup` once after cloning.
.PHONY: setup test lint check dev infra-plan deploy-frontend bot

PY := .venv/bin/python

setup:
	python3 -m venv .venv
	$(PY) -m pip install -q -r requirements-dev.txt
	cd frontend && npm ci

test:
	$(PY) -m pytest -q

lint:
	.venv/bin/ruff check backend
	cd frontend && npm run lint
	@if command -v terraform >/dev/null; then terraform -chdir=infra fmt -check -recursive; else echo "terraform not installed: skipping (CI checks it)"; fi

check: lint test
	cd frontend && npm run build

dev:
	cd frontend && npm run dev

infra-plan:
	terraform -chdir=infra init -input=false
	terraform -chdir=infra plan

deploy-frontend:
	./scripts/deploy-frontend.sh

bot:
	cd backend && ../$(PY) -m telegram_bot
