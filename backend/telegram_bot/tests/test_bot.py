"""Наскрізний тест бота без мережі: підміняємо HTTP-сесію Telegram і дивимось, що бот надсилає."""
import asyncio
from datetime import datetime, timedelta

import pytest
from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.types import Chat, Message, Update, User
from telegram_bot import app
from telegram_bot.report import build_report
from telegram_bot.storage import FMT, Storage

STUDENT = User(id=5, is_bot=False, first_name="Оля", username="olya")
ADMIN = User(id=999, is_bot=False, first_name="Severyn", username="sev")


class FakeSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.sent = []

    async def make_request(self, bot, method, timeout=None):
        name = type(method).__name__
        self.sent.append((name, getattr(method, "chat_id", None), getattr(method, "text", None) or getattr(method, "caption", None) or ""))
        if name.startswith(("Answer", "Edit", "Set")):
            return True
        return Message(message_id=len(self.sent), date=datetime.now(), chat=Chat(id=1, type="private"), text="ok")

    async def close(self):
        pass

    async def stream_content(self, *a, **k):
        yield b""


@pytest.fixture
def env(tmp_path):
    app.db = Storage(tmp_path / "sim.db")
    app.pending_confirm.clear()
    app.admin_writing_review.clear()
    session = FakeSession()
    return Bot("1:test", session=session), session


counter = iter(range(1, 10_000))


def msg(user, text):
    n = next(counter)
    return Update(update_id=n, message={"message_id": n, "date": int(datetime.now().timestamp()),
                                        "chat": {"id": user.id, "type": "private"}, "from": user.model_dump(), "text": text})


def cb(user, data):
    n = next(counter)
    return Update(update_id=n, callback_query={"id": str(n), "from": user.model_dump(), "chat_instance": "x", "data": data,
                                               "message": {"message_id": 1, "date": int(datetime.now().timestamp()),
                                                           "chat": {"id": user.id, "type": "private"}, "text": "x"}})


def feed(bot, *updates):
    async def run():
        for u in updates:
            await app.dp.feed_update(bot, u)
    asyncio.run(run())


def texts_to(session, chat_id):
    return [t for _, c, t in session.sent if c == chat_id]


def test_full_happy_path(env):
    bot, s = env
    feed(bot, msg(STUDENT, "/start"), cb(STUDENT, "prof:analytics"), cb(STUDENT, "view:01-conversion-drop"),
         cb(STUDENT, "take:01-conversion-drop"))
    to_student = texts_to(s, STUDENT.id)
    assert any("Новий лист" in t for t in to_student)
    assert sum(1 for name, c, _ in s.sent if name == "SendDocument" and c == STUDENT.id) == 4  # бриф + 2 CSV + ноутбук
    assert any("Коли сядеш" in t for t in to_student)

    feed(bot, msg(STUDENT, "Готово: https://github.com/olya/case1 Резюме: баг оплати на Android 2.3.0"))
    assert any("Це твоя здача" in t for t in texts_to(s, STUDENT.id))
    feed(bot, cb(STUDENT, "submit:yes"))
    assert app.db.pending()[0]["content"].startswith("Готово")

    feed(bot, cb(ADMIN, "review:1"), msg(ADMIN, "Добре: знайдено баг.\nВиправити: незрілі когорти."))
    sub = app.db.submission(1)
    assert sub["review_text"].startswith("Добре") and sub["reviewed_at"]
    assert any("Рев'ю від тімліда" in t for t in texts_to(s, STUDENT.id))

    feed(bot, cb(STUDENT, "rate:1:4"))
    assert app.db.submission(1)["rating"] == 4
    assert [n for _, n in app.db.funnel()] == [1, 1, 1, 1, 0, 0, 1, 1, 1]


def test_question_is_not_a_submission(env):
    bot, s = env
    feed(bot, msg(STUDENT, "/start"), cb(STUDENT, "take:01-conversion-drop"), msg(STUDENT, "а дані за який період?"))
    assert app.db.pending() == []
    assert any("Передав твоє питання" in t for t in texts_to(s, STUDENT.id))
    assert any("Питання від" in t for t in texts_to(s, ADMIN.id))


