# Telegram bot (earlier prototype)

The first version of the product: an aiogram 3 bot with a SQLite database. It is kept here so all the code
lives in one repository. It does **not** share data with the website.

Run from the repository root:

```bash
cp backend/telegram_bot/.env.example backend/telegram_bot/.env   # BOT_TOKEN from @BotFather, ADMIN_ID = your Telegram ID
make bot
```

Cases come from `cases/cases.json` (shared with the website). Data is stored in `backend/telegram_bot/data/`
(gitignored). Admin commands: `/pending`, `/stats`, `/report`, `/reply <user_id> <text>`.

| File | Responsibility |
|---|---|
| `config.py` | paths, token, admin ID, loading cases and professions |
| `storage.py` | SQLite: users, attempts, submissions, funnel events |
| `texts.py` | all bot texts (Ukrainian) |
| `app.py` | handlers, reminders, start-up |
| `report.py` | HTML funnel dashboard |
