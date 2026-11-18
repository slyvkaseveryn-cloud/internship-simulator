# Project status

_Updated: 2026-11-18 · updated after every merged task_

**Demo: Thursday 19.11.2026.** Each of us submits the repository link and the demo URL.

## Works now

All of this is deployed and checked end-to-end on a 375px phone viewport with throwaway test accounts
(deleted afterwards).

| What | Where |
|---|---|
| Demo site over HTTPS | https://d174ecvpoyspb1.cloudfront.net |
| Public home: what it is + «Зареєструватись» | `/` |
| Sign-up with an email code, sign-in, password reset | `/signup`, `/signin`, `/reset` |
| Roles (coming-soon roles greyed out) → cases of a role → case page (manager's email, files, time, deadline, 20-minute first step, «Схожі тестові») | `/cases`, `/roles/:role`, `/cases/:id` |
| «Беру кейс» → submit a link + conclusion → statuses in «Мої кейси» | case page, `/my` |
| Feedback: liked, hindered, realism 1–5, would pay for a review (stored with email and time); works without taking a case | «Залишити відгук» in the top menu and on every case page, `/feedback` |
| Reviewer page: queue of submissions, review form (good / fix / next) | `/review` (group `reviewers`) |
| Student sees the review, link to rate realism, «Підтримати волонтерів» | case page after the review |
| Funnel events and `scripts/metrics.py` (people, feedback CSV, team and test accounts excluded) | README → "Metrics for the report" |
| Reviewers: Severyn, Lev, Danylo (Cognito group `reviewers`) | |
| CI on every pull request, deploy on merge to `main` | GitHub → Actions |
| Telegram bot (earlier prototype, separate data) | [@intern_sim_bot](https://t.me/intern_sim_bot) |

## Who does what (until Thursday)

| Issue | Task | Owner | State |
|---|---|---|---|
| [#1](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/1) | Roles, case list and case page | Severyn + Claude | done |
| [#2](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/2) | Take a case, submit, statuses | Severyn + Claude | done |
| [#14](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/14) | Feedback form | Severyn + Claude | done |
| [#6](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/6) | Funnel events and metrics | Severyn + Claude | done (a script, not a page) |
| [#7](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/7) | «Support volunteers» button | Severyn + Claude | done, **link missing**: Severyn picks the fund |
| [#3](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/3) | Reviewer page and review form | Severyn + Claude | done (minimal) |
| [#4](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/4) | Show the review, realism rating | Severyn + Claude | done (rating = feedback form) |
| [#5](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/5) | Votes for «coming soon» roles | — | not started (roles are only greyed out) |
| [#8](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/8) | Report template and PDF build | Lev | to do; numbers from `scripts/metrics.py` |
| [#9](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/9) | Invite the first users (cohort) | Danylo | to do; text needs Severyn's OK |
| [#10](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/10) | End-to-end check, copy review, demo script | Danylo | can start now: the whole path works |

To set the donate link: `donate_url = "https://…"` in `infra/variables.tf` (default) and merge; it reaches the
site through `config.json` without a frontend rebuild.

## Why the report matters most

The course grades three things: the repository (3 points), a deployed prototype with sign-in (3 points) and
**the report (4 points)**. The first two are mostly done; the report is the largest part of the grade and it
can only be written from **real people using the site**: who we showed it to, how many tried it, what they
said, what we changed after, and evidence of donations (bonus). Nothing in it may be invented, so every day
without users is a day of report lost. Getting real users (#9) is as important as building features.

## Open questions

- Charity fund for the donate button: Severyn chooses (#7 uses a placeholder until then).
- Reviewers sign out and in again to see the «Рев’ю» link (the role is in the sign-in token).