def test_double_click_does_not_resend_files(env):
    bot, s = env
    feed(bot, cb(STUDENT, "take:01-conversion-drop"), cb(STUDENT, "take:01-conversion-drop"))
    assert sum(1 for name, c, _ in s.sent if name == "SendDocument") == 4


def test_cancelled_submission_is_not_saved(env):
    bot, _ = env
    feed(bot, cb(STUDENT, "take:01-conversion-drop"), msg(STUDENT, "https://colab.research.google.com/x"), cb(STUDENT, "submit:no"))
    assert app.db.pending() == []


def test_reminder_sent_once_before_deadline(env):
    bot, s = env
    a = app.db.start_attempt(STUDENT.id, "01-conversion-drop", 3)
    soon = (datetime.now() + timedelta(hours=10)).strftime(FMT)
    app.db.db.execute("UPDATE attempts SET deadline=? WHERE id=?", (soon, a["id"]))

    async def one_tick():
        task = asyncio.create_task(app.reminders_loop(bot, every=0.01))
        await asyncio.sleep(0.05)
        task.cancel()

    asyncio.run(one_tick())
    reminders = [t for t in texts_to(s, STUDENT.id) if "До дедлайну" in t]
    assert len(reminders) == 1


def test_report_renders(env):
    bot, _ = env
    feed(bot, msg(STUDENT, "/start"), cb(STUDENT, "take:01-conversion-drop"))
    html = build_report(app.db, app.CASES)
    assert "Воронка" in html and "Впала конверсія" in html


def test_legacy_csv_import(tmp_path):
    (tmp_path / "starts.csv").write_text(
        "user_id,username,case_id,started_at,deadline\n111,sev,01-conversion-drop,2026-10-11 08:31,2026-10-14 08:31\n",
        encoding="utf-8",
    )
    db = Storage(tmp_path / "sim.db")
    assert db.import_legacy_csv(tmp_path) == 1
    assert db.import_legacy_csv(tmp_path) == 0  # повторний запуск нічого не дублює


def test_plan_and_reminder_at_planned_time(env):
    bot, s = env
    feed(bot, cb(STUDENT, "take:01-conversion-drop"))
    attempt = app.db.active_attempt(STUDENT.id)
    feed(bot, cb(STUDENT, f"plan:{attempt['id']}:1"))  # «Через 2 години»
    assert app.db.attempt(attempt["id"])["planned_at"]
    past = (datetime.now() - timedelta(minutes=1)).strftime(FMT)
    app.db.db.execute("UPDATE attempts SET planned_at=? WHERE id=?", (past, attempt["id"]))

    async def one_tick():
        task = asyncio.create_task(app.reminders_loop(bot, every=0.01))
        await asyncio.sleep(0.05)
        task.cancel()

    asyncio.run(one_tick())
    assert sum(1 for t in texts_to(s, STUDENT.id) if "Ти планував" in t) == 1


def test_plan_options_never_after_deadline():
    start = datetime(2026, 10, 16, 22, 0)  # п'ятниця пізно ввечері, дедлайн за 3 дні
    attempt = {"deadline": (start + timedelta(days=3)).strftime(FMT)}
    for _, when in app.plan_options(attempt, now=start):
        assert when is None or when < start + timedelta(days=3)


def test_pm_checkin_after_a_day_and_reply(env):
    bot, s = env
    feed(bot, cb(STUDENT, "take:01-conversion-drop"))
    attempt = app.db.active_attempt(STUDENT.id)
    old = (datetime.now() - timedelta(hours=25)).strftime(FMT)
    app.db.db.execute("UPDATE attempts SET started_at=? WHERE id=?", (old, attempt["id"]))

    async def one_tick():
        task = asyncio.create_task(app.reminders_loop(bot, every=0.01))
        await asyncio.sleep(0.05)
        task.cancel()

    asyncio.run(one_tick())
    assert sum(1 for t in texts_to(s, STUDENT.id) if "Як просувається" in t) == 1
    feed(bot, msg(STUDENT, "Поки чищу дані, бачу дублікати"))
    assert app.db.has_event(STUDENT.id, "checkin_reply", "01-conversion-drop")
    assert any("Дякую, прийнято" in t for t in texts_to(s, STUDENT.id))
    feed(bot, msg(STUDENT, "А ще питання про період"))
    assert any("Передав твоє питання" in t for t in texts_to(s, STUDENT.id))


