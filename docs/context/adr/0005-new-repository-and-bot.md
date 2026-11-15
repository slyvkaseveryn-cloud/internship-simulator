# ADR 0005: New repository; Telegram bot kept separately

- Status: accepted · Date: 2026-11-15

**Decision.** The course repository starts with a clean history. The Telegram bot's code moves to
`backend/telegram_bot/` and keeps its own SQLite database; the website does not share data with it.
Case metadata (`cases/cases.json`) is shared by both. Case answers live only in the private repository
`internship-simulator-author`; only `cases/*/candidate/` is public and uploaded to S3.

**Why.** The old history contains private material; one repository is simpler for the team; joining two
databases is not needed for the first version.
