> **Status, owners and deadlines: [docs/STATUS.md](docs/STATUS.md)**

# CLAUDE.md

Guide for Claude Code (and humans) working in this repository. Read `docs/context/HANDOFF.md` for the
full product history.

## Product
Internship Simulator: people starting in IT solve realistic junior test tasks ("cases") for analytics,
business analysis and QA, get a human review and rate how realistic the case felt. Main metric: share of
people who took a case and submitted work. Goals: took/invited ≥ 50%, submitted/took ≥ 30%, realism ≥ 4/5.

## Architecture
- `frontend/`: React + TS (Vite), React Router. Auth in `src/auth.ts`: direct calls to the Cognito API
  (SignUp, ConfirmSignUp, InitiateAuth USER_PASSWORD_AUTH, refresh). ID token goes to `/api` as Bearer.
  Runtime config from `/config.json` (written by Terraform).
- `backend/api/`: one Python 3.13 Lambda. `app/handler.py` (event → response), `app/routes.py`
  (`@route("GET", "/api/...")`). API Gateway has already verified the JWT; the user is in `user`.
  Routes under `/api/public/` need no sign-in. Storage: DynamoDB table `internship-simulator` (pk/sk).
  `cases/cases.json` and `professions.json` are bundled into the Lambda zip under `cases/`.
- `backend/telegram_bot/`: the old aiogram bot with its own SQLite. Do not connect it to the website.
- `infra/`: Terraform, state in S3 (`internship-simulator-tfstate-637965527585`, `use_lockfile`).
  `infra/bootstrap/` (budget, state bucket, CI role) is applied only by the account owner.
- Reviewer role = Cognito group `reviewers` (claim `cognito:groups`).

## Glossary
- **Case** (кейс): one test task. **Brief**: `brief.md`, the manager's email before `---`, data description after.
- **Candidate files**: `cases/NN/candidate/`, public, what the user downloads. **Author files**: rubric,
  data generator, reference solution; only in the private repo `internship-simulator-author`.
- **Profession / role** (професія): analytics, ba, qa are live; others are `soon` (voting).
- **Submission** (здача): link + short conclusion. **Review** (рев'ю): written by a person in `reviewers`.
- **Realism rating**: «наскільки схоже на справжнє тестове» 1–5, the product's key quality signal.

## Access and environment (what a teammate has)
- Teammates have **no AWS credentials**, and do not need them:
  - backend tests run without network or AWS;
  - `make dev` runs the frontend locally against the deployed demo (real sign-in and API);
  - deploys happen only in GitHub Actions on merge to `main`.
- PR checks run `terraform validate`, not `plan`, so an infra mistake can show up only after merge in the
  Deploy run. If Deploy fails: read the log in Actions, fix in a new PR, tell Severyn if it is an AWS permission.
- Reviewer role for testing: sign up on the demo, send Severyn your email to be added to `reviewers`;
  sign out and in again.
- Ukrainian UI voice: short, informal «ти», like a colleague. `backend/telegram_bot/texts.py` holds the
  bot's texts: reuse its wording for the same steps.
- Current status and who owns which issue: `docs/STATUS.md`. Update it in the same PR that finishes a task.

## Commands
- `make setup`, `make test`, `make lint`, `make check` (lint + tests + frontend build), `make dev`.
- Single test: `.venv/bin/python -m pytest backend/api/tests/test_routes.py -k me -q`.
- Deploy = merge to `main` (GitHub Actions). Do not run `terraform apply` from a laptop unless asked.

## How to add a case
See README → "Add a case". Only `cases/*/candidate/` is public. Run `make test` afterwards.

## Rules (from HANDOFF)
- **Never publish case answers:** `cases/*/author/`, rubrics, generators, reference solutions,
  `docs/research.md`. Do not describe a case's hidden problem in code, docs, commits or UI texts.
- **No secrets** in code, logs, commits or chat: bot token, AWS keys. Never read `.env` files.
- **UI language is Ukrainian.** Do not use «курс», «навчання», «уроки», «сертифікат». Use «тестове
  завдання», «кейс», «рев'ю», «портфоліо». Code, comments, README, docs: English.
- **Facts separate from estimates; never invent** users, numbers or feedback (especially in the report).
- Legal or financial questions: facts plus a note that this is not legal or tax advice.
- **Anything outward-facing** (public posts, messages to people, spending money) needs Severyn's explicit OK.
- Similar real test tasks are named honestly; we never copy real companies' tasks.

## What not to do
- No EC2, RDS/Aurora, NAT Gateway, Elastic IP, load balancers, OpenSearch, Marketplace, Bedrock or any
  AI model, and no domain purchase, without Severyn's explicit approval. Pay-per-use services only.
- Every AWS resource carries `project=internship-simulator` (provider `default_tags` does it).
- No `git push --force`, no direct pushes to `main`: branch + pull request.
- Do not add AI colleagues yet: the first version is without them.

## Workflow
Branch `feat/<short-name>` → small commits → PR with what changed and how it was tested → CI green →
review by a teammate → merge (deploys automatically).
