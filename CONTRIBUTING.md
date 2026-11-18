# Contributing

## Get started

First accept the GitHub invitation (email from GitHub or https://github.com/notifications), then:

```bash
git clone https://github.com/slyvkaseveryn-cloud/internship-simulator.git
cd internship-simulator
make setup        # Python venv + backend deps, npm ci in frontend/
make check        # lint, tests, frontend build: should be green before you change anything
make dev          # http://localhost:5173, uses the deployed API and sign-in
```

Needs: Git, Python 3.13 (`.python-version`), Node 24 (`.nvmrc`), `make`. On Windows use WSL, or run the
commands from the Makefile by hand. Terraform is optional locally (CI checks it).

You do not need AWS keys: the local frontend talks to the deployed demo, backend tests run without network,
and deploys happen in GitHub Actions.

| What | Command |
|---|---|
| Backend tests (API + Telegram bot) | `make test` |
| One test | `.venv/bin/python -m pytest backend/api/tests -k me -q` |
| Lint everything | `make lint` |
| Frontend only | `cd frontend && npm run dev` / `npm run lint` / `npm run build` |
| Terraform format | `terraform -chdir=infra fmt -recursive` |

Tasks without code (report #8, invitations #9, demo #10) need only Git: write in `docs/` and open a PR.
Which task is whose: [docs/STATUS.md](docs/STATUS.md).

## Branches and pull requests

1. Pick an issue on GitHub and assign yourself, so we don't do the same thing twice.
2. `git switch -c feat/<short-name>` from an up-to-date `main`.
3. Small commits. Message: what changed and why, in English.
4. Open a PR that says `Closes #<issue>`, what you changed and how you checked it (screenshot for UI).
5. CI must be green. One teammate reviews. Merge with "Squash and merge".
6. The merge deploys automatically. Open the demo URL and check your change.
7. In the same PR, update `docs/STATUS.md` (task state, what now works).

Never push to `main` directly and never force-push.

## Asking Claude Code to take a task

Claude reads `CLAUDE.md` automatically. A good request:

> Take issue #12. Read CLAUDE.md first. Create a branch, implement it with tests, run `make check`, and
> show me the diff before committing.

Tips:
- Give the issue number or paste its acceptance criteria.
- Ask for tests together with the feature, and for `make check` before you commit.
- Review the diff yourself: you are the author of the PR, not Claude.
- Claude must not read `.env` files or force-push (`.claude/settings.json` blocks both).
- Infra changes (`infra/*.tf`) need a note in the PR about what new AWS resources appear and what they cost.

## Things to keep in mind

- UI text is Ukrainian; code and docs English. Words to avoid in the UI: see CLAUDE.md.
- Case answers never go into this repository.
- Don't invent users, numbers or feedback anywhere, especially in `docs/report/`.
