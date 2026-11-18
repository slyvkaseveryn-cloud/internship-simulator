> **Status, owners and deadlines: [docs/STATUS.md](docs/STATUS.md)**

# Internship Simulator

A website where people starting in IT complete realistic junior **test tasks** ("cases"), get a
team-lead style review, and leave with a portfolio project.

**Demo:** https://d174ecvpoyspb1.cloudfront.net · **Telegram bot (earlier prototype):** [@intern_sim_bot](https://t.me/intern_sim_bot)

Team: Severyn Slyvka, Lev Zhuraiev, Danylo Koval (UCU). Product one-pager: [docs/context/one-pager.pdf](docs/context/one-pager.pdf).

## What the product does

Junior vacancies ask for real work samples, but beginners only have tutorial projects. Real company test
tasks are rarely published, and after a rejection nobody explains what was wrong.

A case looks like a real take-home task: a vague email from a manager, messy input data or a spec, a
deadline and a suggested 20-minute first step. The user submits a link and a short conclusion, a reviewer
from our team writes a review, and the user rates how close the case felt to a real test task.

| Role | Cases |
|---|---|
| Data / product analyst | 01 Trial-to-paid conversion dropped · 02 A/B price test |
| Business analyst | 03 "Refund" button requirements · 04 Why orders get cancelled |
| QA engineer | 05 Checkout page before release · 06 Reminder feature: gaps in the spec |

Marketing, Customer Support, PM and HR are shown as "coming soon" with a vote button; the next role is the
one with the most votes. The site's UI is in Ukrainian; code and docs are in English.

Case texts and data are our own. Each case card honestly says where similar tasks are given. Answers
(rubrics, data generators, reference solutions) are kept in a separate private repository and are never
published here.

## Architecture

```
browser ──HTTPS──> CloudFront (*.cloudfront.net)
                    ├── /*        -> private S3 bucket: React app, config.json, cases/*/candidate files
                    └── /api/*    -> API Gateway HTTP API ──JWT check (Cognito)──> Lambda (Python) -> DynamoDB
browser ──HTTPS──> Cognito user pool (sign-up, email code, sign-in)
```

Everything is pay-per-use, with no always-on servers: S3, CloudFront, Cognito, API Gateway HTTP API, Lambda,
DynamoDB on-demand. Region `eu-central-1`. Every resource is tagged `project=internship-simulator`.
Decisions are recorded in [docs/context/adr](docs/context/adr).

| Folder | What is inside |
|---|---|
| `frontend/` | React + TypeScript (Vite). Talks to Cognito directly and to `/api` |
| `backend/api/` | Lambda handler and routes, tests |
| `backend/telegram_bot/` | The earlier Telegram bot (aiogram, SQLite). Runs separately, has its own database |
| `cases/` | `cases.json`, `professions.json` and the candidate files of every case |
| `infra/` | Terraform for the app; `infra/bootstrap/` for the budget, state bucket and CI role |
| `docs/` | Context, decisions (ADR), report template |

## Run locally

Requirements: Python 3.13, Node 24, (for deploys) Terraform 1.10+ and AWS CLI.

```bash
make setup          # .venv with backend deps, npm ci in frontend/
make test           # backend tests (API + Telegram bot)
make lint           # ruff, eslint, terraform fmt
make dev            # frontend on http://localhost:5173
```

`make dev` proxies `/api`, `/config.json` and `/cases` to the deployed demo, so sign-up and sign-in work
locally against the real Cognito pool without any AWS credentials. To point at another deployment:
`SITE_URL=https://xxxx.cloudfront.net make dev`.

Telegram bot: `cp backend/telegram_bot/.env.example backend/telegram_bot/.env`, fill in the token from
@BotFather and your Telegram ID, then `make bot`.

## Deploy

Normal path: **merge a pull request into `main`.** GitHub Actions runs the tests, then `terraform apply` in
`infra/` and uploads the frontend (`.github/workflows/deploy.yml`). It reaches AWS through an OIDC role, so no
AWS keys are stored in GitHub.

Manual deploy (account owner):

```bash
terraform -chdir=infra init && terraform -chdir=infra apply   # infrastructure, case files, config.json
./scripts/deploy-frontend.sh                                  # build and upload the React app
```

One-time bootstrap, already done: `infra/bootstrap/` creates the cost budget (alert above $1 of real spend
after credits), the Terraform state bucket and the GitHub OIDC role. The role trusts only workflows on `main`
of this repository, identified by GitHub's immutable subject (`github_sub_prefix` in `infra/bootstrap/main.tf`).

### Give someone the reviewer role

```bash
aws cognito-idp admin-add-user-to-group --region eu-central-1 \
  --user-pool-id "$(terraform -chdir=infra output -raw user_pool_id)" \
  --username <their email> --group-name reviewers
```

They need to sign in again to get the new role.

## Metrics for the report

Every step of the user's path is an event in DynamoDB (`opened`, `signed_up`, `profession_chosen`,
`case_viewed`, `case_taken`, `submitted`, `review_sent`, `feedback_sent`, `donate_clicked`). The numbers:

```bash
.venv/bin/python scripts/metrics.py --csv docs/report/data   # needs the owner's AWS read access
```

It prints the funnel in people (not clicks) and writes `funnel.csv`, `feedback.csv` and `events.csv`. The team
(Cognito group `reviewers`), test accounts (`@example.com`, `e2e-…`, `+test`) and any `--exclude <email>` are
left out, together with their anonymous visits. The CSVs contain emails: do not commit them to the public repo.

## Add a case

1. Create `cases/NN-name/candidate/` with `brief.md` (the manager's email, then `---`, then the data
   description) and the input files. Keep answers out of this folder.
2. Add an entry to `cases/cases.json` (role, title, deadline, first step, "similar test tasks", files).
3. `make test`: `test_every_case_is_complete` checks that every listed file exists.
4. Put the rubric and the data generator into the private author repository.
5. Open a pull request. After the merge the files are uploaded to the site.

## Delete everything after the course

```bash
terraform -chdir=infra destroy                     # site, API, Lambda, Cognito (all users!), DynamoDB
# then the bootstrap: remove `prevent_destroy` from infra/bootstrap/main.tf, empty the state bucket, and
terraform -chdir=infra/bootstrap destroy -var alert_email=<email>
```

Check that nothing is left: AWS Console → Resource Groups → Tag Editor → tag `project=internship-simulator`.

## Cost

Designed for $0 out of pocket: every service is pay-per-use and within the free tier or promotional credits at
prototype scale. Cognito's built-in email sender is free but limited to 50 emails a day. A budget alert fires if
real spend after credits exceeds $1 or is forecast to.
