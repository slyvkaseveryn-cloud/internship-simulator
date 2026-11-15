"""Telegram-бот «Симулятор стажувань».

Користувач: обирає професію → кейс → отримує лист PM і дані → здає посилання чи файл → отримує рев'ю,
шаблон README для портфоліо й оцінює кейс.
Автор (ADMIN_ID): отримує здачі й питання, пише рев'ю кнопкою «Написати рев'ю», бачить воронку в /stats
і повний дашборд у /report.
"""
import asyncio
import logging
import re
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import (
    BotCommand,
    BufferedInputFile,
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

from . import texts
from .config import ADMIN_ID, BOT_DIR, BOT_TOKEN, CASES, DATA_DIR, DB_PATH, PROFESSIONS, REVIEW_SLA_DAYS
from .storage import Storage

log = logging.getLogger(__name__)
URL_RE = re.compile(r"https?://\S+")

BTN_CASES = "📂 Кейси"
BTN_MINE = "📊 Мої кейси"
BTN_HELP = "❓ Як це працює"

MAIN_MENU = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text=BTN_CASES), KeyboardButton(text=BTN_MINE)], [KeyboardButton(text=BTN_HELP)]],
    resize_keyboard=True,
)

dp = Dispatcher()
db: Storage | None = None

# Стан у пам'яті: здачі, що чекають підтвердження, і рев'ю, яке автор зараз пише
pending_confirm: dict[int, dict] = {}
admin_writing_review: dict[int, int] = {}


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# Кольори кнопок (Bot API style): заливка з білим текстом добре читається на будь-якому фоні чату.
# Старі клієнти Telegram просто ігнорують style і показують звичайну кнопку.
PRIMARY, SUCCESS = "primary", "success"


