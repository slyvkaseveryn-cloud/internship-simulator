# Project status

_Updated: 2026-11-17 · updated after every merged task_

**Demo: Thursday 19.11.2026.** Each of us submits the repository link and the demo URL.

## Works now

| What | Where |
|---|---|
| Demo site over HTTPS | https://d174ecvpoyspb1.cloudfront.net |
| Sign-up with an email code, sign-in, password reset | `/signup`, `/signin`, `/reset` |
| Account page (shows your email and whether you are a reviewer) | `/account` |
| Case files for candidates (only `candidate/` folders) | `/cases/<id>/candidate/<file>` |
| Reviewer role: Cognito group `reviewers` (Severyn is in it) | see README → "Give someone the reviewer role" |
| CI on every pull request, deploy on merge to `main` | GitHub → Actions |
| Telegram bot (earlier prototype, separate data) | [@intern_sim_bot](https://t.me/intern_sim_bot) |

## Who does what (until Thursday)

| Issue | Task | Owner | State |
|---|---|---|---|
| [#1](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/1) | Roles, case list and case page | Severyn + Claude | next |
| [#2](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/2) | Take a case, submit a link + conclusion, statuses | Severyn + Claude | to do |
| [#3](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/3) | Reviewer page and review form | Severyn + Claude | to do |
| [#4](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/4) | Show the review, realism rating 1–5 with feedback | Severyn + Claude | to do |
| [#5](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/5) | Votes for «coming soon» roles | Severyn + Claude | to do |
| [#6](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/6) | Funnel events and metrics page | Severyn + Claude | to do |
| [#7](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/7) | «Support volunteers» button | Severyn + Claude | to do (fund not chosen yet) |
| [#8](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/8) | Report template and PDF build | Lev | to do (can start now) |
| [#9](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/9) | Invite the first users (cohort) | Danylo | to do (can start now) |
| [#10](https://github.com/slyvkaseveryn-cloud/internship-simulator/issues/10) | End-to-end check, copy review, demo script | Danylo | after #1–#4 are merged |

Dependencies: the report's numbers come from #6 (metrics), so Lev can write the template and the PDF build
first and fill numbers after people have used the site. Danylo's invitation text needs Severyn's OK before it
is sent anywhere.

## Why the report matters most

The course grades three things: the repository (3 points), a deployed prototype with sign-in (3 points) and
**the report (4 points)**. The first two are mostly done; the report is the largest part of the grade and it
can only be written from **real people using the site**: who we showed it to, how many tried it, what they
said, what we changed after, and evidence of donations (bonus). Nothing in it may be invented, so every day
without users is a day of report lost. Getting real users (#9) is as important as building features.

## Open questions

- Charity fund for the donate button: Severyn chooses (#7 uses a placeholder until then).
- Lev's and Danylo's emails for the `reviewers` group: after they sign up on the site.
