"""Усі тексти бота в одному місці. Формат: Telegram HTML.

Словник проєкту: «тестове завдання», «кейс», «рев'ю», «портфоліо».
Не вживаємо: «курс», «навчання», «уроки», «сертифікат».
"""
from html import escape as _escape


def escape(value: str) -> str:
    return _escape(value, quote=False)


BOT_DESCRIPTION = (
    "Тестові завдання для junior, як на відборі в компаніях: аналітика, бізнес-аналіз, QA. "
    "Розмитий бриф від менеджера, сирі дані, дедлайн і рев'ю від тімліда. Результат — робота для портфоліо."
)
BOT_SHORT_DESCRIPTION = "Тестові для junior: аналітика, BA, QA. З рев'ю як від тімліда"

WELCOME = (
    "<b>Привіт, {name}!</b>\n\n"
    "Тут ти розв'язуєш тестові завдання, як на відборі в компаніях:\n\n"
    "📩 розмитий бриф від менеджера, а не покрокова інструкція\n"
    "🗂 сирі дані, суперечливі вимоги чи специфікація з дірками\n"
    "⏰ дедлайн, як у справжньому тестовому\n"
    "🧑‍💻 рев'ю від тімліда: що добре, що виправити, що робити далі\n\n"
    "На виході — робота, яку не соромно покласти в портфоліо й показати на співбесіді."
)

HOW_IT_WORKS = (
    "<b>Як це працює</b>\n\n"
    "<b>1. Обираєш професію й кейс.</b> Бачиш, яка компанія, які навички й скільки часу піде.\n"
    "<b>2. Отримуєш лист від менеджера й матеріали.</b> Бриф навмисно розмитий: з'ясувати, що насправді питають, теж частина роботи.\n"
    "<b>3. Робиш завдання</b> в тих інструментах, які звичні для професії: Python, SQL, таблиці, Miro, Google Docs.\n"
    "<b>4. Здаєш сюди</b> посилання чи файл плюс коротке резюме для менеджера.\n"
    "<b>5. Отримуєш рев'ю</b> протягом {sla} днів і шаблон README, щоб оформити роботу в портфоліо.\n\n"
    "Єдиної правильної відповіді немає: оцінюється хід думки, якість висновків і рекомендація."
)

NO_CASES_YET = "Ти ще не брав кейсів. Обери перший 👇"

CASES_HEADER = "<b>Доступні кейси</b>\n\nОбери, щоб побачити деталі:"

PROFESSIONS_HEADER = (
    "<b>Обери професію</b>\n\n"
    "Для кожної є кейси у форматі справжніх тестових. Напрями з 🔜 ще готуємо: "
    "натисни, якщо хочеш, щоб вони з'явились раніше."
)


def profession_cases(prof: dict) -> str:
    about = f"\n{escape(prof['about'])}\n" if prof.get("about") else ""
    return f"<b>{prof['emoji']} {escape(prof['title'])}</b>\n{about}\nОбери кейс, щоб побачити деталі:"


def profession_soon(prof: dict) -> str:
    return (
        f"<b>{prof['emoji']} {escape(prof['title'])}</b>\n\n"
        "Кейси для цього напряму ще готуємо. Перші з'являться там, де більше людей натисне кнопку нижче."
    )


VOTE_THANKS = "Записав 🙌 Напишу, щойно з'являться кейси. Поки можеш спробувати суміжний напрям."


def case_card(case: dict) -> str:
    skills = " · ".join(case["skills"])
    return (
        f"<b>{escape(case['title'])}</b>\n"
        f"<i>{escape(case['track'])} · {escape(case['level'])}</i>\n\n"
        f"🏢 {escape(case['company'])}\n\n"
        f"{escape(case['teaser'])}\n\n"
        f"🔎 <b>Схожі тестові:</b> {escape(case['similar'])}\n"
        "<i>Текст і дані наші: справжні тестові компанії не публікують.</i>\n\n"
        f"🎯 <b>Навички:</b> {escape(skills)}\n"
        f"🛠 <b>Інструменти:</b> {escape(case['tools'])}\n"
        f"⏱ <b>Час:</b> {escape(case['time_estimate'])} роботи\n"
        f"📅 <b>Дедлайн:</b> {case['deadline_days']} дні з моменту, як візьмеш"
    )


def letter(markdown_text: str) -> str:
    """Лист PM із brief.md (до роздільника ---) у вигляді повідомлення."""
    body = markdown_text.split("\n---", 1)[0]
    out = []
    for line in body.splitlines():
        line = line.strip()
        if line.startswith("# "):
            continue
        line = escape(line)
        while "**" in line:
            line = line.replace("**", "<b>", 1).replace("**", "</b>", 1)
        if line.startswith("- "):
            line = "• " + line[2:]
        out.append(line)
    text = "\n".join(out).strip()
    return f"📩 <b>Новий лист</b>\n\n{text}"