def kb(*rows: list[tuple]) -> InlineKeyboardMarkup:
    """Рядки з кнопок (текст, callback_data) або (текст, callback_data, style)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=b[0], callback_data=b[1], style=b[2] if len(b) > 2 else None) for b in row]
            for row in rows
        ]
    )


def cases_keyboard(profession: str | None = None) -> InlineKeyboardMarkup:
    cases = [c for c in CASES.values() if profession in (None, c["profession"])]
    rows = [[(f"📁 {c['title']}", f"view:{c['id']}", PRIMARY)] for c in cases]
    return kb(*rows, [("🔄 Інша професія", "profs")])


def professions_keyboard() -> InlineKeyboardMarkup:
    live = [p for p in PROFESSIONS.values() if p["status"] == "live"]
    soon = [p for p in PROFESSIONS.values() if p["status"] != "live"]
    rows = [[(f"{p['emoji']} {p['title']}", f"prof:{p['id']}", PRIMARY)] for p in live]
    rows += [[(f"🔜 {p['title']}", f"prof:{p['id']}") for p in soon[i:i + 2]] for i in range(0, len(soon), 2)]
    return kb(*rows)


async def show_cases(message: Message, user_id: int):
    """Кейси обраної професії, або вибір професії, якщо її ще нема."""
    prof = PROFESSIONS.get(db.profession(user_id) or "")
    if not prof:
        await message.answer(texts.PROFESSIONS_HEADER, reply_markup=professions_keyboard())
        return
    await message.answer(texts.profession_cases(prof), reply_markup=cases_keyboard(prof["id"]))


# ---------- користувач ----------

@dp.message(CommandStart())
async def on_start(message: Message):
    db.touch_user(message.from_user)
    db.log(message.from_user.id, "start", value=message.text.removeprefix("/start").strip() or None)
    name = message.from_user.first_name or "колего"
    await message.answer(texts.WELCOME.format(name=texts.escape(name)), reply_markup=MAIN_MENU)
    await message.answer(texts.PROFESSIONS_HEADER, reply_markup=professions_keyboard())


@dp.message(Command("cases"))
@dp.message(F.text == BTN_CASES)
async def on_cases(message: Message):
    db.touch_user(message.from_user)
    await show_cases(message, message.from_user.id)


@dp.callback_query(F.data == "profs")
async def on_professions(call: CallbackQuery):
    await call.message.answer(texts.PROFESSIONS_HEADER, reply_markup=professions_keyboard())
    await call.answer()


@dp.callback_query(F.data.startswith("prof:"))
async def on_profession(call: CallbackQuery):
    prof = PROFESSIONS.get(call.data.split(":", 1)[1])
    if not prof:
        await call.answer()
        return
    db.touch_user(call.from_user)
    if prof["status"] != "live":
        db.log(call.from_user.id, "track_viewed", value=prof["id"])
        await call.message.answer(
            texts.profession_soon(prof),
            reply_markup=kb([("🔔 Хочу цей напрям", f"vote:{prof['id']}", SUCCESS)], [("← Інші професії", "profs")]),
        )
    else:
        db.set_profession(call.from_user.id, prof["id"])
        db.log(call.from_user.id, "profession_chosen", value=prof["id"])
        await call.message.answer(texts.profession_cases(prof), reply_markup=cases_keyboard(prof["id"]))
    await call.answer()


@dp.callback_query(F.data.startswith("vote:"))
async def on_vote(call: CallbackQuery):
    prof_id = call.data.split(":", 1)[1]
    if prof_id in PROFESSIONS and not db.has_event(call.from_user.id, "track_vote", value=prof_id):
        db.log(call.from_user.id, "track_vote", value=prof_id)
        if ADMIN_ID and not is_admin(call.from_user.id):
            await call.bot.send_message(
                ADMIN_ID, f"🔔 {texts.escape(db.username(call.from_user.id))} хоче напрям «{PROFESSIONS[prof_id]['title']}»"
            )
    await call.message.edit_reply_markup(reply_markup=kb([("← Інші професії", "profs")]))
    await call.message.answer(texts.VOTE_THANKS)
    await call.answer()


@dp.message(Command("help"))
@dp.message(F.text == BTN_HELP)
async def on_help(message: Message):
    await message.answer(texts.HOW_IT_WORKS.format(sla=REVIEW_SLA_DAYS), reply_markup=MAIN_MENU)


@dp.message(Command("my"))
@dp.message(F.text == BTN_MINE)
async def on_my(message: Message):
    rows = db.user_attempts(message.from_user.id)
    if not rows:
        await message.answer(texts.NO_CASES_YET)
        await show_cases(message, message.from_user.id)
        return
    await message.answer(texts.my_cases(rows, CASES))


@dp.callback_query(F.data.startswith("view:"))
async def on_view_case(call: CallbackQuery):
    case = CASES.get(call.data.split(":", 1)[1])
    if not case:
        await call.answer("Кейс не знайдено")
        return
    db.touch_user(call.from_user)
    db.log(call.from_user.id, "case_viewed", case["id"])
    await call.message.answer(
        texts.case_card(case),
        reply_markup=kb([("✅ Беру кейс", f"take:{case['id']}", SUCCESS)], [("← Усі кейси", "list")]),
    )
    await call.answer()


@dp.callback_query(F.data == "list")
async def on_list(call: CallbackQuery):
    await show_cases(call.message, call.from_user.id)
    await call.answer()


@dp.callback_query(F.data.startswith("take:"))
async def on_take_case(call: CallbackQuery):
    case = CASES.get(call.data.split(":", 1)[1])
    if not case:
        await call.answer("Кейс не знайдено")
        return
    user = call.from_user
    db.touch_user(user)
    last = db.last_attempt(user.id, case["id"])
    active = db.active_attempt(user.id)
    if last and active and active["id"] == last["id"]:
        await call.answer(texts.ALREADY_TAKEN, show_alert=True)
        return

    attempt = db.start_attempt(user.id, case["id"], case["deadline_days"])
    db.log(user.id, "case_taken", case["id"])
    await call.answer()
    await call.message.edit_reply_markup(reply_markup=None)

    folder = case["path"]
    await call.message.answer(texts.letter((folder / case["brief"]).read_text(encoding="utf-8")))
    await call.message.answer_document(
        FSInputFile(folder / case["brief"]), caption="📄 Повний бриф з описом даних"
    )
    for f in case["files"]:
        await call.message.answer_document(FSInputFile(folder / f["name"]), caption=f"🗂 {f['caption']}")
    await call.message.answer(texts.case_taken(texts.short_dt(attempt["deadline"])), reply_markup=MAIN_MENU)
    await call.message.answer(texts.PLAN_QUESTION, reply_markup=plan_keyboard(attempt))
    if ADMIN_ID and not is_admin(user.id):
        await call.bot.send_message(ADMIN_ID, texts.admin_case_taken(db.username(user.id), case["title"]))


def plan_options(attempt, now: datetime | None = None) -> list[tuple[str, datetime | None]]:
    """Варіанти «коли сядеш»: лише ті, що раніше за дедлайн."""
    now = now or datetime.now()
    deadline = datetime.strptime(attempt["deadline"], "%Y-%m-%d %H:%M:%S")
    tomorrow = (now + timedelta(days=1)).replace(hour=19, minute=0, second=0, microsecond=0)
    days_to_sat = (5 - now.weekday()) % 7 or 7
    saturday = (now + timedelta(days=days_to_sat)).replace(hour=11, minute=0, second=0, microsecond=0)
    options = [("🚀 Вже сідаю", None), ("Через 2 години", now + timedelta(hours=2)), ("Завтра о 19:00", tomorrow)]
    if saturday < deadline - timedelta(hours=6):
        options.append(("У суботу об 11:00", saturday))
    return [(label, when) for label, when in options if when is None or when < deadline]


def plan_keyboard(attempt) -> InlineKeyboardMarkup:
    rows = [[(label, f"plan:{attempt['id']}:{i}", PRIMARY)] for i, (label, _) in enumerate(plan_options(attempt))]
    return kb(*rows)


@dp.callback_query(F.data.startswith("plan:"))
async def on_plan(call: CallbackQuery):
    _, attempt_id, idx = call.data.split(":")
    attempt = db.attempt(int(attempt_id))
    if not attempt or attempt["user_id"] != call.from_user.id:
        await call.answer()
        return
    options = plan_options(attempt)
    label, when = options[min(int(idx), len(options) - 1)]
    db.log(call.from_user.id, "plan_set", attempt["case_id"], label)
    first_step = CASES.get(attempt["case_id"], {}).get("first_step", "")
    if when is None:
        await call.message.edit_text(texts.plan_now(first_step))
    else:
        db.set_plan(attempt["id"], when)
        await call.message.edit_text(texts.plan_saved(label.lower()))
    await call.answer()


@dp.callback_query(F.data.startswith("submit:"))
async def on_confirm_submission(call: CallbackQuery):
    user = call.from_user
    draft = pending_confirm.pop(user.id, None)
    attempt = db.active_attempt(user.id)
    if call.data == "submit:no" or not draft or not attempt:
        await call.message.edit_text(texts.SUBMISSION_CANCELLED)
        await call.answer()
        return
    sub_id = db.add_submission(attempt, draft["content"], draft["file_id"], draft["file_name"])
    db.log(user.id, "submission", attempt["case_id"], str(sub_id))
    await call.message.edit_text(texts.SUBMITTED.format(sla=REVIEW_SLA_DAYS))
    await call.answer()
    if ADMIN_ID:
        title = CASES.get(attempt["case_id"], {}).get("title", attempt["case_id"])
        await call.bot.send_message(ADMIN_ID, texts.admin_new_submission(sub_id, db.username(user.id), title))
        await call.bot.forward_message(ADMIN_ID, draft["chat_id"], draft["message_id"])
        await call.bot.send_message(
            ADMIN_ID, "👆 Робота вище", reply_markup=kb([("✍️ Написати рев'ю", f"review:{sub_id}")])
        )


@dp.callback_query(F.data.startswith("rate:"))
async def on_rate(call: CallbackQuery):
    _, sub_id, score = call.data.split(":")
    db.save_rating(int(sub_id), int(score))
    db.log(call.from_user.id, "rating", value=f"{sub_id}:{score}")
    await call.message.edit_text(texts.THANKS_FOR_RATING.format(score=score))
    await call.answer()
    if ADMIN_ID:
        await call.bot.send_message(ADMIN_ID, f"⭐ {db.username(call.from_user.id)} оцінив кейс (здача #{sub_id}): {score}/5")


# ---------- автор ----------

@dp.callback_query(F.data.startswith("review:"))
async def on_review_button(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer()
        return
    sub_id = int(call.data.split(":")[1])
    admin_writing_review[call.from_user.id] = sub_id
    await call.message.answer(texts.ADMIN_REVIEW_PROMPT.format(sub_id=sub_id))
    await call.answer()


@dp.message(Command("cancel"))
async def on_cancel(message: Message):
    admin_writing_review.pop(message.from_user.id, None)
    pending_confirm.pop(message.from_user.id, None)
    await message.answer("Скасовано.", reply_markup=MAIN_MENU)


@dp.message(Command("review"))
async def on_review_command(message: Message, command: CommandObject):
    """Запасний шлях: /review <id> <текст>"""
    if not is_admin(message.from_user.id):
        return
    if not command.args or " " not in command.args.strip():
        await message.answer("Формат: /review <id> <текст рев'ю>")
        return
    sub_id, text = command.args.strip().split(maxsplit=1)
    await send_review(message.bot, message, int(sub_id), text)


async def send_review(bot: Bot, admin_msg: Message, sub_id: int, text: str):
    sub = db.submission(sub_id)
    if not sub:
        await admin_msg.answer(f"Здачі #{sub_id} немає.")
        return
    db.save_review(sub_id, text)
    db.log(sub["user_id"], "review_sent", sub["case_id"], str(sub_id))
    await bot.send_message(sub["user_id"], texts.review(text))
    await bot.send_document(
        sub["user_id"], FSInputFile(BOT_DIR / "portfolio_template.md"), caption=texts.PORTFOLIO_CAPTION
    )
    await bot.send_message(
        sub["user_id"],
        texts.RATE_QUESTION,
        reply_markup=kb([(str(i), f"rate:{sub_id}:{i}", PRIMARY) for i in range(1, 6)]),
    )
    await admin_msg.answer(texts.ADMIN_REVIEW_SENT.format(sub_id=sub_id))


@dp.message(Command("reply"))
async def on_reply(message: Message, command: CommandObject):
    """Відповідь на питання: /reply <user_id> <текст>"""
    if not is_admin(message.from_user.id):
        return
    if not command.args or " " not in command.args.strip():
        await message.answer("Формат: /reply <user_id> <текст>")
        return
    user_id, text = command.args.strip().split(maxsplit=1)
    await message.bot.send_message(int(user_id), f"💬 <b>Відповідь від команди</b>\n\n{texts.escape(text)}")
    db.log(int(user_id), "answer_sent")
    await message.answer("✅ Надіслано.")


@dp.message(Command("pending"))
async def on_pending(message: Message):
    if not is_admin(message.from_user.id):
        return
    rows = db.pending()
    if not rows:
        await message.answer(texts.ADMIN_NOTHING_PENDING)
        return
    for r in rows:
        title = CASES.get(r["case_id"], {}).get("title", r["case_id"])
        await message.answer(
            f"#{r['id']} · {texts.escape(db.username(r['user_id']))} · {texts.escape(title)} · {texts.short_dt(r['submitted_at'])}",
            reply_markup=kb([("✍️ Написати рев'ю", f"review:{r['id']}")]),
        )


@dp.message(Command("stats"))
async def on_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    funnel = db.funnel()
    top = funnel[0][1] or 1
    lines = [f"{label}: <b>{n}</b> ({n * 100 // top}%)" for label, n in funnel]
    await message.answer("📈 <b>Воронка, унікальні люди</b>\n\n" + "\n".join(lines) + "\n\nПовний дашборд: /report")


@dp.message(Command("report"))
async def on_report(message: Message):
    if not is_admin(message.from_user.id):
        return
    from .report import build_report

    html = build_report(db, CASES, PROFESSIONS)
    await message.answer_document(BufferedInputFile(html.encode("utf-8"), "dashboard.html"), caption="📊 Дашборд продукту")


# ---------- усе інше: здачі, питання, текст рев'ю від автора ----------

@dp.message(F.text | F.document)
async def on_any_message(message: Message):
    user = message.from_user
    db.touch_user(user)

    if is_admin(user.id) and user.id in admin_writing_review and message.text:
        sub_id = admin_writing_review.pop(user.id)
        await send_review(message.bot, message, sub_id, message.text)
        return

    attempt = db.active_attempt(user.id)
    text = message.text or message.caption or ""
    if not attempt:
        await message.answer(texts.NEED_CASE_FIRST)
        await show_cases(message, user.id)
        return

    if message.document or URL_RE.search(text):
        pending_confirm[user.id] = {
            "content": text,
            "file_id": message.document.file_id if message.document else None,
            "file_name": message.document.file_name if message.document else None,
            "chat_id": message.chat.id,
            "message_id": message.message_id,
        }
        title = CASES.get(attempt["case_id"], {}).get("title", attempt["case_id"])
        await message.reply(
            texts.CONFIRM_SUBMISSION.format(title=texts.escape(title)),
            reply_markup=kb([("✅ Так, здаю", "submit:yes", SUCCESS), ("Ні", "submit:no")]),
        )
        return

    if attempt["checkin_sent_at"] and not db.has_event(user.id, "checkin_reply", attempt["case_id"]):
        db.log(user.id, "checkin_reply", attempt["case_id"])
        sender = CASES.get(attempt["case_id"], {}).get("sender", "Менеджер")
        await message.answer(texts.pm_checkin_thanks(sender))
        if ADMIN_ID and not is_admin(user.id):
            await message.bot.send_message(ADMIN_ID, f"📩 {texts.escape(db.username(user.id))} відповів на чек-ін PM:")
            await message.forward(ADMIN_ID)
        return

    db.log(user.id, "question", attempt["case_id"])
    await message.answer(texts.QUESTION_FORWARDED)
    if ADMIN_ID and not is_admin(user.id):
        await message.bot.send_message(ADMIN_ID, texts.admin_question(db.username(user.id), user.id))
        await message.forward(ADMIN_ID)


# ---------- фонові задачі й запуск ----------

async def reminders_loop(bot: Bot, every: int = 300):
    """Раз на 5 хв: нагадування у запланований час, чек-ін від PM через добу, нагадування за добу до дедлайну."""
    while True:
        try:
            for a in db.due_plan_reminders():
                case = CASES.get(a["case_id"], {})
                await bot.send_message(a["user_id"], texts.plan_reminder(case.get("title", a["case_id"]), case.get("first_step", "")))
                db.mark_plan_reminded(a["id"])
                db.log(a["user_id"], "plan_reminder", a["case_id"])
            for a in db.due_checkins(timedelta(hours=24)):
                sender = CASES.get(a["case_id"], {}).get("sender", "Менеджер")
                await bot.send_message(a["user_id"], texts.pm_checkin(sender, texts.short_dt(a["deadline"])))
                db.mark_checkin(a["id"])
                db.log(a["user_id"], "checkin_sent", a["case_id"])
            for a in db.due_reminders(timedelta(hours=24)):
                title = CASES.get(a["case_id"], {}).get("title", a["case_id"])
                await bot.send_message(a["user_id"], texts.reminder(title, texts.short_dt(a["deadline"])))
                db.mark_reminded(a["id"])
                db.log(a["user_id"], "reminder", a["case_id"])
        except Exception:
            log.exception("reminders failed")
        await asyncio.sleep(every)


async def setup_bot_profile(bot: Bot):
    """Меню команд і опис, який людина бачить до першого /start."""
    await bot.set_my_commands([
        BotCommand(command="start", description="Почати"),
        BotCommand(command="cases", description="Кейси"),
        BotCommand(command="my", description="Мої кейси"),
        BotCommand(command="help", description="Як це працює"),
    ])
    try:
        await bot.set_my_description(texts.BOT_DESCRIPTION)
        await bot.set_my_short_description(texts.BOT_SHORT_DESCRIPTION)
    except Exception:
        log.warning("could not set bot description", exc_info=True)


def init_storage() -> Storage:
    global db
    db = Storage(DB_PATH)
    migrated = db.import_legacy_csv(DATA_DIR)
    if migrated:
        log.info("imported %s attempts from legacy CSV", migrated)
    return db


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if not BOT_TOKEN or not ADMIN_ID:
        raise SystemExit("Заповни BOT_TOKEN і ADMIN_ID у bot/.env (див. bot/.env.example)")
    init_storage()
    bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await setup_bot_profile(bot)
    asyncio.create_task(reminders_loop(bot))
    await dp.start_polling(bot)