def test_old_database_gets_new_columns(tmp_path):
    import sqlite3
    path = tmp_path / "old.db"
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE attempts (id INTEGER PRIMARY KEY, user_id INTEGER, case_id TEXT, started_at TEXT, deadline TEXT, reminded_at TEXT)")
    con.commit()
    con.close()
    db = Storage(path)
    cols = {r["name"] for r in db.db.execute("PRAGMA table_info(attempts)")}
    assert {"planned_at", "plan_reminded_at", "checkin_sent_at"} <= cols


def test_start_offers_professions_and_filters_cases(env):
    bot, s = env
    feed(bot, msg(STUDENT, "/start"))
    assert any("Обери професію" in t for t in texts_to(s, STUDENT.id))
    feed(bot, cb(STUDENT, "prof:qa"))
    assert app.db.profession(STUDENT.id) == "qa"
    feed(bot, msg(STUDENT, "📂 Кейси"))
    assert any("QA-тестувальник" in t for t in texts_to(s, STUDENT.id)[-1:])
    ids = [b.callback_data for row in app.cases_keyboard("qa").inline_keyboard for b in row]
    assert ids[-1] == "profs"
    assert all(app.CASES[i.split(":")[1]]["profession"] == "qa" for i in ids[:-1])


def test_soon_profession_vote_counted_once(env):
    bot, s = env
    feed(bot, msg(STUDENT, "/start"), cb(STUDENT, "prof:marketing"))
    assert any("ще готуємо" in t for t in texts_to(s, STUDENT.id))
    assert app.db.profession(STUDENT.id) is None
    feed(bot, cb(STUDENT, "vote:marketing"), cb(STUDENT, "vote:marketing"))
    assert app.db.track_votes() == [("marketing", 1)]
    assert sum(1 for t in texts_to(s, ADMIN.id) if "хоче напрям" in t) == 1
    html = build_report(app.db, app.CASES, app.PROFESSIONS)
    assert "Маркетолог" in html


def test_case_card_shows_where_similar_tasks_are_given(env):
    bot, s = env
    feed(bot, msg(STUDENT, "/start"), cb(STUDENT, "view:02-ab-price"))
    assert any("Схожі тестові" in t for t in texts_to(s, STUDENT.id))


def test_every_case_is_complete():
    """Кожен кейс має професію, яка працює, і всі файли, які бот надсилає."""
    for case in app.CASES.values():
        assert app.PROFESSIONS[case["profession"]]["status"] == "live", case["id"]
        assert (case["path"] / case["brief"]).exists(), case["id"]
        for f in case["files"]:
            assert (case["path"] / f["name"]).exists(), (case["id"], f["name"])
        assert "author" not in str(case["path"]), case["id"]
        for key in ("similar", "sender", "first_step"):
            assert case.get(key), (case["id"], key)
    live = [p for p, v in app.PROFESSIONS.items() if v["status"] == "live"]
    for p in live:
        assert sum(c["profession"] == p for c in app.CASES.values()) >= 1, p


def test_old_users_table_gets_profession_column(tmp_path):
    import sqlite3
    path = tmp_path / "old.db"
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, first_seen TEXT NOT NULL)")
    con.execute("INSERT INTO users VALUES (5, 'olya', 'Оля', '2026-10-11 10:00:00')")
    con.commit()
    con.close()
    db = Storage(path)
    db.set_profession(5, "ba")
    assert db.profession(5) == "ba"