def case_taken(deadline: str) -> str:
    return (
        f"⏰ <b>Дедлайн: {deadline}</b>\n\n"
        "Коли буде готово, надішли сюди <b>одним повідомленням</b>:\n"
        "• посилання (GitHub, Colab, Google Docs чи Sheets, Miro) або файл\n"
        "• короткий висновок текстом, як просить лист\n\n"
        "Питання по кейсу пиши сюди звичайним повідомленням. Удачі!"
    )


PLAN_QUESTION = (
    "🗓 <b>Коли сядеш за кейс?</b>\n\n"
    "Обери час, і я нагадаю. Люди, які одразу планують конкретний час, доводять справу до кінця значно частіше."
)
def plan_now(first_step: str) -> str:
    return f"🚀 Тоді почни з малого. {escape(first_step)} Це 20 хвилин, і далі піде легше."


def plan_saved(when: str) -> str:
    return f"👌 Нагадаю {when} і підкажу перший крок на 20 хвилин."


def plan_reminder(title: str, first_step: str) -> str:
    return (
        f"⏱ Ти планував зараз сісти за кейс «{escape(title)}».\n\n"
        f"<b>Перший крок на 20 хвилин:</b> {escape(first_step)} Більше на сьогодні можна й не робити."
    )


def pm_checkin(sender: str, deadline: str) -> str:
    return (
        f"📩 <b>{escape(sender)}</b>\n\n"
        "Привіт! Як просувається? Напиши 2–3 речення, що вже бачиш. "
        f"Навіть «поки розбираюсь» — нормальна відповідь. Нагадаю, фінальний результат чекаю до {deadline}."
    )


def pm_checkin_thanks(sender: str) -> str:
    return f"📩 <b>{escape(sender.split(',')[0])}:</b> Дякую, прийнято! Чекаю на результат."

ALREADY_TAKEN = "Цей кейс уже в тебе, лист і дані вище в чаті."

CONFIRM_SUBMISSION = "Це твоя здача по кейсу «{title}»? Після підтвердження змінити її вже не вийде."

SUBMITTED = (
    "✅ <b>Здачу прийнято!</b>\n\n"
    "Рев'ю прийде сюди протягом {sla} днів. Поки чекаєш, запиши, що б ти зробив інакше, "
    "якби мав ще день: це знадобиться на співбесіді."
)

SUBMISSION_CANCELLED = "Добре, не зараховую. Надішли роботу, коли будеш готовий."

QUESTION_FORWARDED = (
    "Передав твоє питання команді, відповідь прийде сюди.\n\n"
    "Якщо це була здача, додай посилання на GitHub чи Colab або прикріпи файл."
)

NEED_CASE_FIRST = "Спершу обери кейс 👇"


def review(text: str) -> str:
    return f"🧑‍💻 <b>Рев'ю від тімліда</b>\n\n{escape(text)}"


PORTFOLIO_CAPTION = (
    "📁 Шаблон README для GitHub. Врахуй рев'ю, онови роботу й оформи її за шаблоном: "
    "так її можна показувати рекрутеру."
)

RATE_QUESTION = "Наскільки цей кейс схожий на справжнє тестове завдання?\n1 — зовсім ні, 5 — дуже схоже."

THANKS_FOR_RATING = "Дякую, твоя оцінка: {score}/5. Якщо хочеш щось додати, просто напиши сюди."


def reminder(title: str, deadline: str) -> str:
    return (
        f"⏰ До дедлайну по кейсу «{escape(title)}» менше доби ({deadline}).\n\n"
        "Навіть неідеальна здача з чесним описом обмежень краща за жодну: рев'ю покаже, що доробити."
    )


def my_cases(rows, cases: dict) -> str:
    lines = ["<b>Мої кейси</b>\n"]
    for r in rows:
        title = escape(cases.get(r["case_id"], {}).get("title", r["case_id"]))
        if r["reviewed_at"]:
            status = "🟢 рев'ю отримано"
        elif r["submission_id"]:
            status = "🟡 здано, чекає на рев'ю"
        else:
            status = f"🔵 у роботі, дедлайн {short_dt(r['deadline'])}"
        lines.append(f"• {title}: {status}")
    return "\n".join(lines)


def short_dt(value: str) -> str:
    """'2026-10-17 17:17:00' → '17.10 о 17:17'"""
    date, time = value.split(" ")
    _, m, d = date.split("-")
    return f"{d}.{m} о {time[:5]}"


# --- для автора ---
def admin_new_submission(sub_id: int, who: str, title: str) -> str:
    return f"📥 <b>Здача #{sub_id}</b> від {escape(who)}\nКейс: {escape(title)}"


def admin_case_taken(who: str, title: str) -> str:
    return f"▶️ {escape(who)} взяв кейс «{escape(title)}»"


def admin_question(who: str, user_id: int) -> str:
    return f"💬 Питання від {escape(who)}. Відповісти: <code>/reply {user_id} текст</code>"


ADMIN_REVIEW_PROMPT = "Напиши рев'ю на здачу #{sub_id} наступним повідомленням. /cancel, щоб скасувати."
ADMIN_REVIEW_SENT = "✅ Рев'ю на здачу #{sub_id} надіслано."
ADMIN_NOTHING_PENDING = "Усі здачі переглянуті 🎉"
