"""SQLite-сховище. Одна база data/sim.db: люди, спроби кейсів, здачі, події воронки."""
import csv
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id     INTEGER PRIMARY KEY,
    username    TEXT,
    first_name  TEXT,
    first_seen  TEXT NOT NULL,
    profession  TEXT
);
CREATE TABLE IF NOT EXISTS attempts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    case_id     TEXT NOT NULL,
    started_at  TEXT NOT NULL,
    deadline    TEXT NOT NULL,
    reminded_at TEXT,
    planned_at  TEXT,
    plan_reminded_at TEXT,
    checkin_sent_at TEXT
);
CREATE TABLE IF NOT EXISTS submissions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    attempt_id   INTEGER NOT NULL,
    user_id      INTEGER NOT NULL,
    case_id      TEXT NOT NULL,
    submitted_at TEXT NOT NULL,
    content      TEXT,
    file_id      TEXT,
    file_name    TEXT,
    review_text  TEXT,
    reviewed_at  TEXT,
    rating       INTEGER
);
CREATE TABLE IF NOT EXISTS events (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    ts       TEXT NOT NULL,
    user_id  INTEGER NOT NULL,
    event    TEXT NOT NULL,
    case_id  TEXT,
    value    TEXT
);
"""

FMT = "%Y-%m-%d %H:%M:%S"


def now() -> str:
    return datetime.now().strftime(FMT)


class Storage:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self._migrate()

    def _migrate(self) -> None:
        """Додає нові колонки в базу, створену старішою версією бота."""
        have = {r["name"] for r in self.db.execute("PRAGMA table_info(attempts)")}
        for col in ("planned_at", "plan_reminded_at", "checkin_sent_at"):
            if col not in have:
                self.db.execute(f"ALTER TABLE attempts ADD COLUMN {col} TEXT")
        if "profession" not in {r["name"] for r in self.db.execute("PRAGMA table_info(users)")}:
            self.db.execute("ALTER TABLE users ADD COLUMN profession TEXT")
        self.db.commit()

    # --- люди й події ---
    def touch_user(self, user) -> None:
        self.db.execute(
            "INSERT INTO users(user_id, username, first_name, first_seen) VALUES (?,?,?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name",
            (user.id, user.username, user.first_name, now()),
        )
        self.db.commit()

    def log(self, user_id: int, event: str, case_id: str | None = None, value: str | None = None) -> None:
        self.db.execute(
            "INSERT INTO events(ts, user_id, event, case_id, value) VALUES (?,?,?,?,?)",
            (now(), user_id, event, case_id, value),
        )
        self.db.commit()

    def set_profession(self, user_id: int, profession: str) -> None:
        self.db.execute("UPDATE users SET profession=? WHERE user_id=?", (profession, user_id))
        self.db.commit()

    def profession(self, user_id: int) -> str | None:
        row = self.db.execute("SELECT profession FROM users WHERE user_id=?", (user_id,)).fetchone()
        return row["profession"] if row else None

    def track_votes(self) -> list[tuple[str, int]]:
        """Скільки людей хочуть кожен напрям «незабаром»."""
        return [(r[0], r[1]) for r in self.db.execute(
            "SELECT value, COUNT(DISTINCT user_id) FROM events WHERE event='track_vote' GROUP BY value ORDER BY 2 DESC"
        )]

    def username(self, user_id: int) -> str:
        row = self.db.execute("SELECT username, first_name FROM users WHERE user_id=?", (user_id,)).fetchone()
        if not row:
            return str(user_id)
        return f"@{row['username']}" if row["username"] else (row["first_name"] or str(user_id))

    # --- спроби ---
    def start_attempt(self, user_id: int, case_id: str, deadline_days: int) -> sqlite3.Row:
        started = datetime.now()
        cur = self.db.execute(
            "INSERT INTO attempts(user_id, case_id, started_at, deadline) VALUES (?,?,?,?)",
            (user_id, case_id, started.strftime(FMT), (started + timedelta(days=deadline_days)).strftime(FMT)),
        )
        self.db.commit()
        return self.attempt(cur.lastrowid)

    def attempt(self, attempt_id: int) -> sqlite3.Row:
        return self.db.execute("SELECT * FROM attempts WHERE id=?", (attempt_id,)).fetchone()

    def active_attempt(self, user_id: int) -> sqlite3.Row | None:
        """Остання спроба людини, по якій ще немає здачі."""
        return self.db.execute(
            "SELECT a.* FROM attempts a LEFT JOIN submissions s ON s.attempt_id = a.id "
            "WHERE a.user_id=? AND s.id IS NULL ORDER BY a.id DESC LIMIT 1",
            (user_id,),
        ).fetchone()

    def last_attempt(self, user_id: int, case_id: str) -> sqlite3.Row | None:
        return self.db.execute(
            "SELECT * FROM attempts WHERE user_id=? AND case_id=? ORDER BY id DESC LIMIT 1", (user_id, case_id)
        ).fetchone()

    def user_attempts(self, user_id: int) -> list[sqlite3.Row]:
        return self.db.execute(
            "SELECT a.*, s.id AS submission_id, s.reviewed_at, s.rating FROM attempts a "
            "LEFT JOIN submissions s ON s.attempt_id = a.id WHERE a.user_id=? ORDER BY a.id",
            (user_id,),
        ).fetchall()

    def due_reminders(self, within: timedelta) -> list[sqlite3.Row]:
        limit = (datetime.now() + within).strftime(FMT)
        return self.db.execute(
            "SELECT a.* FROM attempts a LEFT JOIN submissions s ON s.attempt_id = a.id "
            "WHERE s.id IS NULL AND a.reminded_at IS NULL AND a.deadline > ? AND a.deadline <= ?",
            (now(), limit),
        ).fetchall()

    def set_plan(self, attempt_id: int, when: datetime) -> None:
        self.db.execute("UPDATE attempts SET planned_at=?, plan_reminded_at=NULL WHERE id=?", (when.strftime(FMT), attempt_id))
        self.db.commit()

    def due_plan_reminders(self) -> list[sqlite3.Row]:
        return self.db.execute(
            "SELECT a.* FROM attempts a LEFT JOIN submissions s ON s.attempt_id = a.id "
            "WHERE s.id IS NULL AND a.planned_at IS NOT NULL AND a.plan_reminded_at IS NULL "
            "AND a.planned_at <= ? AND a.deadline > ?",
            (now(), now()),
        ).fetchall()

    def mark_plan_reminded(self, attempt_id: int) -> None:
        self.db.execute("UPDATE attempts SET plan_reminded_at=? WHERE id=?", (now(), attempt_id))
        self.db.commit()

    def due_checkins(self, after: timedelta) -> list[sqlite3.Row]:
        """Спроби, взяті більше ніж `after` тому, без здачі й без чек-іну від PM."""
        border = (datetime.now() - after).strftime(FMT)
        return self.db.execute(
            "SELECT a.* FROM attempts a LEFT JOIN submissions s ON s.attempt_id = a.id "
            "WHERE s.id IS NULL AND a.checkin_sent_at IS NULL AND a.started_at <= ? AND a.deadline > ?",
            (border, now()),
        ).fetchall()

    def mark_checkin(self, attempt_id: int) -> None:
        self.db.execute("UPDATE attempts SET checkin_sent_at=? WHERE id=?", (now(), attempt_id))
        self.db.commit()

    def has_event(self, user_id: int, event: str, case_id: str | None = None, value: str | None = None) -> bool:
        return self.db.execute(
            "SELECT 1 FROM events WHERE user_id=? AND event=? AND (? IS NULL OR case_id=?) AND (? IS NULL OR value=?) LIMIT 1",
            (user_id, event, case_id, case_id, value, value),
        ).fetchone() is not None

    def mark_reminded(self, attempt_id: int) -> None:
        self.db.execute("UPDATE attempts SET reminded_at=? WHERE id=?", (now(), attempt_id))
        self.db.commit()

    # --- здачі ---
    def add_submission(self, attempt: sqlite3.Row, content: str, file_id: str | None, file_name: str | None) -> int:
        cur = self.db.execute(
            "INSERT INTO submissions(attempt_id, user_id, case_id, submitted_at, content, file_id, file_name) "
            "VALUES (?,?,?,?,?,?,?)",
            (attempt["id"], attempt["user_id"], attempt["case_id"], now(), content, file_id, file_name),
        )
        self.db.commit()
        return cur.lastrowid

    def submission(self, sub_id: int) -> sqlite3.Row | None:
        return self.db.execute("SELECT * FROM submissions WHERE id=?", (sub_id,)).fetchone()

    def pending(self) -> list[sqlite3.Row]:
        return self.db.execute("SELECT * FROM submissions WHERE reviewed_at IS NULL ORDER BY id").fetchall()

    def save_review(self, sub_id: int, text: str) -> None:
        self.db.execute("UPDATE submissions SET review_text=?, reviewed_at=? WHERE id=?", (text, now(), sub_id))
        self.db.commit()

    def save_rating(self, sub_id: int, rating: int) -> None:
        self.db.execute("UPDATE submissions SET rating=? WHERE id=?", (rating, sub_id))
        self.db.commit()

    # --- аналітика ---
    FUNNEL = [
        ("start", "Відкрили бота"),
        ("profession_chosen", "Обрали професію"),
        ("case_viewed", "Подивились кейс"),
        ("case_taken", "Взяли кейс"),
        ("plan_set", "Запланували час"),
        ("checkin_reply", "Відповіли PM на чек-іні"),
        ("submission", "Здали роботу"),
        ("review_sent", "Отримали рев'ю"),
        ("rating", "Оцінили кейс"),
    ]

    def funnel(self) -> list[tuple[str, int]]:
        out = []
        for event, label in self.FUNNEL:
            n = self.db.execute("SELECT COUNT(DISTINCT user_id) FROM events WHERE event=?", (event,)).fetchone()[0]
            out.append((label, n))
        return out

    # --- міграція зі старої CSV-версії бота ---
    def import_legacy_csv(self, data_dir: Path) -> int:
        starts = data_dir / "starts.csv"
        if not starts.exists() or self.db.execute("SELECT COUNT(*) FROM attempts").fetchone()[0]:
            return 0
        n = 0
        with starts.open(encoding="utf-8") as f:
            for r in csv.DictReader(f):
                started = r["started_at"] + (":00" if len(r["started_at"]) == 16 else "")
                deadline = r["deadline"] + (":00" if len(r["deadline"]) == 16 else "")
                self.db.execute(
                    "INSERT OR IGNORE INTO users(user_id, username, first_name, first_seen) VALUES (?,?,?,?)",
                    (int(r["user_id"]), r["username"] or None, None, started),
                )
                self.db.execute(
                    "INSERT INTO attempts(user_id, case_id, started_at, deadline, reminded_at) VALUES (?,?,?,?,?)",
                    (int(r["user_id"]), r["case_id"], started, deadline, started),
                )
                self.db.execute(
                    "INSERT INTO events(ts, user_id, event, case_id) VALUES (?,?,?,?)",
                    (started, int(r["user_id"]), "case_taken", r["case_id"]),
                )
                n += 1
        self.db.commit()
        return n
